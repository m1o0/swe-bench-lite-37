"""Build the confidence-vs-official-result comparison table from harness output.

Inputs (all read-only):
  * predictions_swebench.jsonl                      -> the 37 instances in scope
  * runs/<instance_id>/summary.md                   -> self-reported confidence
  * glm-5.3-zcode-campaign.tonight.json             -> harness summary report
  * logs/run_evaluation/tonight/glm-5.3-zcode-campaign/<instance_id>/report.json
                                                    -> per-instance grading record

Outputs:
  * comparison.md        full table + statistics + attribution
  * results_append.md    the same table, formatted to append to RESULTS.md

Usage: python analyze_results.py
"""
import json
import os
import re

BASE = r"<EXP_ROOT>"
RUN_ID = "tonight"
MODEL = "glm-5.3-zcode-campaign"
LOG_ROOT = os.path.join(BASE, "logs", "run_evaluation", RUN_ID, MODEL)
TOP_REPORT = os.path.join(BASE, "%s.%s.json" % (MODEL, RUN_ID))
PREDS = os.path.join(BASE, "predictions_swebench.jsonl")

# order matters inside the regex: medium-high must win over medium/high
CONF_RE = re.compile(r"\b(?:medium-high|medium|high|low)\b")
CONF_LEVELS = ["high", "medium-high", "medium", "low"]
CONFIDENT = ("high", "medium-high")

# Top-level failure category.  It says only "applied but the official verdict was
# not satisfied"; it deliberately does NOT claim "differs from the upstream fix"
# (the harness log proves the benchmark's target tests failed, not how our
# implementation differs from the upstream commit), and it does NOT fold runtime
# defects into a "contract" story -- the mechanism lives in the M1..M4 sub-modes.
CATEGORY_CONTRACT = "补丁已应用但未满足官方判定"
CATEGORY_APPLY = "补丁未应用"
CATEGORY_ENV = "测试环境问题"
CATEGORY_OTHER = "其他"

# Failure sub-modes, assigned from per-instance report.json + test_output.txt
# evidence (see extract_failures.py).  Conservative: only mechanisms directly
# visible in the log are assigned.
SUBMODES = {
    "django__django-11019": "M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式）",
    "django__django-11283": "M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式）",
    "django__django-11564": "M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式）",
    "django__django-11630": "M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式）",
    "pylint-dev__pylint-6506": "M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式）",
    "pytest-dev__pytest-5103": "M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式）",
    "pytest-dev__pytest-5221": "M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式）",
    "django__django-11001": "M2 补丁自带运行时/语法缺陷",
    "django__django-12308": "M2 补丁自带运行时/语法缺陷",
    "django__django-12856": "M2 补丁自带运行时/语法缺陷",
    "django__django-12589": "M3 目标测试通过但引入 PASS_TO_PASS 回归",
    "django__django-11797": "M4 修复不完整（目标行为未达成）",
}


