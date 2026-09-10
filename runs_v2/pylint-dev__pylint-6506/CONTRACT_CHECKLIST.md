# pylint-dev__pylint-6506 — 输出契约检查表（M1：层级 + 文案 + 退出码）

> v1 失败证据（事后信息，见 `../../comparison.md`）：F2P 0/2，
> 目标断言要求输出 `E0015: Unrecognized option found: <opt>` 且 `usage: pylint` 出现在 stderr；
> v1 让 argparse 抢先报 `unrecognized arguments: unknown-option=yes`，修复落在了错误的抽象层。
> 填写纪律：不读 `test_patch`。

## 必须确定的层级与格式契约

| 项 | 问题 | 依据来源 | 结论 |
|---|---|---|---|
| 报错层级 | 未知选项应由 **pylint 自己的检查器**（E0015）报出，而不是 argparse？ | ticket、`config_initialization.py` 既有选项校验、既有 E0015 定义 | |
| 文案格式 | `E0015: Unrecognized option found: <option>` 的确切写法 | 仓库内 E0015 的既有消息与既有测试 | |
| 长/短选项 | `--unknown-option=yes` 与 `-Q` 两种形式的消息差异 | ticket 复现步骤 | |
| 输出通道 | 消息进 stdout 还是 stderr？`usage: pylint` 出现在哪里？ | 既有配置错误用例 | |
| 退出码 | 该错误对应的退出码（用法错误 vs lint 错误） | 既有 CLI 行为 | |
| 是否继续运行 | 报错后是否终止、是否进入 lint 流程 | 既有行为 | |

## 必做验证

1. 断言**逐字**消息（含 `E0015:` 前缀）与出现通道。
2. 断言 `usage: pylint` 出现在 stderr。
3. 断言退出码。
4. 反例：合法选项不得触发 E0015。
5. 回归：`tests/config/` 与 `tests/test_self.py` 中与选项相关的公开测试跑通。
6. 命令与原始输出写入 `verify_output.txt`。

## 已知不确定性

- 长短选项消息是否共用同一模板，若无仓库证据必须标注。
