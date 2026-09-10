# runs_v2：v2（评测后修复条件）工作区

> **与 v1 的边界**：`runs/` 是 v1 盲写产出，**只读**。本目录是 v2。
> v1 的分数（`25/37 = 67.6%`，`comparison.md`，run_id `tonight`）已冻结，
> v2 的任何结果都**不得**合并进 v1 的统计，也不得覆盖 `runs/`、`predictions_swebench.jsonl`、
> `logs/run_evaluation/tonight/`。规则详见 `../V2_PLAN.md`。

## 目录约定

```
runs_v2/
  <instance_id>/
    patch.diff                 # v2 补丁（新建，不复制 v1 文件覆盖）
    summary.md                 # 根因 + 置信度 + 验证命令 + 已知不确定性 + 信息条件
    verify_output.txt          # 验证命令的原始输出（不摘要、不美化）
    CONTRACT_CHECKLIST.md      # 该实例的输出契约检查表（M1 类必填）
    verify.py                  # 可选：优选载体，但非唯一载体
```

## 每条的最小完成契约

| 必填项 | 载体 | 通过标准 |
|---|---|---|
| 补丁 | `patch.diff` | `git apply --check` 通过 |
| 根因 | `summary.md` | 与 v1 同样的盲写纪律（不读上游修复、不读 `test_patch`） |
| 置信度 | `summary.md` | 与 v1 同刻度：high / medium-high / medium / low |
| 验证命令 | `summary.md` | 可原样复制执行 |
| 验证输出 | `verify_output.txt` | 原始输出 |
| 已知不确定性 | `summary.md` | M1 类逐项列出：文案 / 级别 / 顺序 / 格式 |
| 信息条件 | `summary.md` | **是否使用了 v1 评测反馈、用了哪一部分**（这是 v1↔v2 对比的自变量） |
| 契约检查表 | `CONTRACT_CHECKLIST.md` | 仅 M1 类必须；其余可选 |

## 门禁（M2 类强制，其余建议）

1. `git apply --check patch.diff`
2. `python -m py_compile <改动文件…>`
3. `python -c "import <受影响模块>"`
4. 最小真实 repro 运行（真的触发被修路径，而不是只 import）
5. M3 类追加：受影响模块的公开测试 + before/after 计数

以上命令与输出全部落进 `verify_output.txt`。

## 处理顺序（12 条 v1 失败）

| 子模式 | 实例 | 检查表 |
|---|---|---|
| M1 契约细节 | django-11019、django-11283、django-11564、django-11630、pylint-6506、pytest-5103、pytest-5221 | 各自的 `CONTRACT_CHECKLIST.md` |
| M2 运行时缺陷 | django-11001、django-12308、django-12856 | 走门禁 1–4 |
| M3 引入回归 | django-12589 | 门禁 1–4 + 公开测试 before/after |
| M4 修复不完整 | django-11797 | 同族场景清单逐条覆盖 |

## 跑评测（v2）

```bash
# 1) 生成 v2 预测文件（Windows 侧）
python make_predictions_v2.py

# 2) 评测（WSL 内；镜像已在 v1 阶段拉好，通常无需重新拉取）
cd <EXP_ROOT_POSIX>
HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation \
  -d SWE-bench/SWE-bench_Lite -s test -p predictions_v2.jsonl \
  -id tonight-v2 --max_workers 4

# 3) 结果表
python analyze_v2.py
```

第 3 步产出 `comparison_v2.md`，其中含 v1→v2 的逐条转移表
（转绿 / 仍红 / 新回归 / 未尝试），以及 v2 的分档读数。两张表永远分列报告。