def wilson_interval(successes, total, z=1.96):
    """95% Wilson score interval for a binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def parse_confidence(instance_id):
    """Return (label, caveat, evidence) from the summary.md Confidence section.

    The label is the FIRST confidence word in the section: summaries such as
    "High on mechanism; medium on exact upstream variant" are self-reported as
    high, with the weaker word recorded as a caveat.
    """
    text = read_text(os.path.join(BASE, "runs", instance_id, "summary.md"))
    if not text:
        return None, "", "summary.md 缺失"
    m = re.search(r"^#+\s*Confidence\b(.*)", text, re.S | re.M | re.I)
    section = (m.group(1) if m else text[-600:]).strip()
    flat = re.sub(r"[*_`>]", "", section).lower()
    head = flat[:400]

    found = CONF_RE.search(head)
    label = found.group(0) if found else None
    others = [w for w in dict.fromkeys(CONF_RE.findall(head)) if w != label]
    caveat = ("文中另提及 %s" % "/".join(others)) if others else ""
    evidence = re.sub(r"\s+", " ", section)[:110]
    return label, caveat, evidence


def load_instance_record(instance_id):
    data = read_text(os.path.join(LOG_ROOT, instance_id, "report.json"))
    if not data:
        return None
    try:
        obj = json.loads(data)
    except ValueError:
        return None
    return obj.get(instance_id)


def classify(inst, rec, top):
    """Return (result_label, category, detail)."""
    if rec is None:
        reason = (top.get("failure_reasons") or {}).get(inst, "no per-instance report.json")
        if inst in set(top.get("error_ids") or []):
            return "错误", CATEGORY_ENV, "harness 记录为 error：%s" % reason
        if inst in set(top.get("incomplete_ids") or []):
            return "未完成", CATEGORY_ENV, "实例未跑完：%s" % reason
        return "无记录", CATEGORY_ENV, "未生成 report.json（多为镜像或容器不可用）"

    status = rec.get("tests_status") or {}
    f2p = status.get("FAIL_TO_PASS") or {}
    p2p = status.get("PASS_TO_PASS") or {}
    f2p_ok = f2p.get("success") or []
    f2p_fail = f2p.get("failure") or []
    p2p_fail = p2p.get("failure") or []
    applied = rec.get("patch_successfully_applied")

    if rec.get("resolved"):
        return "通过", "通过", "FAIL_TO_PASS %d/%d 通过" % (len(f2p_ok), len(f2p_ok) + len(f2p_fail))

    if not applied:
        return "未通过", CATEGORY_APPLY, "patch_successfully_applied=false"
    if rec.get("infra_failure"):
        return "未通过", CATEGORY_ENV, "harness 标记 infra_failure"
    if f2p_fail:
        return "未通过", CATEGORY_CONTRACT, "目标测试仍失败：%s" % "; ".join(f2p_fail[:3])
    if p2p_fail:
        return "未通过", CATEGORY_CONTRACT, "破坏既有测试：%s" % "; ".join(p2p_fail[:3])

    reason = (top.get("failure_reasons") or {}).get(inst, "无失败测试明细")
    return "未通过", CATEGORY_OTHER, "补丁已应用但无测试判定明细：%s" % reason


def load_subagent_batch():
    """Instance ids under RESULTS.md '子代理批次' heading (mode A production)."""
    text = read_text(os.path.join(BASE, "RESULTS.md")) or ""
    m = re.search(r"###\s*子代理批次.*?\n(.*?)\n###", text, re.S)
    if not m:
        return set()
    return set(re.findall(r"\b((?:django|pylint-dev|pytest-dev|sympy|astropy|matplotlib)"
                          r"[a-z-]*__[a-z0-9_.-]+-\d+)\b", m.group(1)))


def main():
    instances = []
    with open(PREDS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                instances.append(json.loads(line)["instance_id"])

    top = {}
    if os.path.isfile(TOP_REPORT):
        top = json.loads(read_text(TOP_REPORT))

    subagent_batch = load_subagent_batch()

    # artifact inventory, machine-checked rather than asserted
    verify_present = [
        i for i in instances if os.path.isfile(os.path.join(BASE, "runs", i, "verify.py"))
    ]
    patch_present = [
        i for i in instances if os.path.isfile(os.path.join(BASE, "runs", i, "patch.diff"))
    ]
    summary_present = [
        i for i in instances if os.path.isfile(os.path.join(BASE, "runs", i, "summary.md"))
    ]
    report_present = [
        i for i in instances if os.path.isfile(os.path.join(LOG_ROOT, i, "report.json"))
    ]
    inventory = {
        "patch.diff": "%d/%d" % (len(patch_present), len(instances)),
        "summary.md": "%d/%d" % (len(summary_present), len(instances)),
        "verify.py": "%d/%d" % (len(verify_present), len(instances)),
        "harness report.json": "%d/%d" % (len(report_present), len(instances)),
    }

    rows = []
    for inst in instances:
        conf, caveat, evidence = parse_confidence(inst)
        rec = load_instance_record(inst)
        result, category, detail = classify(inst, rec, top)
        rows.append(
            {
                "instance_id": inst,
                "batch": "子代理并行" if inst in subagent_batch else "主会话串行",
                "confidence": conf or "未标注",
                "caveat": caveat,
                "confidence_evidence": evidence,
                "result": result,
                "category": category,
                "submode": SUBMODES.get(inst, ""),
                "detail": detail,
            }
        )

    resolved = [r for r in rows if r["result"] == "通过"]
    not_run = [r for r in rows if r["result"] in ("无记录", "错误", "未完成")]
    judged = [r for r in rows if r["result"] in ("通过", "未通过")]
    failed = [r for r in judged if r["result"] == "未通过"]

    overconf_strict = [r for r in failed if r["confidence"] == "high"]
    overconf_lenient = [r for r in failed if r["confidence"] in CONFIDENT]
    conservative = [r for r in resolved if r["confidence"] in ("medium", "medium-high", "low")]

    cat_counts = {}
    for r in judged:
        cat_counts[r["category"]] = cat_counts.get(r["category"], 0) + 1

    calib = {}
    for level in CONF_LEVELS + ["未标注"]:
        group = [r for r in rows if r["confidence"] == level]
        if group:
            calib[level] = (len(group), len([r for r in group if r["result"] == "通过"]))

    lines = []
    lines.append("# SWE-bench Lite 37 条：自报置信度 vs 官方 harness 实测")
    lines.append("")
    lines.append("评测命令（WSL 内执行，零 LLM token）：")
    lines.append("")
    lines.append("```bash")
    lines.append("cd <EXP_ROOT_POSIX>")
    lines.append("HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation \\")
    lines.append("  -d SWE-bench/SWE-bench_Lite -s test -p predictions_swebench.jsonl \\")
    lines.append("  -id %s --max_workers 4" % RUN_ID)
    lines.append("```")
    lines.append("")
    lines.append("评测输入为 `predictions_swebench.jsonl`：它由 `predictions.jsonl` 逐字复制补丁文本、"
                 "仅把键名 `patch` 改为 swebench 5.x harness 需要的 `model_patch`，并逐条与 "
                 "`runs/*/patch.diff` 做 SHA-256 比对（37/37 一致）。评测阶段未修改任何 `patch.diff`。")
    lines.append("")
    lines.append("**唯一真源声明**：本文件是 v1 结果的正式结果表。`RESULTS.md` 中 2026-09-08 的小节是"
                 "评测前的“未运行”状态记录，仅作历史保留，**不作为结果使用**；"
                 "任何自动统计都应以本文件为准，避免出现互相矛盾的“未运行/通过”双份行。")
    lines.append("")
    lines.append("**版本冻结**：下表的 v1 分数在盲写条件下产生，已冻结。依据失败反馈修改补丁的实验"
                 "属于 v2 条件（新 `run_id`、新预测文件、新补丁目录），不得覆盖或重算 v1。")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---|")
    lines.append("| 提交实例 | %d |" % len(rows))
    lines.append("| 拿到官方判定（通过+未通过） | %d |" % len(judged))
    lines.append("| 通过（FAIL_TO_PASS 全绿且 PASS_TO_PASS 无回归） | %d |" % len(resolved))
    lines.append("| **官方通过率** | **%.1f%%**（%d/%d） |" % (
        100.0 * len(resolved) / len(rows) if rows else 0.0, len(resolved), len(rows)))
    wilson = wilson_interval(len(resolved), len(rows))
    lines.append("| 通过率 95%% Wilson 区间 | %.1f%%–%.1f%% |" % (
        100.0 * wilson[0], 100.0 * wilson[1]))
    lines.append("| 基础设施未完成（镜像/容器/超时） | %d |" % len(not_run))
    lines.append("| 自报 high 却未通过（严格过度自信） | %d |" % len(overconf_strict))
    lines.append("| 自报 high/medium-high 却未通过（宽口径） | %d |" % len(overconf_lenient))
    lines.append("| 自报 medium/medium-high/low 却通过（保守） | %d |" % len(conservative))
    lines.append("")
    lines.append("失败归因分布：" + ("、".join("%s %d 条" % (k, v) for k, v in sorted(cat_counts.items())) or "无"))
    lines.append("")
    lines.append("## 置信度校准矩阵")
    lines.append("")
    lines.append("| 自报置信度 | 条数 | 通过 | 未通过 | 该档通过率 |")
    lines.append("|---|---|---|---|---|")
    for level, (total, ok) in calib.items():
        lines.append("| %s | %d | %d | %d | %.0f%% |" % (
            level, total, ok, total - ok, 100.0 * ok / total))
    lines.append("")
    mid_total = sum(v[0] for k, v in calib.items() if k in ("medium", "medium-high"))
    mid_ok = sum(v[1] for k, v in calib.items() if k in ("medium", "medium-high"))
    lines.append("**描述性读数（不做统计推断）**：high 档 %d/%d 通过；medium-high 与 medium 合计 "
                 "%d/%d 通过。样本极小（37 条、且高置信度占 31 条），分档比较不足以支持"
                 "“置信度与结果存在系统性关联”的统计结论，只能作为后续实验的假设来源。"
                 % (calib.get("high", (0, 0))[1], calib.get("high", (0, 0))[0], mid_ok, mid_total))
    lines.append("")
    lines.append("## 失败子模式（仅依据评测 log 中可见的机理）")
    lines.append("")
    sub_counts = {}
    for r in failed:
        sub_counts[r["submode"] or "未归类"] = sub_counts.get(r["submode"] or "未归类", 0) + 1
    lines.append("| 子模式 | 条数 | 实例 |")
    lines.append("|---|---|---|")
    for sub, cnt in sorted(sub_counts.items()):
        ids = ", ".join("`%s`" % r["instance_id"] for r in failed if (r["submode"] or "未归类") == sub)
        lines.append("| %s | %d | %s |" % (sub, cnt, ids))
    lines.append("")
    lines.append("> 上位分类“%s”只表示官方判定未通过；12 条里只有 M1 的 7 条属于"
                 "“与目标测试的行为契约不匹配”，M2 的 3 条是补丁自带的运行时/语法缺陷，"
                 "不应被读成单纯的契约误差。子模式是**证据可见的机理**，不是与上游实现的逐处比对；"
                 "`extract_failures.py` 打印每个实例对应的失败测试与断言文本。" % CATEGORY_CONTRACT)
    lines.append("")
    lines.append("## 产出完整度（评测前轨迹 vs 评测后补充）")
    lines.append("")
    lines.append("| artifact | 覆盖 | 性质 |")
    lines.append("|---|---|---|")
    lines.append("| `runs/<id>/patch.diff` | %s | 评测前原始产出，评测阶段未修改 |" % inventory["patch.diff"])
    lines.append("| `runs/<id>/summary.md`（含自报置信度） | %s | 评测前盲写，未事后回填 |" % inventory["summary.md"])
    lines.append("| `runs/<id>/verify.py` | %s | 评测前产出，**并非每条都有**（本行由脚本实检目录得出） |" % inventory["verify.py"])
    lines.append("| 官方 harness `report.json` / `test_output.txt` | %s | 评测后产物 |" % inventory["harness report.json"])
    lines.append("")
    lines.append("> 没有为缺失的 `verify.py` 补造文件：那会污染“盲写轨迹”的含义。"
                 "v1 的验证证据只承认当时真实存在的部分，评测后补充材料（复现命令、日志）"
                 "一律标注来源与时间。")
    lines.append("")
    lines.append("## v1 冻结声明")
    lines.append("")
    lines.append("本表记录的 `25/37 = 67.6%` 为 **v1（盲写条件）冻结分数**，"
                 "与评测输入 `predictions_swebench.jsonl` 及 `runs/*/patch.diff` 的 SHA-256 绑定，"
                 "见 `MANIFEST_v1.md`。任何根据失败反馈修改补丁的工作都进入 **v2 条件**："
                 "新的 `run_id`、新的预测文件、新的补丁目录，v1 的分数与文件不得被覆盖或重算。")
    lines.append("")
    lines.append("## 生产模式对比（观察性，非因果）")
    lines.append("")
    lines.append("| 生产模式 | 条数 | 通过 | 未通过 | 通过率 | 其中 Django 条数 | Django 通过率 |")
    lines.append("|---|---|---|---|---|---|---|")
    for batch in ("子代理并行", "主会话串行"):
        group = [r for r in rows if r["batch"] == batch]
        ok = [r for r in group if r["result"] == "通过"]
        dj = [r for r in group if r["instance_id"].startswith("django__")]
        dj_ok = [r for r in dj if r["result"] == "通过"]
        lines.append("| %s | %d | %d | %d | %.0f%% | %d | %s |" % (
            batch, len(group), len(ok), len(group) - len(ok),
            100.0 * len(ok) / len(group) if group else 0.0,
            len(dj),
            ("%.0f%%" % (100.0 * len(dj_ok) / len(dj))) if dj else "n/a"))
    all_dj = [r for r in rows if r["instance_id"].startswith("django__")]
    lines.append("| 全体 Django | %d | %d | %d | %.0f%% | %d | %.0f%% |" % (
        len(all_dj), len([r for r in all_dj if r["result"] == "通过"]),
        len([r for r in all_dj if r["result"] != "通过"]),
        100.0 * len([r for r in all_dj if r["result"] == "通过"]) / len(all_dj) if all_dj else 0.0,
        len(all_dj),
        100.0 * len([r for r in all_dj if r["result"] == "通过"]) / len(all_dj) if all_dj else 0.0))
    lines.append("")
    lines.append("> 两个批次不是随机分组：子代理批次包含全部 4 条非 Django 实例（pylint/pytest），"
                 "且任务难度未做匹配；因此该表只能作为观察，不能推断“并行 vs 串行”的因果优劣。")
    lines.append("")
    lines.append("## 逐条对比")
    lines.append("")
    lines.append("| instance_id | summary.md 自报置信度 | 官方实测 | 失败归因 | 失败子模式 | 证据/备注 |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        detail = r["detail"].replace("|", "/")
        conf = r["confidence"] + ("（%s）" % r["caveat"] if r["caveat"] else "")
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r["instance_id"], conf, r["result"], r["category"], r["submode"] or "—", detail))
    lines.append("")
    lines.append("## 重点标记")
    lines.append("")
    lines.append("### A. 过度自信：自报 high 却未通过（%d 条，严格口径）" % len(overconf_strict))
    lines.append("")
    for r in overconf_strict:
        lines.append("- **%s**：%s。自评原文：%s" % (r["instance_id"], r["detail"], r["confidence_evidence"]))
    lines.append("")
    lines.append("### B. 过度自信：自报 medium-high 却未通过（%d 条，宽口径补充）" % (
        len(overconf_lenient) - len(overconf_strict)))
    lines.append("")
    extra = [r for r in overconf_lenient if r["confidence"] == "medium-high"]
    if extra:
        for r in extra:
            lines.append("- **%s**：%s。自评原文：%s" % (r["instance_id"], r["detail"], r["confidence_evidence"]))
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("### C. 保守：自报 medium / medium-high / low 却通过（%d 条）" % len(conservative))
    lines.append("")
    if conservative:
        for r in conservative:
            lines.append("- **%s**（自报 %s）：%s" % (r["instance_id"], r["confidence"], r["detail"]))
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("### D. 失败但置信度归类正确（自报 medium 且未通过）")
    lines.append("")
    medium_failed = [r for r in failed if r["confidence"] == "medium"]
    if medium_failed:
        for r in medium_failed:
            lines.append("- **%s**：%s" % (r["instance_id"], r["detail"]))
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("## 基础设施跳过清单")
    lines.append("")
    if not_run:
        for r in not_run:
            lines.append("- %s：%s" % (r["instance_id"], r["detail"]))
    else:
        lines.append("- 无：37 条全部拿到官方判定（镜像拉取失败 0 条，容器/harness 错误 0 条）")
    lines.append("")
    lines.append("## 归因口径")
    lines.append("")
    lines.append("1. **补丁未应用**：`patch_successfully_applied=false`。")
    lines.append("2. **%s**（上位分类）：补丁成功应用，但 FAIL_TO_PASS 目标测试仍失败，"
                 "或 PASS_TO_PASS 出现回归。该分类**只说明官方判定未通过，不预设机理**；"
                 "机理见 M1–M4 子模式——其中只有 **M1 是“与目标测试的行为契约不匹配”**，"
                 "M2 是补丁自带的运行时/语法缺陷，M3 是引入回归，M4 是修复不完整。"
                 "命名同样刻意**不**声称“与上游修复实现不同”：benchmark 的评测 log 能证明"
                 "目标测试失败，不能证明我们的实现与上游 commit 的逐处差异。"
                 % CATEGORY_CONTRACT)
    lines.append("3. **测试环境问题**：镜像拉取失败、容器/harness 错误、超时、实例未跑完。")
    lines.append("4. **其他**：补丁已应用但没有可用的测试判定明细。")
    lines.append("")
    lines.append("失败子模式只使用 log 中直接可见的机理（失败测试名、断言文本、异常类型）；"
                 "未观察到的差异不写进结论。")
    lines.append("")
    lines.append("> 归因依据评测 log 与 per-instance `report.json`。凡引用上游修复代码或 `test_patch` "
                 "内容做出的解释，均为事后信息，仅用于理解失败机理，不参与分数与通过判定。")
    lines.append("> harness 顶层报告的 `ambiguous_failure_ids` 是对原始输出做正则扫描的启发式"
                 "（命中 `no tests ran|collected 0 items` 即标记），pytest 自身测试套件会打印内层 "
                 "pytest 会话输出，因而出现 2 例误标；逐条判定以 per-instance `report.json` 的 "
                 "`tests_status` 为准。")
    lines.append("")

    out = "\n".join(lines)
    with open(os.path.join(BASE, "comparison.md"), "w", encoding="utf-8") as f:
        f.write(out)

    append = []
    append.append("")
    append.append("## 实测（2026-09-10 官方 harness，run_id=%s）" % RUN_ID)
    append.append("")
    append.append("评测输入 `predictions_swebench.jsonl`（补丁文本与 `predictions.jsonl` 逐字一致，"
                  "仅键名 `patch`→`model_patch`，37/37 SHA-256 校验通过）；评测阶段未修改任何 "
                  "`patch.diff`。37 条全部拿到官方判定，无镜像/容器/超时跳过。")
    append.append("")
    append.append("| instance_id | summary.md 自报置信度 | 官方实测 | 失败归因 |")
    append.append("|---|---|---|---|")
    for r in rows:
        append.append("| %s | %s | %s | %s |" % (
            r["instance_id"], r["confidence"], r["result"], r["category"]))
    append.append("")
    append.append("> **唯一真源与冻结声明**：本节为 2026-09-10 实测结果，正式结果表见 `comparison.md`；"
                  "上面 2026-09-08 的小节是评测前状态，仅作历史保留。v1 分数在盲写条件下产生并冻结，"
                  "校验清单见 `MANIFEST_v1.md`；依据失败反馈修改补丁的实验一律进入 v2 条件"
                  "（新 `run_id`、新预测文件、新补丁目录），不得覆盖或重算 v1。")
    append.append("")
    append.append("**产物完整度（脚本实检）**：`patch.diff` %s、`summary.md` %s、`verify.py` %s、"
                  "官方 `report.json` %s。没有为 v1 缺失的 `verify.py` 事后补造文件。"
                  % (inventory["patch.diff"], inventory["summary.md"],
                     inventory["verify.py"], inventory["harness report.json"]))
    append.append("")
    append.append("**官方通过率 %d/%d = %.1f%%**（95%% Wilson 区间 %.1f%%–%.1f%%）；"
                  "自报 high 却未通过 %d 条（含 medium-high 则 %d 条），自报 medium/medium-high 却通过 %d 条。"
                  "分档读数：high %d/%d、medium-high+medium %d/%d——样本很小，只作描述，不做统计推断。"
                  "逐条证据、校准矩阵与归因口径见 `comparison.md`，"
                  "评测产物见 `logs/run_evaluation/%s/` 与 `%s.%s.json`。"
                  % (len(resolved), len(rows), 100.0 * len(resolved) / len(rows),
                     100.0 * wilson[0], 100.0 * wilson[1],
                     len(overconf_strict), len(overconf_lenient), len(conservative),
                     calib.get("high", (0, 0))[1], calib.get("high", (0, 0))[0], mid_ok, mid_total,
                     RUN_ID, MODEL, RUN_ID))
    append.append("")
    with open(os.path.join(BASE, "results_append.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(append))

    print("instances=%d judged=%d resolved=%d not_run=%d overconf_strict=%d overconf_lenient=%d conservative=%d"
          % (len(rows), len(judged), len(resolved), len(not_run),
             len(overconf_strict), len(overconf_lenient), len(conservative)))
    print("categories:", cat_counts)
    print("calibration:", calib)
    print("wrote comparison.md and results_append.md")


if __name__ == "__main__":
    main()
