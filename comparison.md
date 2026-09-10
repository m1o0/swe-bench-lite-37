# SWE-bench Lite 37 条：自报置信度 vs 官方 harness 实测（v1，已冻结）

评测命令（WSL 内执行，零 LLM token）：

```bash
cd <EXP_ROOT_POSIX>
HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation \
  -d SWE-bench/SWE-bench_Lite -s test -p predictions_swebench.jsonl \
  -id tonight --max_workers 4
```

评测输入为 `predictions_swebench.jsonl`：它由 `predictions.jsonl` 逐字复制补丁文本、仅把键名 `patch` 改为 swebench 5.x harness 需要的 `model_patch`，并逐条与 `runs/*/patch.diff` 做 SHA-256 比对（37/37 一致）。评测阶段未修改任何 `patch.diff`。

**唯一真源声明**：本文件是 v1 结果的正式结果表。`RESULTS.md` 中 2026-09-08 的小节是评测前的“未运行”状态记录，仅作历史保留，**不作为结果使用**；任何自动统计都应以本文件为准，避免出现互相矛盾的“未运行/通过”双份行。

**版本冻结**：下表的 v1 分数在盲写条件下产生，已冻结。逐文件 SHA-256、数据集 parquet 哈希、镜像 digest 与环境版本已由 `make_manifest.py` 落盘：`MANIFEST_v1.json`（机器可读）+ `MANIFEST_v1.md`（人读版）。脚本实检：`patch.diff` 37/37、`summary.md` 37/37、`verify.py` **19/37**、`report.json` 37/37，`patch_delta_vs_predictions` **37/37 为 `true`**（源补丁=预测文件=评测输入，三方一致）。
（**生成自检**：`patch_delta_vs_predictions` 不一致 0 条；镜像 digest **37/37** 已记录并与本地 `image_id` 一致。首轮暴露的两处脚本缺陷——`wsl.exe` UTF-16 输出污染环境字段、`docker inspect` 格式串含 `|` 被 shell 拆解——均已修复并重跑验证。）
依据失败反馈修改补丁的实验属于 v2 条件（新 `run_id`、新预测文件、新补丁目录），不得覆盖或重算 v1；v2 方案见 `V2_PLAN.md`（脚手架已就绪，尚未运行）。

## 总览

| 指标 | 数值 |
|---|---|
| 提交实例 | 37 |
| 拿到官方判定（通过+未通过） | 37 |
| 通过（FAIL_TO_PASS 全绿且 PASS_TO_PASS 无回归） | 25 |
| **官方通过率** | **67.6%**（25/37） |
| 通过率 95% Wilson 区间 | 51.5%–80.4% |
| 基础设施未完成（镜像/容器/超时） | 0 |
| 自报 high 却未通过（严格过度自信） | 8 |
| 自报 high/medium-high 却未通过（宽口径） | 10 |
| 自报 medium/medium-high/low 却通过（保守） | 2 |

失败归因分布（上位分类）：**补丁已应用但未满足官方判定 12 条**、通过 25 条。
上位分类只表示官方判定未通过，机理见下表 M1–M4。

## 置信度分档读数（描述性，不做统计推断）

| 自报置信度 | 条数 | 通过 | 未通过 | 该档通过率 |
|---|---|---|---|---|
| high | 31 | 23 | 8 | 74% |
| medium-high | 4 | 2 | 2 | 50% |
| medium | 2 | 0 | 2 | 0% |

**描述性读数**：high 档 23/31 通过；medium-high 与 medium 合计 2/6 通过。样本极小（37 条，且其中 31 条自报 high），分档比较不足以支持“置信度与结果存在系统性关联”的统计结论，只能作为后续实验（v2）的假设来源。

## 失败子模式（仅依据评测 log 中可见的机理）

| 子模式 | 条数 | 实例 |
|---|---|---|
| M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式） | 7 | `django__django-11019`, `django__django-11283`, `django__django-11564`, `django__django-11630`, `pylint-dev__pylint-6506`, `pytest-dev__pytest-5103`, `pytest-dev__pytest-5221` |
| M2 补丁自带运行时/语法缺陷 | 3 | `django__django-11001`, `django__django-12308`, `django__django-12856` |
| M3 目标测试通过但引入 PASS_TO_PASS 回归 | 1 | `django__django-12589` |
| M4 修复不完整（目标行为未达成） | 1 | `django__django-11797` |

