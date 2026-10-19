# django__django-11019 — v2 修复(Media 合并改为全列表依赖拓扑合并)

## 信息条件
使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。
v1 日志给出 14 个失败断言的 fnmatch/列表 diff(合并顺序、repr 列表形态、告警
格式);test_patch 给出 test_merge 参数格、three_way 系列、去重、admin 两个
模块的完整期望。

## v1 遗留缺陷
v1 自研 142 行拓扑排序,顺序契约与上游不一致:3+ 对象合并顺序(逐元素不等)、
_js/_css 形态(元组 vs 期望列表)、告警文案(多行元素 vs 列表对)全不匹配。

## v2 实现(django/forms/widgets.py,唯一改动文件,+46/-40)
- `Media.merge(*lists)` 重写为依赖图轮次合并(Kahn 分层):
  * 依赖图 = 每条输入列表中相邻项的前驱边(自边跳过,避免单列表重复元素
    被误判成环);
  * 每轮收集"依赖已全部发出"的项,按首次出现序(全列表按序 chain 去重)
    整批发出——无依赖关系的相邻层交替排列,`merge([1,2],[3,4])→[1,3,2,4]`,
    七列表场景 →[1,5,8,2,6,3,7,9];
  * 无可发出项 = 存在相反顺序环:发出 MediaOrderConflictWarning,消息为
    'Detected duplicate Media files in an opposite order: ' + 各含未发出项的
    输入列表 repr(如 '[1, 2], [2, 1]'),并按首次出现序拼接剩余项返回;
  * 结果天然去重(全元素首次出现序),单列表即自身去重(支持
    test_media_deduplication)。
- `_js` 属性:`merge(*self._js_lists)` 一次合并全部 js 列表(列表形态)。
- `_css` 属性:按 medium 收集各来源 path_list 后逐 medium 一次合并
  (不再是两两递增合并——test_merge_css_three_way 要求三列表同批合并,
  两两合并会造出 [c,a] 与 [a,b,c] 的伪环)。
- `__repr__` 不变(经属性取到列表后自然输出列表形态)。

## 验证(WSL 实跑,见 verify_output.txt)
- test_patch 应用态:forms_tests.tests.test_media + admin_inlines.tests +
  admin_widgets.test_autocomplete_widget **80/80 OK(6 skip 为环境跳过)**,
  含全部隐藏改写测试,零回归。

## 已知不确定性
- 未读上游实现;算法为按 test_patch 全部期望反推的轮次拓扑合并,在官方
  隐藏用例(含 admin 真实媒体列表)上逐项吻合;两用例外的平局次序(如
  同轮无依赖多项的先后)取"全输入按序首次出现"约定,上游若不同仅可能
  影响未被钉死的角落形态。
- 告警消息列出的"冲突列表"集合取"含未发出项的输入列表";对
  merge([1,2],[2,1]) 与官方消息一致,更复杂的部分冲突场景无测试钉死。
