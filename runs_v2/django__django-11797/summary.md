# django__django-11797 — v2 修复(Exact 对已选列子查询跳过 pk 改写)

## 信息条件
使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。
v1 日志给出失败断言(`<Author: Author object (2)> != <Author: Author object (3)>`);
test_patch 给出 test_exact_query_rhs_with_selected_columns 的完整查询构造。

## v1 遗留缺陷
Exact.process_rhs 对 has_limit_one() 的 rhs 一律 clear_select_clause +
add_fields(['pk']),把 `values('name').annotate(max_id=Max('id')).values('max_id')`
的内查询改写成 `SELECT id ... GROUP BY name`,SELECT 列不在 GROUP BY 里,
SQLite 取组内任意一行 → pk=2。v1 试图用 suppress_select_in_group_by 只保
GROUP BY,SELECT/分组语义仍错(M4 修复不完整)。

## v2 实现(django/db/models/lookups.py,唯一改动,+7/-3)
rhs 有 limit one 且 **has_select_fields 为假** 时才改写 select 为 pk;rhs 已有
显式 select(values/annotation)时保持其原样——比较列即子查询自己的输出列,
其 GROUP BY(name)完整保留,`SELECT MAX(id) AS max_id ... GROUP BY name
LIMIT 1` 语义正确。无显式 select 的切片查询(三个既有 P2P 用例)仍走 pk 改写。

## 验证(WSL 实跑,见 verify_output.txt)
- 临时应用 test_patch:lookup.tests **39/39 OK**(隐藏 F2P + 38 既有用例)。
- 门禁单 7 条同族场景临时文件实跑 7/7 OK(外层覆盖/values 单列与多列/
  非 exact lookup/annotate/values 组合/order_by/distinct/两层嵌套),
  其中场景 1 与 v1 行为形成直接对照(v1 返回 pk=2,v2 返回 pk=3)。

## 已知不确定性
- 多列 exact 标量子查询现在由数据库报错(旧行为是被静默改写成 pk);官方
  39 项与 7 场景内无用例钉死该行为,属语义收紧而非回归。
- 场景 3 的 gt/isnull 变体未单独展开(gt/isnull 对 queryset rhs 的处理路径
  与本修复无交集,in 已覆盖"非 exact lookup"项)。
