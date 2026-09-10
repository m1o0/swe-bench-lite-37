# django__django-11797 — v2 检查单（M4：修复不完整）

> v1 失败证据（事后信息，见 `../../comparison.md`）：F2P 0/1，
> `lookup.tests.LookupTests::test_exact_query_rhs_with_selected_columns`：
> `authors.get()` 返回了错误的行（2 而非 3）——外层 filter 覆盖内查询 GROUP BY 的场景没被完整修好。

## 同族场景清单（逐条标注覆盖状态）

| # | 场景 | 覆盖状态 | 断言方式 |
|---|---|---|---|
| 1 | 外层 `filter(...)` 覆盖内查询已 `values(...)` 的 selected columns | | 取回对象并断言主键/顺序 |
| 2 | 内查询 `values()` 单列 vs 多列 | | |
| 3 | 外层用 `exact` 以外的 lookup（`in`、`gt`、`isnull`） | | |
| 4 | 内查询带 `annotate()` 后再 `values()` | | |
| 5 | 内查询带 `order_by()` 且外层再 filter | | |
| 6 | `distinct()` 参与时 | | |
| 7 | 子查询嵌套两层 | | |

## 必做验证

1. 每条场景给出最小 repro 并断言**具体返回值**（不是"没报错"）。
2. 与 v1 行为对照：同一 repro 在 v1 补丁下的结果（预期不一致）——这是"修复不完整"的直接证据。
3. 回归：`lookup.tests` 模块跑通。
4. 命令与原始输出写入 `verify_output.txt`。

## 已知不确定性

- 第 4–7 条若无法确定期望行为，标注为"未覆盖/无法判断"，不得默认通过。
