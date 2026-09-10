# pytest-dev__pytest-5221 — 输出契约检查表（M1：CLI 展示格式）

> v1 失败证据（事后信息，见 `../../comparison.md`）：F2P 1/2，
> `TestShowFixtures::test_show_fixtures_verbose` 未通过（`--fixtures -v` 的 scope 展示细节未对齐）。
> 填写纪律：不读 `test_patch`。

## 必须确定的展示契约

| 项 | 问题 | 依据来源 | 结论 |
|---|---|---|---|
| scope 标注位置 | scope 写在 fixture 名后、类型前，还是单独一行？ | ticket / 既有 `--fixtures` 输出测试 | |
| 取值写法 | `session`、`function`、`class`、`module`、`package` 的确切字符串 | 既有输出格式 | |
| 排序 | fixture 按名称、按 scope，还是按定义顺序？ | 既有测试 | |
| 分组 | 按 scope 分组时，组间空行与标题格式 | 既有测试 | |
| 对齐与缩进 | 名称与说明之间的空白宽度 | 既有测试 | |
| 非 verbose 路径 | 不加 `-v` 时不得改变输出 | 既有测试 | |

## 必做验证

1. 用 `pytester`（`testdir`）运行带 fixture 的临时用例，对 `--fixtures -v` 的完整输出做
   **模式匹配**（含 scope 关键字与顺序）。
2. 同一用例跑非 `-v` 版本，断言输出未变化。
3. 回归：`testing/python/fixtures.py` 模块跑通。
4. 命令与原始输出写入 `verify_output.txt`。

## 已知不确定性

- 对齐宽度等细节若无法从仓库证据推出，列入不确定性（v1 正是在这类细节上失败）。
