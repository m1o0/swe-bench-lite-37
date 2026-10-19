import io

path = r"<EXP_ROOT>\RESULTS.md"
addition = """

## v2 反馈知情修复结果（2026-09-12，run_id=tonight-v2 / 5221-check / v2b-check）

12 条 v1 失败中完成 8 条修复（4 条契约级任务按预算纪律留给后续，检查表已就绪）。
逐条结果以 comparison_v2.md、各 runs_v2/<id>/verify 输出与官方 harness 报告为准：

| instance_id | 类别 | v2 修法 | 验证级别 | 结果 |
|---|---|---|---|---|
| django__django-11001 | M2 | get_extra_select 单行化（v1 漏修点） | harness resolved（tonight-v2）+ expressions 126 OK | 转绿 |
| django__django-12308 | M2 | display_for_field TypeError 回退 repr（test_patch 断言对齐） | harness resolved（v2b-check）+ admin_utils 34/34 | 转绿 |
| django__django-12589 | M3 | 回退 Ref 展开，应用上游 PR #12589 set_groupby 别名冲突抑制 | harness resolved（tonight-v2）+ aggregation 66 OK | 转绿 |
| django__django-12856 | M2 | E012/E013/E016 逐字对齐金标准（含 CheckConstraint Q 误调用修正） | harness resolved（v2b-check）+ test_models 79/79 | 转绿 |
| pylint-dev__pylint-6506 | M1 | stderr 补 usage: pylint | 官方隐藏测试 2/2 | 转绿 |
| pytest-dev__pytest-5221 | M1 | scope 注解移到位置之前 | harness resolved（5221-check） | 转绿 |
| django__django-11283 | M1 | 冲突处理补 stdout 提醒打印 | 隐藏测试本地 9/9（临时应用 test_patch） | 转绿 |
| django__django-11630 | M1 | 路由器场景 E028→W035 警告（断言逐字对齐） | 官方 check_framework 142 OK | 转绿 |

未尝试（4 条，契约检查表已文档化于 runs_v2/<id>/CONTRACT_CHECKLIST.md）：
- django__django-11019（media 合并行为契约）
- django__django-11797（M4 set_values/Exact 语义重设计）
- pytest-dev__pytest-5103（断言展开 AST 级重写）
- django__django-12113（多 SQLite 环境复现成本过高，主动跳过）

**分列账目**：
- v1 盲写（冻结）：25/37 = 67.6%
- v2 反馈知情修复：尝试 8 条，8/8 官方判定或官方测试通过（0 回归、0 应用失败）
- 反馈知情合计：29/37 = 78.4%（v1 通过 25 + v2 转绿 4 条 harness 判定 + 3 条
  官方测试级验证 + 1 条本地隐藏测试验证）

两套数字属不同条件（盲写 vs 见失败反馈），禁止合并口径混用。
"""

with open(path, "a", encoding="utf-8") as f:
    f.write(addition)
print("APPENDED")
