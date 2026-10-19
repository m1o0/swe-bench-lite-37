# django__django-11630 — v2 修复(M1:路由器场景应为 W035 警告而非静默跳过)

## 信息条件
使用了 v1 评测反馈:v1 隐藏测试的 AssertionError diff 逐字给出了三个期望断言
(见下方"金标准断言"),来自 v1 评测日志。**未读 test_patch**。

## v1 遗留缺陷
v1 在"路由器已配置 + 跨 app 冲突"时直接 `continue`(静默跳过)——而金标准行为
是降级为 **models.W035 警告**(提示用户验证路由);同 app 冲突 + 路由器的期望
也是 W035 警告(v1 误判为应保持 E028 错误)。

## 金标准断言(从 v1 日志逐字提取)
- 路由器已配置 → Warning(level 30)
  msg="db_table 'X' is used by multiple models: <labels>."
  hint="You have configured settings.DATABASE_ROUTERS. Verify that <labels> are
  correctly routed to separate databases."
  obj='test_table', id='models.W035'
- 无路由器 → Error models.E028(基线行为,不变)

## v2 修复(django/core/checks/model_checks.py, check_all_models)
- `settings.DATABASE_ROUTERS` 已配置 → 任意 db_table 冲突降级为 W035 警告
  (msg 与 hint 按金标准,labels 逗号连接)
- 无路由器 → 维持 E028 错误
- 补 `Warning` 导入

## 验证(WSL 实跑)
- runs_v2\django__django-11630\verify_v2.py:路由器→W035(精确 msg+hint+level 30)✓、
  无路由器→E028 ✓
- 官方 check_framework 全模块:142 tests OK ✓
- 目标:test_collision_across_apps_database_routers_installed、
  test_collision_in_same_app_database_routers_installed

## 信息条件
v1 评测反馈(已登记);test_patch 未读。

## 置信度
High — 断言逐字对齐官方期望。
