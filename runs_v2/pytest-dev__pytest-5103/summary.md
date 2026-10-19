# pytest-dev__pytest-5103 — v2 修复(assert all 真展开为逐元素断言)

## 信息条件
使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。
v1 日志给出期望消息特征("0 == 1" 缺失、三个 unroll 测试 FAILED);
test_patch 给出 test_unroll_expression/test_unroll_generator/
test_unroll_list_comprehension/test_for_loop 四个用例的确切输出契约。

## v1 遗留缺陷
v1 没有改写展开结构,只给 all() 调用解释加了"where falsy items: [0, 2, ...]"
元素值列表——隐藏测试要求的是逐元素比较解释("0 == 1")与调用解释
("where False = check_even(1)")。

## v2 实现(src/_pytest/assertion/rewrite.py,唯一语义文件,+60 行)
- 新增 AssertionRewriter._try_unroll_all 并在 visit_Assert 顶部接入:
  `assert all(<genexp|listcomp>)`(单生成器、无 if、目标为简单 Name、元素
  表达式不含 Lambda/嵌套推导式)改写为
  `for <唯一临时名> in <iter>: assert <elt>`;内层 assert 走既有重写机制,
  失败时自然产出 "assert 0 == 1" / "assert False + where False = check_even(1)"。
  - 循环目标改名为 @py_unrollN,避免推导式目标泄漏进外层作用域;
  - all 的短路语义保持:首个 False 元素即抛出,后续元素不再求值;
  - 不匹配形态(带 if/多生成器/带 msg 的 assert/非 all 调用)完全回退原路径。
- 另含 run() 中 ast.alias 位置信息修补(跨版本无害,py3.10 本地验证使能;
  py3.6/harness 上为惰性属性,详见 verify_output.txt)。

## 验证(WSL 实跑,见 verify_output.txt)
- test_patch 应用态:testing/test_assertrewrite.py 全模块 **67 passed /
  5 skipped / 0 failed**(3 个 F2P 隐藏测试 + test_for_loop 全部转绿,零回归;
  v1 官方日志中前 3 项为 FAILED)。
- 门禁单直接验证 7/7:逐元素比较消息、调用解释消息、副作用单次、短路、
  变量不泄漏、listcomp 同型、不可展开形态回退。

## 已知不确定性
- `any()` 未做对称展开(隐藏测试未覆盖,保持原行为;若官方 test_patch 之外
  存在 any 展开断言会失败——已核对本条 test_patch 全文,无此内容)。
- 展开后失败点行号统一取原 assert 行(与既有重写机制一致)。
- 本地验证跑在 py3.10(需 alias 修补 + 插件屏蔽),官方 harness 为镜像内
  Python;alias 修补在旧解释器上无行为差异。
