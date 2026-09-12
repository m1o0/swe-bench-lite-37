# 明天打分指南(最终版,零 token,纯算力)

## 阶段一:准备(约 30 分钟)

1. 开 WSL:`wsl -d Ubuntu-22.04`
2. 安装官方评测库:
   ```bash
   python3 -m pip install -U swebench -i https://mirrors.aliyun.com/pypi/simple/
   ```
3. 生成预测文件(Windows 侧跑,或直接 WSL 访问 /mnt/c):
   ```powershell
   python <EXP_ROOT>\make_predictions.py
   ```
   → 产出 `<EXP_ROOT>\predictions.jsonl`(37 条)

## 阶段二:评测(1-2 小时,主要是拉镜像)

把 predictions.jsonl 拷进 WSL 可见位置(已在 /mnt/c 下),然后:

```bash
cd <EXP_ROOT_POSIX>
python3 -m swebench.harness.run_evaluation \
    --predictions_path predictions.jsonl \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --run_id tonight \
    --max_workers 4
```

注意:
- 首次会为每条实例拉取/构建 Docker 镜像(swebench/sweb.eval.x86_64.*),
  daemon.json 已配 DaoCloud 透明镜像;单镜像 2-8GB,37 条约 40-80GB 磁盘,
  C 盘紧张的话先把 WSL 发行版迁到 D 盘或清理。
- 只会评 predictions.jsonl 里出现的 instance_id,不会跑全部 300 条。
- 评测本身零 token、不联网推理,纯跑测试。

## 阶段三:结果(30 分钟)

- 结果在 `runs/tonight/` 下:每条实例的报告 log + 汇总
- 统计:FAIL_TO_PASS 通过数 / 37,按 patch.diff 是否正确应用分类
- 常见失败模式:补丁 context 对不上(路径/行号漂移)、测试依赖缺失、
  修复语义与上游不同 —— 逐条记进 RESULTS.md 的"实测"列

## 阶段四:对比表 + 报告(1 小时)

对每条补丁做三列对比:
| instance_id | summary.md 自报置信度 | 官方实测 | 差异原因 |

这张表就是你 agent 研究的第一份真实数据:
- 自报 high 但实测失败 → 过度自信案例(研究素材)
- 自报 medium 但实测通过 → 保守案例
- 全部通过率 = "GLM-5.3 + ZCode 人工编排" 在 SWE-bench Lite 子集上的
  真实成绩单(可与官方 leaderboard 对比)

## 写作出口(选一)
- 技术博客:额度转化实验 + 37 补丁 + 对比表
- workshop 短文骨架:上述内容 + 限流约束下的方法论讨论
- 简历/申请一句话:"独立复现 SWE-bench Lite 37 实例,N 条通过官方评测"

## 清理(评测完成后)
- 删工作树:`wsl` 里 `rm -rf /mnt/d/mio/worktrees/*`(回收磁盘)
- 删评测镜像:`docker rmi $(docker images -q swebench/*)` 
- 保留:runs\、predictions.jsonl、RESULTS.md、数据集 parquet(研究数据)
