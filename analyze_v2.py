"""Build comparison_v2.md: the v2 (post-evaluation repair) result table.

Hard rule enforced by this script: v1 and v2 are reported side by side and are
NEVER merged into a single pass rate. v1 (`run_id=tonight`, blinded) is frozen;
v2 (`run_id=tonight-v2`, feedback-informed) is a different condition.

Outputs: comparison_v2.md (and v2_append.md with the same table, for appending).

Usage: python analyze_v2.py
"""

import glob
import hashlib
import json
import os
import re
import time

BASE = r"<EXP_ROOT>"
RUNS_V1 = os.path.join(BASE, "runs")
RUNS_V2 = os.path.join(BASE, "runs_v2")
PREDS_V2 = os.path.join(BASE, "predictions_v2.jsonl")

V1_RUN_ID = "tonight"
V1_MODEL = "glm-5.3-zcode-campaign"
V1_LOG = os.path.join(BASE, "logs", "run_evaluation", V1_RUN_ID, V1_MODEL)

V2_RUN_ID = os.environ.get("V2_RUN_ID", "tonight-v2")
V2_MODEL = "glm-5.3-zcode-campaign-v2"
V2_LOG = os.path.join(BASE, "logs", "run_evaluation", V2_RUN_ID, V2_MODEL)

CONF_RE = re.compile(r"\b(?:medium-high|medium|high|low)\b")
CONF_LEVELS = ["high", "medium-high", "medium", "low"]


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verdict(log_root, instance_id):
    """Return (label, detail) from a harness log tree; '无记录' when missing."""
    data = read(os.path.join(log_root, instance_id, "report.json"))
    if not data:
        return "无记录", "未生成 report.json（未跑或环境失败）"
    try:
        rec = json.loads(data).get(instance_id)
    except ValueError:
        return "无记录", "report.json 解析失败"
    if not rec:
        return "无记录", "report.json 无该实例"
    status = rec.get("tests_status") or {}
    f2p = (status.get("FAIL_TO_PASS") or {}).get("failure") or []
    p2p = (status.get("PASS_TO_PASS") or {}).get("failure") or []
    if rec.get("resolved"):
        return "通过", "FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归"
    if not rec.get("patch_successfully_applied"):
        return "未通过", "补丁未应用"
    if f2p:
        return "未通过", "目标测试仍失败：%s" % "; ".join(f2p[:2])
    if p2p:
        return "未通过", "破坏既有测试：%s" % "; ".join(p2p[:2])
    return "未通过", "补丁已应用但无测试判定明细"


def confidence(path):
    text = read(path)
    if not text:
        return "未标注", ""
    m = re.search(r"^#+\s*Confidence\b(.*)", text, re.S | re.M | re.I)
    section = (m.group(1) if m else text[-500:]).strip()
    flat = re.sub(r"[*_`>]", "", section).lower()[:400]
    hit = CONF_RE.search(flat)
    return (hit.group(0) if hit else "未标注"), re.sub(r"\s+", " ", section)[:100]


def info_condition(path):
    """Extract the declared 信息条件 (which v1 feedback informed this patch)."""
    text = read(path) or ""
    m = re.search(r"信息条件[^\n]*\n+([^\n#]+)", text)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:120]
    return "（未声明）"


