# django__django-12589 — v2 门禁单（M3：目标通过但引入回归）

> v1 失败证据（事后信息，见 `../../comparison.md`）：
> 目标用例（F2P）**已通过**，但 `aggregation.tests.AggregateTestCase` 的两个既有用例回归：
> `test_group_by_exists_annotation`、`test_group_by_subquery_annotation`。
> 结论：v1 的修复过宽，改变了其他 GROUP BY 场景的行为。

## 门禁（全部必须通过，输出落盘）

| # | 命令 | 通过标准 |
|---|---|---|
| 1 | `git apply --check patch.diff` | 退出码 0 |
| 2 | `python -m py_compile <改动文件…>` | 退出码 0 |
| 3 | 最小真实 repro（ticket 查询） | 目标行为成立 |
| 4 | **受影响模块公开测试** | `aggregation` 模块全绿，且给出 before/after 计数 |

## 需要专门覆盖的点

- 修复的**触发条件**必须收窄：只有 ticket 描述的那种"子查询注解 + GROUP BY 歧义列"才改写；
- 显式列出不该被影响的场景并逐个断言：
  - `Exists` 注解 + GROUP BY；
  - 子查询注解 + 其他 lookup；
  - 多列 GROUP BY；
  - 无注解的普通聚合。
- 对每个场景给出 ①v1 行为 ②v2 行为 ③期望行为 三列对照（写进 `summary.md`）。

## 落盘

- `verify_output.txt`：目标 repro + `aggregation` 模块测试的原始输出（含计数行）。
- `summary.md`：before/after 计数 + "为什么这次不会影响其他场景"的机制说明。
