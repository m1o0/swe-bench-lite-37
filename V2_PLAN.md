# V2 PLAN：失败反馈条件下的补丁修复与验证协议升级

> **版本纪律（最重要）**：v1（`run_id=tonight`，盲写条件，25/37 = 67.6%，已冻结）不得被覆盖、
> 重算或与 v2 合并统计。v2 的定位是**评测后修复条件**（post-evaluation repair），
> 它回答的是另一个问题：「看到失败反馈后，修复能到什么程度」。
> v1 与 v2 的对比本身就是研究数据：它量化了「失败反馈」这一信息通道的价值。

## 0. v2 的命名与目录约定

| 项 | v1（冻结） | v2（新建） |
|---|---|---|
| run_id | `tonight` | `tonight-v2`（第二迭代可 `tonight-v2b`，逐轮递增） |
| 补丁目录 | `runs/<id>/patch.diff` | `runs_v2/<id>/patch.diff`（**新目录，不覆盖 v1**） |
| 预测文件 | `predictions_swebench.jsonl` | `predictions_v2.jsonl` |
| 结果表 | `comparison.md` | `comparison_v2.md` |
| harness 产物 | `logs/run_evaluation/tonight/` | `logs/run_evaluation/tonight-v2/` |
| 汇总报告 | `glm-5.3-zcode-campaign.tonight.json` | `glm-5.3-zcode-campaign.tonight-v2.json` |
| 每条 summary | `runs/<id>/summary.md` | `runs_v2/<id>/summary.md`，**必须新增** `信息条件` 字段：本条的修复是否使用了 v1 评测反馈、用了哪一部分 |

**只在 12 条失败上做 v2，还是全 37 条？** 建议两种都做但分开报告：
`v2-repair`（只碰 12 条失败，测“反馈→修复”的增益）与 `v2-blind-repeat`（全 37 条重跑，
测“同一条件下的方差”，即 v1 的分数有多少是运气）。后者对研究价值更大，因为它给出噪声地板。

### 0.1 已就绪的脚手架（2026-09-10 落盘，尚未运行）

| 用途 | 文件 |
|---|---|
| 工作区规则 + 最小完成契约 | `runs_v2/README.md` |
| 契约检查表模板 | `runs_v2/CHECKLIST_TEMPLATE.md` |
| 12 条失败的逐条检查表/门禁单 | `runs_v2/<instance_id>/CONTRACT_CHECKLIST.md` |
| 生成 v2 预测 + 补丁改动审计 | `make_predictions_v2.py` → `predictions_v2.jsonl`、`v2_patch_status.md` |
| v2 评测入口（WSL） | `run_eval_v2.sh`（默认 `-id tonight-v2`） |
| v2 结果表 | `analyze_v2.py` → `comparison_v2.md`（当前为未运行空态） |

镜像已在 v1 阶段全部缓存于本地，v2 评测通常不需要重新拉取；若需要，先起
`tools/port_forward.py` 并确认 dockerd 的代理 drop-in 仍生效。

## 1. 触发的失败模式 → 协议升级

v1 的 12 条失败（子模式见 `comparison.md`）直接决定 v2 要补的验证环节：

### M1 目标契约细节不匹配（7 条：11019、11283、11564、11630、6506、5103、5221）

**在不看 `test_patch` 的前提下**，为每条补丁补一张「输出契约检查表」，逐项写成可执行断言：

- 文案：异常/告警的**确切字符串**是否可从 ticket、docstring、既有测试、文档中推出？
  推不出的必须在 summary 里列为「已知不确定性」。
- 级别：应该是 `Warning` 还是 `Error`？（11630 的教训：级别选错即失败）
  依据必须来自仓库内既有代码的同类用法，而不是直觉。
- 顺序：列表/查询/合并结果的顺序是否被断言？（11019）
  需要枚举「顺序由什么决定」，并写出正反两个用例。
- 格式：CLI/`repr`/消息格式（6506 的 `E0015`、5221 的 `--fixtures -v`、5103 的断言展开）
  必须对照仓库内既有的同类输出格式实现。
- 行为可观察面：把「修好了」定义成**可观察输出**，而不是内部状态的改变
  （11283 的教训：崩溃消失 ≠ 契约满足）。