def main():
    if not os.path.isfile(PREDS_V2):
        raise SystemExit("predictions_v2.jsonl 不存在：先运行 make_predictions_v2.py")

    instances = []
    with open(PREDS_V2, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                instances.append(json.loads(line)["instance_id"])

    rows = []
    for inst in instances:
        v1_label, v1_detail = verdict(V1_LOG, inst)
        v2_label, v2_detail = verdict(V2_LOG, inst)

        conf, conf_ev = confidence(os.path.join(RUNS_V2, inst, "summary.md"))
        cond = info_condition(os.path.join(RUNS_V2, inst, "summary.md"))

        v1_patch = read(os.path.join(RUNS_V1, inst, "patch.diff"))
        v2_patch = read(os.path.join(RUNS_V2, inst, "patch.diff"))
        if v1_patch is None or v2_patch is None:
            patch_state = "缺失"
        elif sha(v1_patch) == sha(v2_patch):
            patch_state = "与 v1 相同"
        else:
            patch_state = "已修改"

        if v2_label == "无记录":
            transition = "未运行"
        elif v1_label == "通过" and v2_label == "未通过":
            transition = "**新回归**"
        elif v1_label == "未通过" and v2_label == "通过":
            transition = "转绿"
        elif v1_label == "未通过" and v2_label == "未通过":
            transition = "仍红"
        elif v1_label == "通过" and v2_label == "通过":
            transition = "保持通过"
        else:
            transition = "v1 无判定"

        rows.append({
            "instance_id": inst,
            "v1": v1_label, "v1_detail": v1_detail,
            "v2": v2_label, "v2_detail": v2_detail,
            "transition": transition,
            "confidence": conf, "confidence_evidence": conf_ev,
            "info_condition": cond, "patch_state": patch_state,
        })

    ran = [r for r in rows if r["v2"] != "无记录"]
    fixed = [r for r in rows if r["transition"] == "转绿"]
    still = [r for r in rows if r["transition"] == "仍红"]
    regressed = [r for r in rows if r["transition"] == "**新回归**"]
    not_attempted = [r for r in rows if r["patch_state"] == "与 v1 相同"]

    calib = {}
    for level in CONF_LEVELS + ["未标注"]:
        group = [r for r in ran if r["confidence"] == level]
        if group:
            calib[level] = (len(group), len([r for r in group if r["v2"] == "通过"]))

    lines = []
    lines.append("# v2（评测后修复条件）结果表 — run_id `%s`" % V2_RUN_ID)
    lines.append("")
    lines.append("生成时间：`%s`" % time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    lines.append("")
    lines.append("> **与 v1 的边界（不可协商）**：v1（`run_id=%s`，盲写条件，25/37 = 67.6%%）已冻结，"
                 "唯一真源是 `comparison.md`。本文件的 v2 分数是**另一个条件**下的结果："
                 "其补丁可以使用 v1 的失败反馈。两套数字**必须分列报告，禁止合并统计**。"
                 % V1_RUN_ID)
    lines.append("")
    lines.append("## v2 总览")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---|")
    lines.append("| v2 条目 | %d |" % len(rows))
    lines.append("| 已跑（拿到判定） | %d |" % len(ran))
    lines.append("| v2 通过 | %d |" % len([r for r in ran if r["v2"] == "通过"]))
    lines.append("| v1→v2 转绿 | %d |" % len(fixed))
    lines.append("| v1→v2 仍红 | %d |" % len(still))
    lines.append("| v1→v2 新回归 | %d |" % len(regressed))
    lines.append("| 补丁与 v1 相同（未真正修复，不计入修复率分母） | %d |" % len(not_attempted))
    lines.append("")
    if not ran:
        lines.append("> **v2 尚未运行**：上面除“v2 条目”外的计数为空态。"
                     "运行 `bash run_eval_v2.sh` 后重跑本脚本即可填充。")
        lines.append("")
    lines.append("## 逐条转移表")
    lines.append("")
    lines.append("| instance_id | v1（冻结） | v2 | 转移 | v2 自报置信度 | 信息条件 | 补丁状态 | v2 证据 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["instance_id"], r["v1"], r["v2"], r["transition"], r["confidence"],
            r["info_condition"], r["patch_state"], r["v2_detail"].replace("|", "/")))
    lines.append("")
    lines.append("## v2 置信度分档读数（描述性，不做统计推断）")
    lines.append("")
    lines.append("| 自报置信度 | 条数 | 通过 | 该档通过率 |")
    lines.append("|---|---|---|---|")
    for level, (total, ok) in calib.items():
        lines.append("| %s | %d | %d | %.0f%% |" % (level, total, ok, 100.0 * ok / total))
    lines.append("")
    lines.append("## 需要一起报告的三件事")
    lines.append("")
    lines.append("1. **v1 与 v2 是不同条件**：v1 盲写、v2 见失败反馈；"
                 "把两者相加得到的“总通过率”没有意义。")
    lines.append("2. **修复率的分母**：只算真正改过的补丁（上表“补丁状态=已修改”）；"
                 "与 v1 完全相同却计入修复率会高估。")
    lines.append("3. **新回归要单独列**：v2 修好一条却弄坏另一条，与“没修好”是不同性质的失败。")
    lines.append("")
    lines.append("## 尚未创建的 v2 目录")
    lines.append("")
    missing = [i for i in instances if not os.path.isdir(os.path.join(RUNS_V2, i))]
    if missing:
        lines.append("- " + "、".join("`%s`" % m for m in missing))
    else:
        lines.append("- 无")
    lines.append("")

    out = "\n".join(lines)
    with open(os.path.join(BASE, "comparison_v2.md"), "w", encoding="utf-8") as f:
        f.write(out)

    print("v2 entries=%d ran=%d fixed=%d still_failing=%d regressions=%d unchanged_patches=%d"
          % (len(rows), len(ran), len(fixed), len(still), len(regressed), len(not_attempted)))
    print("wrote comparison_v2.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
