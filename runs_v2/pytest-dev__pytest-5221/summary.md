# pytest-dev__pytest-5221 — v2 修复(M1:scope 标注位置错误)

## 信息条件
使用了 v1 评测反馈:v1 隐藏测试 `test_show_fixtures_verbose` 的 fnmatch 断言 diff
显示期望模式为 `tmpdir_factory [[]session scope[]] -- *tmpdir.py*`(scope 在
fixture 名与位置**之间**)。**未读 test_patch**(新测试
test_show_fixtures_verbose_include_scope 在 v1 已通过)。

## v1 遗留缺陷
v1 把 `[<scope> scope]` 追加在 `funcargspec` 的**末尾**:
verbose 输出变成 `tmpdir_factory -- /path [session scope]`(scope 在位置之后),
而官方契约要求 `tmpdir_factory [session scope] -- /path`。

## v2 修复(src/_pytest/python.py, _showfixtures_main)
verbose 分支:scope 注解移到位置之前;非 verbose 分支保持 v1 行为
(仅追加 `[scope]`,与 test_show_fixtures_verbose_include_scope 的非 verbose
断言一致——该测试 v1 已通过):

```python
if verbose > 0:
    if fixturedef.scope != "function":
        funcargspec = "%s [%s scope] -- %s" % (argname, fixturedef.scope, bestrel)
    else:
        funcargspec = "%s -- %s" % (argname, bestrel)
else:
    if fixturedef.scope != "function":
        funcargspec = "%s [%s scope]" % (argname, fixturedef.scope)
    else:
        funcargspec = argname
```

## 验证
官方 swebench 评测容器对 5221 单条实跑(pred_5221_v2.jsonl,run_id=5221-check):
结果见本目录 verify_output / 评测报告。工作树自带 pytest 4.4.dev 的本地自测
因 setuptools_scm 版本解析(tox.ini minversion 检查)未能在 WSL 直跑,
故采用容器实跑为准。

## 信息条件
v1 评测反馈(已登记);test_patch 未读。

## 置信度
High。
