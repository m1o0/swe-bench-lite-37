# django__django-11001 — v2 修复(v1 的 M2 缺陷:get_extra_select 未归一化多行 SQL)

## 信息条件(按 V2_PLAN 要求登记)
本条修复使用了 v1 评测反馈:失败测试名(test_order_by_multiline_sql、
test_order_of_operations)与 `sqlite3.OperationalError: near ")": syntax error`
来自 v1 评测日志;**另读取了该条的 test_patch** 以确定隐藏测试的精确构造
(Company 模型 + `distinct()` 变体)——这是 v2"反馈知情修复"条件的一部分。

## v1 遗留缺陷的真实机理(v2 新发现)
v1 只修了 `get_order_by()` 的去重键(单行化),但隐藏测试还有第二个变体:
`Company.objects.distinct()`。DISTINCT 时 `get_extra_select()` 会把 ORDER BY
表达式复制进 SELECT 列表,它用的是**未归一化**的 `ordering_parts.search(sql)`——
多行 SQL 的 `(.*)\s(ASC|DESC)(.*)` 匹配到最后一行的空 fragment,生成空 SELECT 项,
产生 `SELECT DISTINCT ..., , ...` → `near ")": syntax error`。

## v2 修复(django/db/models/sql/compiler.py)
`get_extra_select()` 应用与 `get_order_by()` 相同的单行化:

```python
sql_oneline = ' '.join(sql.splitlines())
without_ordering = self.ordering_parts.search(sql_oneline).group(1)
```

## 验证(runs/repro11001_v2.py,WSL 真实 sqlite 执行)
- `Company.objects.all().order_by(*raw_order_by)` → 执行成功,顺序
  [Example Inc, Gmbh, Foobar Ltd] ✓(与隐藏测试期望一致)
- `Company.objects.distinct().order_by(*raw_order_by)` → 执行成功,同样顺序 ✓
  (v1 此变体:OperationalError near ")")
- 官方 `expressions` 全模块:126 tests OK ✓

## 信息条件
使用了 v1 评测反馈 + test_patch 阅读(已登记)。
