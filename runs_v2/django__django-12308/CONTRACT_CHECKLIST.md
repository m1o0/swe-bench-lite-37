# django__django-12308 — v2 门禁单（M2：补丁自带运行时/语法缺陷）

> v1 失败证据（事后信息，见 `../../comparison.md`）：F2P 0/2，
> `admin_utils.tests.UtilsTests` 两个用例报 `TypeError: keys must be a string`
> （只读 JSONField 显示路径把非字符串键交给 JSON 序列化）。

## 门禁（全部必须通过，输出落盘）

| # | 命令 | 通过标准 |
|---|---|---|
| 1 | `git apply --check patch.diff` | 退出码 0 |
| 2 | `python -m py_compile django/contrib/admin/utils.py`（或实际改动文件） | 退出码 0 |
| 3 | `python -c "import django.contrib.admin.utils"` | 退出码 0 |
| 4 | 最小真实 repro | 构造带**非字符串键**（如整数键）的 `JSONField` 值，调用 `display_for_field`，断言输出为合法 JSON |

## 需要专门覆盖的点

- `display_for_field` 的**所有**分支（不只 JSONField）：空值、普通字段、choices、关系字段；
- `prepare_value` 返回值的类型契约（必须可直接 `json.dumps`）；
- 非字符串键的两种处理：转成字符串键 vs 保持结构；
- 回归：`admin_utils.tests` 模块跑通。

## 落盘

- `verify_output.txt`：命令 + 原始输出。
- `summary.md`：写清"实际调用了 `display_for_field` 并断言返回值"，而非只导入模块。
