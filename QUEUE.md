# SWE-bench 冲刺任务队列
# 规则:做之前把 pending 改成 running(带上你的窗口名),完成后改成 done
# 补丁必须落到 <EXP_ROOT>\runs\<instance_id>\patch.diff
# 工作树:pylint/pytest/django 仓库在 D:\mio\repos\<name>,用 git worktree add 建到 D:\mio\worktrees\<instance_id>

## running
- [running|主窗口A] pylint-dev__pylint-6506
- [running|主窗口A] pytest-dev__pytest-5103

## pending(优先小仓库)
- [pending] pylint-dev__pylint-5859
- [pending] pytest-dev__pytest-5221
- [pending] pytest-dev__pytest-5227
- [pending] pytest-dev__pytest-5413
- [pending] pytest-dev__pytest-5495
- [pending] pytest-dev__pytest-5692
- [pending] pytest-dev__pytest-6116
- [pending] pytest-dev__pytest-7168
- [pending] pytest-dev__pytest-7220
- [pending] pytest-dev__pytest-7373
- [pending] pytest-dev__pytest-7432
- [pending] pytest-dev__pytest-7490
- [pending] pytest-dev__pytest-8365
- [pending] pytest-dev__pytest-8906
- [pending] pytest-dev__pytest-9359
- [pending] pytest-dev__pytest-11143
- [pending] pytest-dev__pytest-11148
- [pending] pylint-dev__pylint-7080
- [pending] pylint-dev__pylint-7114
- [pending] pylint-dev__pylint-7228
- [pending] pylint-dev__pylint-7993
- (django/sympy 的任务卡还没导出,克隆完成后批量生成)

## done