> 上位分类“补丁已应用但未满足官方判定”只表示官方判定未通过；12 条里只有 M1 的 7 条属于
> “与目标测试的行为契约不匹配”，M2 的 3 条是补丁自带的运行时/语法缺陷，
> 不应被读成单纯的契约误差。子模式是**证据可见的机理**（失败测试名、断言文本、异常类型），
> 不是与上游实现的逐处比对；`extract_failures.py` 会打印每个实例对应的失败测试与断言文本。

## 产出完整度（评测前轨迹 vs 评测后补充）

| artifact | 覆盖 | 性质 |
|---|---|---|
| `runs/<id>/patch.diff` | 37/37 | 评测前原始产出，评测阶段未修改（38 个文件 mtime 全为 2026-09-06） |
| `runs/<id>/summary.md`（含自报置信度） | 37/37 | 评测前盲写，未事后回填 |
| `runs/<id>/verify.py` | **19/37** | 评测前产出，**并非每条都有**（`make_manifest.py` 脚本实检，非人工估计） |
| 官方 harness `report.json` / `test_output.txt` | 37/37 | 评测后产物 |

> 没有为缺失的 `verify.py` 补造文件：那会污染“盲写轨迹”的含义。v1 的验证证据只承认当时真实存在的部分；评测后补充材料（复现命令、日志、清单）一律标注来源与时间。

## v1 冻结声明

本文件的 `25/37 = 67.6%` 为 **v1（盲写条件）冻结分数**，哈希绑定已落盘：`MANIFEST_v1.json` 记录 37 条实例的 `patch.diff`／`summary.md`／`verify.py`／`report.json`／`test_output.txt` 的 SHA-256、数据集 parquet 哈希、镜像 RepoDigests，以及 swebench 5.0.2、Docker 29.8.0 等环境版本；`MANIFEST_v1.md` 为同内容的人读版。任何依据失败反馈修改补丁的工作都进入 **v2 条件**：新的 `run_id`、新的预测文件、新的补丁目录，v1 的文件与分数不得被覆盖、重算或合并统计。

## 生产模式对比（观察性，非因果）

| 生产模式 | 条数 | 通过 | 未通过 | 通过率 | 其中 Django 条数 | Django 通过率 |
|---|---|---|---|---|---|---|
| 子代理并行 | 12 | 6 | 6 | 50% | 8 | 62% |
| 主会话串行 | 25 | 19 | 6 | 76% | 25 | 76% |
| 全体 Django | 33 | 24 | 9 | 73% | 33 | 73% |

> 两个批次不是随机分组：子代理批次包含全部 4 条非 Django 实例（pylint/pytest），且任务难度未做匹配；因此该表只能作为观察，不能推断“并行 vs 串行”的因果优劣。v2 若要回答这个问题，需要先做任务分配的随机化或配对。

## 逐条对比

