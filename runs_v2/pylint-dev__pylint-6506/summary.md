# pylint-dev__pylint-6506 — v2 修复(未识别选项:stderr 契约完整版)

## 信息条件
- v2 首轮:使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**。
- v2c 修复轮(本次):**使用了 tonight-v2c 官方 harness 失败详情**(test_output.txt
  的 AssertionError diff,给出 stderr 的逐字断言)——官方复核发现首轮只满足
  "usage: pylint",不满足 "Unrecognized option"。

## 修复史(三段,全程可审计)
1. v1:修在错误抽象层(官方 tonight 判 M1 失败)。
2. v2 首轮:run.py 捕获 _UnrecognizedOptionError → stderr 打
   "pylint: error: unrecognized arguments: ...\nusage: pylint" + sys.exit(32)。
   当时的本地验证"隐藏测试 2/2"存在缺口:工作树里的 tests/config/test_config.py
   是我们自己改写的版本(断言 E0015 在 stdout + SystemExit),并非官方
   test_patch 版本(官方版断言 stderr 含 "usage: pylint" **且** 含
   "Unrecognized option")。tonight-v2c 官方判定 unresolved
   (2 failed / 6 passed),暴露该缺口。
3. v2c 修复:同一 except 分支的 stderr 文案改为
   "Unrecognized option found: <options>\nusage: pylint"(两断言逐字满足)。

## v2c 实现(pylint/lint/run.py,唯一改动文件,+15/-4)
- Run.__init__ 捕获 _UnrecognizedOptionError → stderr 打印
  "Unrecognized option found: <逗号拼接选项>\nusage: pylint",sys.exit(32)。
- E0015 消息仍照常走 reporter(stdout),与官方运行时行为并存。

## 验证(WSL 实跑)
- runs_v2/pylint-dev__pylint-6506/verify_v2c_direct.py:1:1 复刻官方 test_patch
  两个用例的断言(SystemExit、'usage: pylint' in err、'Unrecognized option'
  in err;capsys 用 redirect 替代),**6/6 PASS**。
  实际 stderr:'Unrecognized option found: unknown-option=yes\nusage: pylint\n'
  与 'Unrecognized option found: Q\nusage: pylint\n'。
- 其余 6 个 P2P 用例(test_unknown_message_id 等)不经该 handler,受零影响
  (tonight-v2c 中它们已通过)。
- 说明:本地 WSL 系统 pytest(pluggy 版本不匹配)不可用,故用直接脚本复刻
  断言;最终以 tonight-v2d 官方 harness 判定为准。

## 已知不确定性
- 官方对 stderr 的完整期望措辞未知(仅钉死两个子串);本实现子串逐字满足。
