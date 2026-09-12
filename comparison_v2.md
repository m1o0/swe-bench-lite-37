# v2（评测后修复条件）结果表 — run_id `tonight-v2d`

生成时间：`2026-09-12T23:11:05+0800`

> **与 v1 的边界（不可协商）**：v1（`run_id=tonight`，盲写条件，25/37 = 67.6%）已冻结，唯一真源是 `comparison.md`。本文件的 v2 分数是**另一个条件**下的结果：其补丁可以使用 v1 的失败反馈。两套数字**必须分列报告，禁止合并统计**。

## v2 总览

| 指标 | 数值 |
|---|---|
| v2 条目 | 12 |
| 已跑（拿到判定） | 12 |
| v2 通过 | 12 |
| v1→v2 转绿 | 12 |
| v1→v2 仍红 | 0 |
| v1→v2 新回归 | 0 |
| 补丁与 v1 相同（未真正修复，不计入修复率分母） | 0 |

## 逐条转移表

| instance_id | v1（冻结） | v2 | 转移 | v2 自报置信度 | 信息条件 | 补丁状态 | v2 证据 |
|---|---|---|---|---|---|---|---|
| django__django-11001 | 未通过 | 通过 | 转绿 | 未标注 | 本条修复使用了 v1 评测反馈:失败测试名(test_order_by_multiline_sql、 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| django__django-11019 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| django__django-11283 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈(隐藏测试 test_migrate_with_existing_target_permission 的 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| django__django-11564 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| django__django-11630 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈:v1 隐藏测试的 AssertionError diff 逐字给出了三个期望断言 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| django__django-11797 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| django__django-12308 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈(失败测试名与 subTest 崩溃用例)+ **读取了该条的 test_patch** | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| django__django-12589 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈(两个回归测试名)+ **上游 PR | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| django__django-12856 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| pylint-dev__pylint-6506 | 未通过 | 通过 | 转绿 | 未标注 | - v2 首轮:使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**。 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| pytest-dev__pytest-5103 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。 | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |
| pytest-dev__pytest-5221 | 未通过 | 通过 | 转绿 | 未标注 | 使用了 v1 评测反馈:v1 隐藏测试 `test_show_fixtures_verbose` 的 fnmatch 断言 diff | 已修改 | FAIL_TO_PASS 全绿、PASS_TO_PASS 无回归 |

## v2 置信度分档读数（描述性，不做统计推断）

| 自报置信度 | 条数 | 通过 | 该档通过率 |
|---|---|---|---|
| 未标注 | 12 | 12 | 100% |

## 需要一起报告的三件事

1. **v1 与 v2 是不同条件**：v1 盲写、v2 见失败反馈；把两者相加得到的“总通过率”没有意义。
2. **修复率的分母**：只算真正改过的补丁（上表“补丁状态=已修改”）；与 v1 完全相同却计入修复率会高估。
3. **新回归要单独列**：v2 修好一条却弄坏另一条，与“没修好”是不同性质的失败。

## 尚未创建的 v2 目录

- 无
