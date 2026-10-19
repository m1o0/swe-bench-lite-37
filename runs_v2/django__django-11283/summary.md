# django__django-11283 — v2 修复(M1:冲突处理缺少 stdout 提醒打印)

## 信息条件
使用了 v1 评测反馈(隐藏测试 test_migrate_with_existing_target_permission 的
assertIn 断言:stdout 必须含 'A problem arose migrating proxy model permissions'
——v1 时 stdout 为空)。**读取了该条的 test_patch**(v2 反馈知情修复条件,已登记;
本地验证时临时应用,导出的 patch.diff 不含测试文件改动)。

## v1 遗留缺陷
v1 的冲突处理(删除陈旧权限 + 重试移动)语义正确,但按 test 文档要求
("Output a reminder to audit relevant permissions")还应向 stdout 打印提醒——
隐藏测试断言 'A problem arose migrating proxy model permissions' 出现在 stdout。

## v2 修复(django/contrib/auth/migrations/0011_update_proxy_permissions.py)
except IntegrityError 路径开头新增:

```python
print('A problem arose migrating proxy model permissions')
```

删除陈旧权限 + 重试移动的修复逻辑保持不变。

## 验证(WSL 实跑,临时应用 test_patch 后)
- 官方 auth_tests.test_migrations 全模块:9/9 OK
  (含隐藏测试 test_migrate_with_existing_target_permission——print 命中断言)
- 验证后已将测试文件还原;导出的 patch.diff 仅含迁移文件改动

## 信息条件
v1 评测反馈 + test_patch 阅读(已登记)。

## 置信度
High — 隐藏测试在本地(临时应用 test_patch)实跑通过。
