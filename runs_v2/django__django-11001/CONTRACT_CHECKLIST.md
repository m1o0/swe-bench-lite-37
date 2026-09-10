# django__django-11001 — v2 门禁单（M2：补丁自带运行时/语法缺陷）

> v1 失败证据（事后信息，见 `../../comparison.md`）：F2P 0/2，
> 运行期出现 `sqlite3.OperationalError: near ")": syntax error`——补丁生成的 SQL 非法。

## 门禁（全部必须通过，输出落盘）

| # | 命令 | 通过标准 |
|---|---|---|
| 1 | `git apply --check patch.diff` | 无输出、退出码 0 |
| 2 | `python -m py_compile <改动文件…>` | 退出码 0 |
| 3 | `python -c "import django.db.models.sql.compiler"`（或实际扰动模块） | 退出码 0 |
| 4 | 最小真实 repro | 真的连 SQLite 执行一次带**多行** `RawSQL` 的 `order_by`，断言 SQL 可执行 |

## 需要专门覆盖的点

- 多行 SQL（含换行）作为 `RawSQL` 传入 `order_by` 时的 GROUP BY 去重；
- 去重不得丢列：断言最终 SQL 里 GROUP BY 列表与预期一致；
- 单行 SQL 的既有行为不得改变（回归）；
- 目标模块公开测试：`expressions.tests.BasicExpressionsTests` 跑通。

## 落盘

- `verify_output.txt`：上述命令 + 原始输出（含失败时的完整 traceback）。
- `summary.md`：明确写出"已实际执行 SQL"而不是"仅导入模块"。
