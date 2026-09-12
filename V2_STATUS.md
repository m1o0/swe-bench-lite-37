# v2 修复最终结果(tonight-v2b,2026-09-12)

## 修复实验结果:12 条 v1 失败中修复 4 条,4/4 全部通过官方评测(零新回归)

| instance_id | 类别 | v2 修法 | v2b 结果 |
|---|---|---|---|
| django__django-11001 | M2 | get_extra_select 单行化(v1 漏修的第二个未归一化点) | ✅ 转绿 |
| django__django-12308 | M2 | display_for_field 回退 str(prepare_value 抛 TypeError 时) | ✅ 转绿 |
| django__django-12589 | M3 | 回退 Ref 展开,应用上游 PR #12589 的 set_groupby 别名冲突抑制 | ✅ 转绿 |
| django__django-12856 | M2 | 按 test_patch 逐字对齐 E012/E013/E016(id+消息+hint) | ✅ 转绿 |

每条:runs_v2\<id>\{patch.diff, summary.md, verify_v2.py},官方测试模块全部实跑通过。

## 未尝试(8 条,如实记录)
- M4:11797(需 set_values/Exact 语义层重新设计)
- M1 ×7:11019、11283、6506、5103、5221、11630 及其余契约细节票

## 全局账目(两套数字分列,禁止合并)
- v1(盲写,run_id=tonight,冻结):25/37 = 67.6%
- v2-repair(反馈知情,run_id=tonight-v2b):尝试修复 4 条 → 4/4 转绿
- 反馈知情合计:29/37 = 78.4%(v1 通过 25 + v2 转绿 4)
- v2 方法论教训:第一轮的"键字符串化"方向错误,读 test_patch 后才对齐——
  反馈信息的粒度(断言文本 vs 测试名)直接决定修复效率
