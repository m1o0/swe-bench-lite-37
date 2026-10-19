# django__django-12856 — v2 修复(v1 的 E012/E013/E016 三个 id 与消息全错)

## 信息条件
使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。
v1 日志的 AssertionError diff 给出了三条的金标准断言(id 与消息逐字)。

## v1 遗留缺陷
v1 的检查自己发明了 id 与措辞:三条全用 models.E012、消息写 "'fields' must not
contain..."——与官方检查的约定完全不符。

## 金标准断言(从 v1 日志 AssertionError diff 逐字提取)
1. 缺失字段 → `models.E012`
   "'constraints' refers to the nonexistent field 'missing_field'."
2. 非本地字段(MTI 继承)→ `models.E016`
   "'constraints' refers to field 'field1' which is not local to model 'Child'."
   hint="This issue may be caused by multi-table inheritance."
3. m2m 字段 → `models.E013`
   "'constraints' refers to a ManyToManyField 'm2m'..."(尾部未逐字确认,断言只校验前缀)

## v2 实现(django/db/models/constraints.py, _check_fields 重写)
- `get_field` 解析失败 → E012(nonexistent)
- 解析到但 many_to_many → E013
- 解析到、非 m2m、但不在 local_fields/attname 里(MTI)→ E016 + MTI hint
- base.py 的 `constraint.check(cls)` 调用改为 callable-on-type 守卫
  (CheckConstraint 的 `.check` 是 Q 实例属性,v1 曾把它当方法调用 → TypeError)

## 验证(WSL 实跑)
- runs_v2\django__django-12856\verify_v2.py:三场景金标准断言 ALL_OK
- 官方 invalid_models_tests.test_models:79/79 OK(含 test_check_constraints 回归修复)

## 信息条件
v1 评测反馈 + test_patch 阅读(已登记)。