### M2 补丁自带运行时/语法缺陷（3 条：11001、12308、12856）

强制门禁，缺一不可：

1. `git apply --check` 通过；
2. 受影响 Python 文件逐个 `python -m py_compile`；
3. 受影响模块可导入（`python -c "import <module>"`）；
4. 最小真实 repro 运行通过（不是只 import，而是真的触发被修路径）；
5. 保存上述命令的**原始输出**到 `runs_v2/<id>/verify_output.txt`。

### M3 目标测试通过但引入回归（1 条：12589）

除目标 repro 外，**必须**运行受影响模块的公开测试（例：`aggregation`、`invalid_models_tests`），
并在 summary 中给出 before/after 的测试计数；若公开测试无法在当前工作树运行，
必须在 summary 中显式记录「未运行 + 原因」，不得默认为通过。

### M4 修复不完整（1 条：11797）

对每个 ticket 显式列出**同族场景清单**（边界条件枚举：空值、多行、嵌套、多数据库、
继承、可选参数……），逐条标注「已覆盖/未覆盖/无法判断」，未覆盖项写进已知不确定性。

## 2. 每条实验的最小完成契约（v2 起生效，v1 只作为历史）

| 必填项 | 载体 | 说明 |
|---|---|---|
| 补丁 | `runs_v2/<id>/patch.diff` | 通过 `git apply --check` |
| 根因 | `summary.md` | 与 v1 同样的盲写纪律 |
| 置信度 | `summary.md` | 与 v1 同刻度（high/medium-high/medium/low） |
| **验证命令** | `summary.md` + `verify_output.txt` | 原样可复制执行 |
| **验证输出** | `verify_output.txt` | 原始输出，不摘要、不美化 |
| **已知不确定性** | `summary.md` | M1 类必须逐项列出（文案/级别/顺序/格式） |
| 信息条件 | `summary.md` | 是否使用 v1 反馈、用了哪部分 |

`verify.py` 是**优选载体**，但不是唯一载体：有用的是「命令 + 原始输出」这一对，
而不是某个固定文件名。v1 只有 19/37 有 `verify.py`，v2 起以本表为准，
避免再出现「声明每条都有 verify 却实际不齐」的情况。

## 3. 度量与报告

- 主指标：`v2` 在这批实例上的 resolved 率；对比对象是 v1 的同批实例（12 条修复组）
  与 v1 的 37 条全集（重复组）。
- 校准指标：分档读数（high/medium-high/medium 各档 n 与通过数）+ 过度自信条数；
  样本仍小，只作描述，必要时给出 Wilson 区间（v1：25/37 → 51.5%–80.4%）。
- 必须报告的对照：v1 失败 12 条中，哪些在 v2 转绿、哪些仍红、哪些引入新回归。
- **禁止**：把 v1 与 v2 的条目合并成一个通过率；把 v2 的修复回填进 v1 的
  `summary.md`/`verify.py`；为 v1 缺失项补造文件。

## 4. 若要把「并行 vs 串行」变成可发表的结论

v1 的观察（子代理 6/12 vs 主会话 19/25）被两个混杂因素污染：全部非 Django 实例在并行批次、
任务难度未匹配。要回答这个问题，v2 需要：

1. 把同一批实例**随机**分配到两种生产模式（或做难度配对）；
2. 预先声明分析口径（哪个是主指标、如何算置信区间）；
3. 记录每次生产的 token/时间成本，否则无法讨论「同等成本下的产出」。

## 5. 执行顺序（建议）

1. 先冻结 v1：运行 `python make_manifest.py`，把哈希与镜像 digest 落盘；
   `MANIFEST_v1.md` 转为带哈希的正式版本。
2. 建 `runs_v2/`，只从 v1 的 12 条失败开始，按第 1 节逐模式补验证。
3. 生成 `predictions_v2.jsonl`（`model_name_or_path` 用 `glm-5.3-zcode-campaign-v2`
   以便报告文件名与 v1 区分），跑 `-id tonight-v2`。
4. 产出 `comparison_v2.md`，与 `comparison.md` 并列报告，不合并。