| instance_id | summary.md 自报置信度 | 官方实测 | 失败归因 | 失败子模式 | 证据/备注 |
|---|---|---|---|---|---|
| django__django-10914 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-10924 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-11001 | high | 未通过 | 补丁已应用但未满足官方判定 | M2 补丁自带运行时/语法缺陷 | 目标测试仍失败：test_order_by_multiline_sql (expressions.tests.BasicExpressionsTests); test_order_of_operations (expressions.tests.BasicExpressionsTests) |
| django__django-11019 | high | 未通过 | 补丁已应用但未满足官方判定 | M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式） | 目标测试仍失败：test_combine_media (forms_tests.tests.test_media.FormsMediaTestCase); test_construction (forms_tests.tests.test_media.FormsMediaTestCase); test_form_media (forms_tests.tests.test_media.FormsMediaTestCase) |
| django__django-11039 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-11049 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-11099 | high | 通过 | 通过 | — | FAIL_TO_PASS 3/3 通过 |
| django__django-11133 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-11179 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-11283 | medium | 未通过 | 补丁已应用但未满足官方判定 | M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式） | 目标测试仍失败：test_migrate_with_existing_target_permission (auth_tests.test_migrations.ProxyModelWithSameAppLabelTests) |
| django__django-11422 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-11564 | medium | 未通过 | 补丁已应用但未满足官方判定 | M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式） | 目标测试仍失败：test_add_script_name_prefix (settings_tests.tests.MediaURLStaticURLPrefixTest); test_not_prefixed (settings_tests.tests.MediaURLStaticURLPrefixTest) |
| django__django-11583 | high | 通过 | 通过 | — | FAIL_TO_PASS 2/2 通过 |
| django__django-11620 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-11630 | high（文中另提及 medium） | 未通过 | 补丁已应用但未满足官方判定 | M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式） | 目标测试仍失败：test_collision_across_apps_database_routers_installed (check_framework.test_model_checks.DuplicateDBTableTests); test_collision_in_same_app_database_routers_installed (check_framework.test_model_checks.DuplicateDBTableTests) |
| django__django-11742 | medium-high | 通过 | 通过 | — | FAIL_TO_PASS 2/2 通过 |
| django__django-11797 | medium-high | 未通过 | 补丁已应用但未满足官方判定 | M4 修复不完整（目标行为未达成） | 目标测试仍失败：test_exact_query_rhs_with_selected_columns (lookup.tests.LookupTests) |
| django__django-11999 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-12125 | high | 通过 | 通过 | — | FAIL_TO_PASS 2/2 通过 |
| django__django-12184 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-12284 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-12286 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-12308 | high | 未通过 | 补丁已应用但未满足官方判定 | M2 补丁自带运行时/语法缺陷 | 目标测试仍失败：test_json_display_for_field (admin_utils.tests.UtilsTests); test_label_for_field (admin_utils.tests.UtilsTests) |
| django__django-12453 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-12470 | medium-high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-12497 | high | 通过 | 通过 | — | FAIL_TO_PASS 2/2 通过 |
| django__django-12589 | high | 未通过 | 补丁已应用但未满足官方判定 | M3 目标测试通过但引入 PASS_TO_PASS 回归 | 破坏既有测试：test_group_by_exists_annotation (aggregation.tests.AggregateTestCase); test_group_by_subquery_annotation (aggregation.tests.AggregateTestCase) |
| django__django-12700 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-12708 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-12856 | high | 未通过 | 补丁已应用但未满足官方判定 | M2 补丁自带运行时/语法缺陷 | 目标测试仍失败：test_unique_constraint_pointing_to_m2m_field (invalid_models_tests.test_models.ConstraintsTests); test_unique_constraint_pointing_to_missing_field (invalid_models_tests.test_models.ConstraintsTests); test_unique_constraint_pointing_to_non_local_field (invalid_models_tests.test_models.ConstraintsTests) |
| django__django-12915 | high | 通过 | 通过 | — | FAIL_TO_PASS 3/3 通过 |
| django__django-12983 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| django__django-13028 | high | 通过 | 通过 | — | FAIL_TO_PASS 2/2 通过 |
| pylint-dev__pylint-5859 | high | 通过 | 通过 | — | FAIL_TO_PASS 1/1 通过 |
| pylint-dev__pylint-6506 | high | 未通过 | 补丁已应用但未满足官方判定 | M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式） | 目标测试仍失败：tests/config/test_config.py::test_unknown_option_name; tests/config/test_config.py::test_unknown_short_option_name |
| pytest-dev__pytest-5103 | medium-high | 未通过 | 补丁已应用但未满足官方判定 | M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式） | 目标测试仍失败：testing/test_assertrewrite.py::TestAssertionRewrite::test_unroll_expression |
| pytest-dev__pytest-5221 | high | 未通过 | 补丁已应用但未满足官方判定 | M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式） | 目标测试仍失败：testing/python/fixtures.py::TestShowFixtures::test_show_fixtures_verbose |

## 重点标记

### A. 过度自信：自报 high 却未通过（8 条，严格口径）

