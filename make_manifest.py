"""Freeze the v1 evidence: hashes, environment metadata and image digests.

Writes (does not modify anything else):
  * MANIFEST_v1.json  - machine readable
  * MANIFEST_v1.md    - human readable

What it records
  * per instance (the 37 in predictions_swebench.jsonl):
      sha256 of runs/<id>/patch.diff
      sha256 of runs/<id>/summary.md
      sha256 of runs/<id>/verify.py            (null when the file does not exist)
      sha256 of the patch string inside predictions.jsonl / predictions_swebench.jsonl
      sha256 of logs/run_evaluation/<run_id>/<model>/<id>/report.json and test_output.txt
  * environment: swebench version, docker client/server version, dataset name + split +
    parquet sha256, WSL distro, run_id, exact run command, timestamps
  * images: for each instance image, RepoTags / RepoDigests / local image Id

Run it from Windows (it shells out to WSL for docker/pip facts):
    python make_manifest.py
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time

BASE = r"<EXP_ROOT>"
RUNS = os.path.join(BASE, "runs")
RUN_ID = "tonight"
MODEL = "glm-5.3-zcode-campaign"
LOG_ROOT = os.path.join(BASE, "logs", "run_evaluation", RUN_ID, MODEL)
PREDS_RAW = os.path.join(BASE, "predictions.jsonl")
PREDS_HARNESS = os.path.join(BASE, "predictions_swebench.jsonl")
TOP_REPORT = os.path.join(BASE, "%s.%s.json" % (MODEL, RUN_ID))
PARQUET = os.path.join(BASE, "data", "swebench_lite_test.parquet")
DISTRO = "Ubuntu-22.04"
RUN_COMMAND = (
    "HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation "
    "-d SWE-bench/SWE-bench_Lite -s test -p predictions_swebench.jsonl "
    "-id %s --max_workers 4" % RUN_ID
)


def sha256_file(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean(text):
    """Drop NULs, control chars and the wsl.exe localhost-proxy warning.

    Without WSL_UTF8=1, wsl.exe can emit UTF-16 text; decoding that as UTF-8
    leaves NUL bytes inside strings, which turns the generated markdown into a
    binary file.  Belt and braces: set the env var AND sanitise here.
    """
    text = text.replace("\x00", "")
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("wsl:"):
            continue
        if "localhost" in line and ("WSL" in line or "NAT" in line):
            continue
        kept.append(line)
    text = "\n".join(kept)
    return "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32).strip()


def last_line(text):
    """Last non-empty line of a WSL command's stdout (version strings etc.)."""
    for line in reversed([l.strip() for l in (text or "").splitlines() if l.strip()]):
        return line
    return None


