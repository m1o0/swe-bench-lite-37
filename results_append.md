
## 实测（2026-09-10 官方 harness，run_id=tonight）

评测输入 `predictions_swebench.jsonl`（补丁文本与 `predictions.jsonl` 逐字一致，仅键名 `patch`→`model_patch`，37/37 SHA-256 校验通过）；评测阶段未修改任何 `patch.diff`。37 条全部拿到官方判定，无镜像/容器/超时跳过。

> **唯一真源与冻结声明**：正式结果表见 `comparison.md`；上面 2026-09-08 的小节是评测前状态，仅作历史保留、不得用于统计。v1 分数在盲写条件下产生并冻结，校验清单见 `MANIFEST_v1.json`（机器可读，含逐文件 SHA-256 与 37/37 镜像 digest）与 `MANIFEST_v1.md`（人读版）；依据失败反馈修改补丁的实验一律进入 v2 条件（新 `run_id`、新预测文件、新补丁目录，见 `V2_PLAN.md`），不得覆盖或重算 v1。

**产物完整度（`make_manifest.py` 脚本实检）**：`patch.diff` 37/37、`summary.md` 37/37、`verify.py` **19/37**、官方 `report.json` 37/37。没有为 v1 缺失的 `verify.py` 事后补造文件。

| instance_id | summary.md 自报置信度 | 官方实测 | 失败归因 |
|---|---|---|---|
| django__django-10914 | high | 通过 | 通过 |
| django__django-10924 | high | 通过 | 通过 |
| django__django-11001 | high | 未通过 | 补丁已应用但未满足官方判定（M2 补丁自带运行时/语法缺陷） |
| django__django-11019 | high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节） |
| django__django-11039 | high | 通过 | 通过 |
| django__django-11049 | high | 通过 | 通过 |
| django__django-11099 | high | 通过 | 通过 |
| django__django-11133 | high | 通过 | 通过 |
| django__django-11179 | high | 通过 | 通过 |
| django__django-11283 | medium | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节） |
| django__django-11422 | high | 通过 | 通过 |
| django__django-11564 | medium | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节） |
| django__django-11583 | high | 通过 | 通过 |
| django__django-11620 | high | 通过 | 通过 |
| django__django-11630 | high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节） |
| django__django-11742 | medium-high | 通过 | 通过 |
| django__django-11797 | medium-high | 未通过 | 补丁已应用但未满足官方判定（M4 修复不完整） |
| django__django-11999 | high | 通过 | 通过 |
| django__django-12125 | high | 通过 | 通过 |
| django__django-12184 | high | 通过 | 通过 |
| django__django-12284 | high | 通过 | 通过 |
| django__django-12286 | high | 通过 | 通过 |
| django__django-12308 | high | 未通过 | 补丁已应用但未满足官方判定（M2 补丁自带运行时/语法缺陷） |
| django__django-12453 | high | 通过 | 通过 |
| django__django-12470 | medium-high | 通过 | 通过 |
| django__django-12497 | high | 通过 | 通过 |
| django__django-12589 | high | 未通过 | 补丁已应用但未满足官方判定（M3 目标通过但引入回归） |
| django__django-12700 | high | 通过 | 通过 |
| django__django-12708 | high | 通过 | 通过 |
| django__django-12856 | high | 未通过 | 补丁已应用但未满足官方判定（M2 补丁自带运行时/语法缺陷） |
| django__django-12915 | high | 通过 | 通过 |
| django__django-12983 | high | 通过 | 通过 |
| django__django-13028 | high | 通过 | 通过 |
| pylint-dev__pylint-5859 | high | 通过 | 通过 |
| pylint-dev__pylint-6506 | high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节） |
| pytest-dev__pytest-5103 | medium-high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节） |
| pytest-dev__pytest-5221 | high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节） |

**官方通过率 25/37 = 67.6%（95% Wilson 区间 51.5%–80.4%）**；自报 high 却未通过 8 条（含 medium-high 则 10 条），自报 medium/medium-high 却通过 2 条。分档读数：high 23/31、medium-high+medium 2/6——样本很小，只作描述，不做统计推断。12 条失败的上位分类是“补丁已应用但未满足官方判定”，机理见 M1–M4 子模式（只有 M1 属于契约不匹配）。逐条证据、失败子模式、分档读数与归因口径见 `comparison.md`，评测产物见 `logs/run_evaluation/tonight/` 与 `glm-5.3-zcode-campaign.tonight.json`。