- **django__django-11001**（M2）：目标测试仍失败：test_order_by_multiline_sql (expressions.tests.BasicExpressionsTests); test_order_of_operations (expressions.tests.BasicExpressionsTests)。自评原文：**High.** The one-line root cause (regex cannot match across newlines, so dedup key degenerates to the last li
- **django__django-11019**（M1）：目标测试仍失败：test_combine_media (forms_tests.tests.test_media.FormsMediaTestCase); test_construction (forms_tests.tests.test_media.FormsMediaTestCase); test_form_media (forms_tests.tests.test_media.FormsMediaTestCase)。自评原文：**High.** The fix makes the spurious warning impossible by construction (warnings now require a real cycle amo
- **django__django-11630**（M1）：目标测试仍失败：test_collision_across_apps_database_routers_installed (check_framework.test_model_checks.DuplicateDBTableTests); test_collision_in_same_app_database_routers_installed (check_framework.test_model_checks.DuplicateDBTableTests)。自评原文：High on mechanism; medium on exact upstream variant (some implementations warn instead of skipping) — hidden t
- **django__django-12308**（M2）：目标测试仍失败：test_json_display_for_field (admin_utils.tests.UtilsTests); test_label_for_field (admin_utils.tests.UtilsTests)。自评原文：High.
- **django__django-12589**（M3）：破坏既有测试：test_group_by_exists_annotation (aggregation.tests.AggregateTestCase); test_group_by_subquery_annotation (aggregation.tests.AggregateTestCase)。自评原文：High — reproduces the ticket's query exactly and the fix restores 2.2 semantics.
- **django__django-12856**（M2）：目标测试仍失败：test_unique_constraint_pointing_to_m2m_field (invalid_models_tests.test_models.ConstraintsTests); test_unique_constraint_pointing_to_missing_field (invalid_models_tests.test_models.ConstraintsTests); test_unique_constraint_pointing_to_non_local_field (invalid_models_tests.test_models.ConstraintsTests)。自评原文：High — all three target scenarios verified end-to-end.
- **pylint-dev__pylint-6506**（M1）：目标测试仍失败：tests/config/test_config.py::test_unknown_option_name; tests/config/test_config.py::test_unknown_short_option_name。自评原文：High. The traceback path is fully traced from raise site (`config_initialization.py:85`) to the uncaught propa
- **pytest-dev__pytest-5221**（M1）：目标测试仍失败：testing/python/fixtures.py::TestShowFixtures::test_show_fixtures_verbose。自评原文：High. The change is minimal (2 lines of behavior), sits on a single obvious code path (`_showfixtures_main`), 

### B. 过度自信：自报 medium-high 却未通过（2 条，宽口径补充）

- **django__django-11797**（M4）：目标测试仍失败：test_exact_query_rhs_with_selected_columns (lookup.tests.LookupTests)。自评原文：Medium-high — mechanism fully traced and verified both directions; hidden test's exact SQL string assertion as
- **pytest-dev__pytest-5103**（M1）：目标测试仍失败：testing/test_assertrewrite.py::TestAssertionRewrite::test_unroll_expression。自评原文：**Medium-high.** The rewrite logic, the generated AST shape, the explanation rendering and all fallback paths 

### C. 保守：自报 medium / medium-high / low 却通过（2 条）

- **django__django-11742**（自报 medium-high）：FAIL_TO_PASS 2/2 通过
- **django__django-12470**（自报 medium-high）：FAIL_TO_PASS 1/1 通过

### D. 失败但置信度归类正确（自报 medium 且未通过）

- **django__django-11283**（M1）：目标测试仍失败：test_migrate_with_existing_target_permission (auth_tests.test_migrations.ProxyModelWithSameAppLabelTests)
- **django__django-11564**（M1）：目标测试仍失败：test_add_script_name_prefix (settings_tests.tests.MediaURLStaticURLPrefixTest); test_not_prefixed (settings_tests.tests.MediaURLStaticURLPrefixTest)

## 基础设施跳过清单

- 无：37 条全部拿到官方判定（镜像拉取失败 0 条，容器/harness 错误 0 条）

## 归因口径

1. **补丁未应用**：`patch_successfully_applied=false`。
2. **补丁已应用但未满足官方判定**（上位分类）：补丁成功应用，但 FAIL_TO_PASS 目标测试仍失败，或 PASS_TO_PASS 出现回归。该分类**只说明官方判定未通过，不预设机理**；机理见 M1–M4 子模式——其中只有 **M1 是“与目标测试的行为契约不匹配”**，M2 是补丁自带的运行时/语法缺陷，M3 是引入回归，M4 是修复不完整。命名同样刻意**不**声称“与上游修复实现不同”：benchmark 的评测 log 能证明目标测试失败，不能证明我们的实现与上游 commit 的逐处差异。
3. **测试环境问题**：镜像拉取失败、容器/harness 错误、超时、实例未跑完。
4. **其他**：补丁已应用但没有可用的测试判定明细。

失败子模式只使用 log 中直接可见的机理（失败测试名、断言文本、异常类型）；未观察到的差异不写进结论。

> 归因依据评测 log 与 per-instance `report.json`。凡引用上游修复代码或 `test_patch` 内容做出的解释，均为事后信息，仅用于理解失败机理，不参与分数与通过判定。
> harness 顶层报告的 `ambiguous_failure_ids` 是对原始输出做正则扫描的启发式（命中 `no tests ran|collected 0 items` 即标记），pytest 自身测试套件会打印内层 pytest 会话输出，因而出现 2 例误标；逐条判定以 per-instance `report.json` 的 `tests_status` 为准。
