# django__django-12589 — v2 修复(M3:改用上游 set_groupby 别名冲突抑制,回退 v1 的 Ref 展开)

## 信息条件
使用了 v1 评测反馈(两个回归测试名)+ **上游 PR #12589 的合并 diff**
(github.com/django/django/pull/12589,经 WebFetch 获取)——v2"反馈知情修复"条件。

## v1 失败机理(v2 复盘)
v1 在 compiler/expressions 里把 GROUP BY 元组中的 `Ref(status, Subquery)` 无条件
展开为完整子查询表达式——修复了 ticket 的歧义场景,但破坏了两个
PASS_TO_PASS 回归(test_group_by_exists/subquery_annotation):
对这些场景,按完整表达式分组与按别名分组语义不同,导致分组计数塌缩
({None: 1, 1: 4} 变 {None: 1, 1: 1})。

## v2 修复(= 上游 PR #12589 的真实修法,django/db/models/sql/query.py set_groupby)
1. 回退 v1 对 compiler.py 与 expressions.py 的全部改动(git checkout)。
2. `set_groupby()` 增加别名冲突抑制:收集 JOIN 表(跳过基表)的本地具体列名,
   注解别名撞上任何 JOIN 表列名时 `alias = None`,GROUP BY 退回无歧义的列表达式。

ticket 场景(status 撞 repro_ab.status / repro_c.status)→ GROUP BY repro_a.id,
歧义消除;无冲突场景 → 别名分组保持不变(回归消除)。

## 验证(WSL 实跑)
- runs_v2\django__django-12589\driver_v2.py:GROUP BY "repro_a"."id"、无裸
  "status" 引用 → ALL_OK
- 官方 aggregation.tests:66 tests OK(两个 v1 回归测试全过)

## 信息条件
v1 评测反馈 + 上游 PR diff(已登记)。
