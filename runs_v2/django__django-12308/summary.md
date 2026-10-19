# django__django-12308 — v2b 精修(v1 的 M2 缺陷:元组键字典序列化崩溃)

## 信息条件
使用了 v1 评测反馈(失败测试名与 subTest 崩溃用例)+ **读取了该条的 test_patch**
断言(v2"反馈知情修复"条件,已登记)。

## v1 遗留缺陷
`prepare_value` 直接 `json.dumps(value)`:元组键字典 `{('a', 'b'): 'c'}` 使
json.dumps 抛 `TypeError: keys must be a string`,只读 admin 渲染崩溃。

## v2b 修复(最终形态,django/db/models/fields/json.py + django/contrib/admin/utils.py)
- `JSONField.prepare_value`:保持简单 `json.dumps(value, cls=self.encoder)`
  (可序列化输入不动;不可序列化时抛 TypeError 是明确契约)。
- `display_for_field`:JSONField 分支包 try/except TypeError,失败时回退
  `display_for_value`(Python repr)——与 test_patch 的期望逐字一致:
  `{('a', 'b'): 'c'}` → `"{('a', 'b'): 'c'}"`(注释标注 Invalid JSON)。

(v2 第一轮曾尝试"递归字符串化键",方向与金标准相反,已废弃。)

## 验证(WSL 实跑)
- runs_v2\django__django-12308\verify_v2.py:test_patch 的 4 组断言 + None 场景,
  ALL_OK(含元组键字典的 repr 回退精确匹配)
- 官方 admin_utils.tests:34/34 OK

## 信息条件
v1 评测反馈 + test_patch 阅读(已登记)。
