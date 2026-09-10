"""Build predictions_v2.jsonl from runs_v2/<instance_id>/patch.diff.

v2 is the *post-evaluation repair* condition: its patches may be informed by v1
harness feedback, so v2 results must never be merged into the frozen v1 numbers.

For every instance this script also compares the v2 patch against the frozen v1
patch and writes a status table (v2_patch_status.md) so that "did we actually
change anything?" is auditable instead of assumed.

Usage:
  python make_predictions_v2.py             # only the 12 v1 failures (v2-repair)
  python make_predictions_v2.py --all       # all 37 instances (v2-blind-repeat)
"""

import glob
import hashlib
import json
import os
import sys

BASE = r"<EXP_ROOT>"
RUNS_V1 = os.path.join(BASE, "runs")
RUNS_V2 = os.path.join(BASE, "runs_v2")
OUT = os.path.join(BASE, "predictions_v2.jsonl")
STATUS_MD = os.path.join(BASE, "v2_patch_status.md")
MODEL_V2 = "glm-5.3-zcode-campaign-v2"

# the 12 instances v1 left unresolved (see comparison.md)
V1_FAILURES = [
    "django__django-11001",
    "django__django-11019",
    "django__django-11283",
    "django__django-11564",
    "django__django-11630",
    "django__django-11797",
    "django__django-12308",
    "django__django-12589",
    "django__django-12856",
    "pylint-dev__pylint-6506",
    "pytest-dev__pytest-5103",
    "pytest-dev__pytest-5221",
]


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    all_instances = "--all" in sys.argv
    v2_dirs = sorted(
        d for d in glob.glob(os.path.join(RUNS_V2, "*")) if os.path.isdir(d)
    )
    found = {os.path.basename(d): d for d in v2_dirs}

    targets = sorted(found) if all_instances else [i for i in V1_FAILURES if i in found]
    missing = [i for i in V1_FAILURES if i not in found]

    predictions = []
    rows = []
    for inst in targets:
        patch_path = os.path.join(found[inst], "patch.diff")
        if not os.path.isfile(patch_path):
            rows.append((inst, "无 patch.diff", "", ""))
            continue
        patch = read(patch_path)
        if not patch.strip():
            rows.append((inst, "空 patch.diff", "", ""))
            continue

        v1_path = os.path.join(RUNS_V1, inst, "patch.diff")
        if os.path.isfile(v1_path):
            v1_patch = read(v1_path)
            same = sha(v1_patch) == sha(patch)
            note = "与 v1 完全相同（未做修复？）" if same else "已修改"
        else:
            same, note = None, "v1 无对应补丁"

        predictions.append({
            "instance_id": inst,
            "model_name_or_path": MODEL_V2,
            "model_patch": patch,
        })
        rows.append((inst, note, sha(patch)[:16], sha(v1_patch)[:16] if os.path.isfile(v1_path) else "—"))

    with open(OUT, "w", encoding="utf-8") as f:
        for pred in predictions:
            f.write(json.dumps(pred) + "\n")

    lines = [
        "# v2 补丁状态（生成时间与 predictions_v2.jsonl 同步）",
        "",
        "模式：%s；条目数：%d；输出：`predictions_v2.jsonl`（model_name_or_path=`%s`）。"
        % ("v2-blind-repeat（全 37 条）" if all_instances else "v2-repair（v1 的 12 条失败）",
           len(predictions), MODEL_V2),
        "",
        "> v2 是**评测后修复条件**：其补丁可以使用 v1 的失败反馈。v2 结果与 v1 分数必须分列报告，"
        "不得合并统计（见 `V2_PLAN.md`）。",
        "",
        "| instance_id | 与 v1 补丁的关系 | v2 sha256(前16) | v1 sha256(前16) |",
        "|---|---|---|---|",
    ]
    for inst, note, v2sha, v1sha in rows:
        lines.append("| %s | %s | `%s` | `%s` |" % (inst, note, v2sha, v1sha))
    if missing:
        lines += ["", "尚未创建的 v2 工作目录：" + "、".join("`%s`" % m for m in missing)]
    lines += [
        "",
        "## 提醒",
        "",
        "- 每条 v2 目录必须含：`patch.diff`、`summary.md`（根因/置信度/验证命令/已知不确定性/信息条件）、"
        "`verify_output.txt`；M1 类另需 `CONTRACT_CHECKLIST.md` 填好（模板见 `runs_v2/CHECKLIST_TEMPLATE.md`）。",
        "- 若上表出现“与 v1 完全相同”，说明该条尚未真正修复，不应计入 v2 的修复率分母。",
        "",
    ]
    with open(STATUS_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("wrote %d predictions -> %s" % (len(predictions), OUT))
    print("wrote %s" % STATUS_MD)
    if missing:
        print("not yet created in runs_v2/: %s" % ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