def wsl(args, timeout=90):
    """Run a command inside WSL; return (ok, cleaned stdout)."""
    env = dict(os.environ)
    env["WSL_UTF8"] = "1"  # keep wsl.exe from emitting UTF-16
    try:
        proc = subprocess.run(
            ["wsl.exe", "-d", DISTRO, "--"] + args,
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except Exception as exc:  # WSL missing / blocked
        return False, str(exc)
    out = clean((proc.stdout or b"").decode("utf-8", "replace"))
    return proc.returncode == 0, out


def image_facts(images):
    """Repo tags / digests / local image ids for the instance images.

    Note the format string deliberately contains no '|': wsl.exe hands the
    command line to bash, which would read a pipe as a shell operator, truncate
    the argument list and fail the whole call (observed on the first run).
    """
    facts = {}
    if not images:
        return facts

    tpl = "{{.Id}}@@{{json .RepoTags}}@@{{json .RepoDigests}}"

    def as_list(blob):
        """`{{json .X}}` prints a JSON array (or null) -- decode it properly,
        otherwise the quotes stay attached and the key never matches."""
        try:
            value = json.loads(blob)
        except ValueError:
            return []
        return value if isinstance(value, list) else []

    def parse(blob):
        for line in (blob or "").splitlines():
            line = line.strip()
            if "@@" not in line:
                continue
            parts = (line.split("@@") + ["", ""])[:3]
            image_id = parts[0].strip()
            tags = as_list(parts[1].strip())
            digests = as_list(parts[2].strip())
            tag = tags[0] if tags else image_id
            facts[tag] = {
                "repo_tags": ", ".join(tags),
                "repo_digests": ", ".join(digests),
                "image_id": image_id,
            }

    ok, out = wsl(["docker", "inspect", "--format", tpl] + list(images), timeout=300)
    if ok:
        parse(out)

    if len(facts) < len(images):  # batch call incomplete -> retry one by one
        for image in images:
            if any(image in key for key in facts):
                continue
            ok_one, out_one = wsl(["docker", "inspect", "--format", tpl, image], timeout=60)
            if ok_one:
                parse(out_one)

    if len(facts) < len(images):
        facts["error"] = "resolved %d/%d images; last output: %s" % (
            len([k for k in facts if k != "error"]), len(images), (out or "")[-300:]
        )
    return facts


def main():
    with open(PREDS_HARNESS, encoding="utf-8") as f:
        harness_preds = {json.loads(l)["instance_id"]: json.loads(l)
                         for l in f if l.strip()}
    with open(PREDS_RAW, encoding="utf-8") as f:
        raw_preds = {json.loads(l)["instance_id"]: json.loads(l)
                     for l in f if l.strip()}

    instances = sorted(harness_preds)
    entries = []
    images = []
    for inst in instances:
        runs_dir = os.path.join(RUNS, inst)
        patch_path = os.path.join(runs_dir, "patch.diff")
        summary_path = os.path.join(runs_dir, "summary.md")
        verify_path = os.path.join(runs_dir, "verify.py")
        report_path = os.path.join(LOG_ROOT, inst, "report.json")
        output_path = os.path.join(LOG_ROOT, inst, "test_output.txt")

        patch_text = harness_preds[inst]["model_patch"]
        raw_text = raw_preds.get(inst, {}).get("patch")

        repo = "sweb.eval.x86_64." + inst.replace("__", "_1776_")
        images.append("swebench/%s:latest" % repo)

        entries.append({
            "instance_id": inst,
            "patch_delta_vs_predictions": (
                None if raw_text is None
                else sha256_text(patch_text) == sha256_text(raw_text)
            ),
            "sha256": {
                "runs_patch.diff": sha256_file(patch_path),
                "runs_summary.md": sha256_file(summary_path),
                "runs_verify.py": sha256_file(verify_path),
                "predictions.patch": sha256_text(raw_text) if raw_text is not None else None,
                "predictions_swebench.model_patch": sha256_text(patch_text),
                "harness_report.json": sha256_file(report_path),
                "harness_test_output.txt": sha256_file(output_path),
            },
            "verify_py_present": os.path.isfile(verify_path),
            "image": "swebench/%s:latest" % repo,
        })

    ok_sw, sw_raw = wsl(
        ["python3", "-c", "import swebench,importlib.metadata as m;print(m.version('swebench'))"]
    )
    ok_dv, dv_raw = wsl(["docker", "version", "--format", "{{.Server.Version}}"])
    ok_di, di_raw = wsl(["python3", "-c", "import platform;print(platform.platform())"])

    swebench_version = last_line(sw_raw) if ok_sw else None
    docker_version = last_line(dv_raw) if ok_dv else None
    wsl_kernel = last_line(di_raw) if ok_di else None

    manifest = {
        "manifest_version": 1,
        "frozen_label": "v1-blind-write",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "run_id": RUN_ID,
        "model_name_or_path": MODEL,
        "run_command": RUN_COMMAND,
        "scope": {
            "declared_instances": len(instances),
            "excluded_out_of_scope": ["django__django-12747"],
        },
        "dataset": {
            "name": "SWE-bench/SWE-bench_Lite",
            "split": "test",
            "local_parquet": os.path.relpath(PARQUET, BASE),
            "sha256": sha256_file(PARQUET),
            "hf_endpoint": "https://hf-mirror.com",
        },
        "environment": {
            "host_os": platform.platform(),
            "wsl_distro": DISTRO,
            "wsl_kernel": wsl_kernel,
            "swebench_version": swebench_version,
            "docker_server_version": docker_version,
            "registry_mirrors": ["https://docker.m.daocloud.io", "https://docker.1ms.run"],
            "dockerd_proxy_note": (
                "registry-1.docker.io is unreachable from the WSL NAT network; dockerd runs "
                "with an HTTP(S) proxy pointing at the Windows-side forwarder "
                "tools/port_forward.py (0.0.0.0:7898 -> 127.0.0.1:7897) so the registry "
                "mirror fallback chain can reach Docker Hub."
            ),
        },
        "artifacts": {
            "predictions.jsonl": sha256_file(PREDS_RAW),
            "predictions_swebench.jsonl": sha256_file(PREDS_HARNESS),
            "harness_summary_report": sha256_file(TOP_REPORT),
        },
        "instances": entries,
        "images": image_facts(images) if instances else {},
        "inventory": {
            "patch.diff": sum(1 for e in entries if e["sha256"]["runs_patch.diff"]),
            "summary.md": sum(1 for e in entries if e["sha256"]["runs_summary.md"]),
            "verify.py": sum(1 for e in entries if e["verify_py_present"]),
            "harness report.json": sum(1 for e in entries if e["sha256"]["harness_report.json"]),
            "total": len(entries),
        },
    }

    json_path = os.path.join(BASE, "MANIFEST_v1.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    inv = manifest["inventory"]
    lines = []
    lines.append("# MANIFEST v1（盲写条件，已冻结）")
    lines.append("")
    lines.append("生成时间：`%s`" % manifest["generated_at"])
    lines.append("")
    lines.append("本清单把 v1 的分数与其证据文件绑定：`25/37 = 67.6%` 只有在下列文件"
                 "哈希不变时才成立。任何依据失败反馈修改补丁的工作都属于 v2"
                 "（见 `V2_PLAN.md`），不得覆盖本清单记录的文件。")
    lines.append("")
    lines.append("## 运行信息")
    lines.append("")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    lines.append("| run_id | `%s` |" % RUN_ID)
    lines.append("| model_name_or_path | `%s` |" % MODEL)
    lines.append("| 命令 | `%s` |" % RUN_COMMAND)
    lines.append("| swebench | %s |" % manifest["environment"]["swebench_version"])
    lines.append("| Docker server | %s |" % manifest["environment"]["docker_server_version"])
    lines.append("| WSL | %s (%s) |" % (DISTRO, manifest["environment"]["wsl_kernel"]))
    lines.append("| 数据集 | %s / %s，parquet sha256 `%s` |" % (
        manifest["dataset"]["name"], manifest["dataset"]["split"], manifest["dataset"]["sha256"]))
    lines.append("")
    lines.append("## 产物完整度")
    lines.append("")
    lines.append("| artifact | 覆盖 |")
    lines.append("|---|---|")
    for key in ("patch.diff", "summary.md", "verify.py", "harness report.json"):
        lines.append("| `%s` | %s/%s |" % (key, inv[key], inv["total"]))
    lines.append("")
    lines.append("## 校验值")
    lines.append("")
    lines.append("| instance_id | patch.diff | summary.md | verify.py | report.json | 镜像 digest |")
    lines.append("|---|---|---|---|---|---|")
    for entry in entries:
        sha = entry["sha256"]
        digest = (manifest["images"].get(entry["image"], {}).get("repo_digests") or "").strip()
        digest = digest.split(",")[0].strip() or "—"
        if "@" in digest:  # keep "sha256:..." rather than the repo prefix
            digest = digest.split("@", 1)[1]
        lines.append("| %s | `%s` | `%s` | %s | `%s` | `%s` |" % (
            entry["instance_id"],
            (sha["runs_patch.diff"] or "—")[:16],
            (sha["runs_summary.md"] or "—")[:16],
            ("`%s`" % sha["runs_verify.py"][:16]) if sha["runs_verify.py"] else "**缺失**",
            (sha["harness_report.json"] or "—")[:16],
            digest[:24],
        ))
    lines.append("")
    lines.append("> 表格中哈希为前 16 位便于阅读；完整 64 位值见 `MANIFEST_v1.json`。")
    bad_delta = [e["instance_id"] for e in entries if e["patch_delta_vs_predictions"] is False]
    images_ok = len([k for k in manifest["images"] if k != "error"])
    lines.append("> **本次生成自检**：`patch_delta_vs_predictions` 不一致 %s；"
                 "镜像 digest 解析 %d/%d；`verify.py` %d/%d。"
                 % (("**%d 条**（见 JSON）" % len(bad_delta)) if bad_delta else "0 条",
                    images_ok, len(images), inv["verify.py"], inv["total"]))
    if images_ok < len(images):
        lines.append("> ⚠️ `images` 段未取全：重跑 `python make_manifest.py`（脚本已修正格式串）。")
    lines.append("")

    md_path = os.path.join(BASE, "MANIFEST_v1.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("wrote %s and %s" % (json_path, md_path))
    print("inventory:", manifest["inventory"])
    print("swebench:", manifest["environment"]["swebench_version"],
          "| docker:", manifest["environment"]["docker_server_version"])

    # self-check: the numbers a reader must be able to trust without re-reading
    bad_delta = [e["instance_id"] for e in entries if e["patch_delta_vs_predictions"] is False]
    images_ok = len([k for k in manifest["images"] if k != "error"])
    print("self-check: patch_delta mismatches=%s | images_with_digests=%d/%d"
          % (bad_delta or "none", images_ok, len(images)))
    if bad_delta or images_ok < len(images):
        print("self-check: ATTENTION — see MANIFEST_v1.json (images section may hold an error)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
