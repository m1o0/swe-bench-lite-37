# django__django-12856 — v2 门禁单（M2：补丁自带运行时/语法缺陷）

> v1 失败证据（事后信息，见 `../../comparison.md`）：F2P 0/3，
> 且 `test_check_constraints`、`test_check_constraints_required_db_features` 回归，
> 报错为 `TypeError: 'Q' object is not callable`——补丁自身写错了调用。

## 门禁（全部必须通过，输出落盘）

| # | 命令 | 通过标准 |
|---|---|---|
| 1 | `git apply --check patch.diff` | 退出码 0 |
| 2 | `python -m py_compile django/db/models/constraints.py django/db/models/base.py` | 退出码 0 |
| 3 | `python -c "import django.db.models.constraints"` | 退出码 0 |
| 4 | 最小真实 repro | 定义含 `UniqueConstraint` 的模型并调用 `Model.check()`，断言返回 `models.E012` |

## 需要专门覆盖的点

- 三个目标场景：字段**缺失**、指向 **m2m** 字段、指向**非本地**字段；
- 错误 id 与级别（应为 `models.E012`），消息内容；
- 不得把 `Q` 对象当函数调用（v1 的实际缺陷）——检查器实现里每个"可调用"假设都要有依据；
- 回归：`invalid_models_tests.test_models` 中 `ConstraintsTests` 全类跑通（含 `test_check_constraints*`）。

## 落盘

- `verify_output.txt`：命令 + 原始输出。
- `summary.md`：列出三个场景各自的断言结果，以及回归用例的 before/after。
