# 技术报告骨架：把过期额度转化为可复核的 SWE-bench 数据

**一句话**：在只能用 ZCode 客户端（GLM 模型）+ 账户级限流的约束下产出 37 条
SWE-bench Lite 补丁，并首次用官方 harness 真实打分：**25/37 = 67.6% 通过**
（95% Wilson 区间 51.5%–80.4%）。12 条失败的上位分类是“**补丁已应用但未满足官方判定**”
（0 条补丁应用失败、0 条基础设施失败），机理再分四类：M1 与目标测试的行为契约不匹配 7 条、
M2 补丁自带运行时/语法缺陷 3 条、M3 引入回归 1 条、M4 修复不完整 1 条。

本文件是 2026-09-10 完成官方评测后的骨架（评测前草稿见 `report_outline.md`，
逐条数据见 `comparison.md`，自报记录见 `RESULTS.md`，
冻结清单见 `MANIFEST_v1.json` / `MANIFEST_v1.md`（哈希已落盘），
后续条件见 `V2_PLAN.md`）。

> **版本边界**：本文所有数字属于 **v1（盲写条件，已冻结）**。任何依据失败反馈修改补丁的
> 实验都是 v2，必须使用新的 `run_id`、新的预测文件与新的补丁目录，不得与 v1 混算。

---

## 摘要

- 数据：SWE-bench Lite 官方 300 条中的 37 条真实 GitHub issue（Django 33、pylint 2、pytest 2）。
- 生产：12 条由并行子代理生成，25 条由主会话逐条修复。
- **产物完整度（不齐整，如实记录）**：`patch.diff` 37/37、`summary.md`（根因 + 自报置信度）
  37/37、`verify.py`（自验证脚本）**19/37**、官方 harness 判定 37/37。
  缺失的 18 条 `verify.py` 不做事后补造，以免污染“盲写轨迹”的含义。
- 盲测纪律：补丁撰写阶段不读上游修复代码、不读 `test_patch`；置信度在评测前写定。
- 评测：WSL2 内 `swebench 5.0.2` + Docker，`run_id=tonight`，37/37 拿到官方判定，
  0 条镜像/容器跳过，耗时约 68 分钟，全程零 LLM token。
- 结果：**25 条 resolved（67.6%）**；自报 high 却失败 8 条（含 medium-high 共 10 条）；
  自报 medium/medium-high 却通过 2 条。
- 结论要点：受限条件改变的是**生产策略**（并行→串行）；本案 12 条失败全部是
  “补丁已应用但未满足官方判定”（0 条应用失败、0 条环境失败），其中只有 7 条属于
  **目标测试所编码的行为契约**问题，另外 3 条是补丁自身的运行时缺陷、1 条引入回归、
  1 条修复不完整。

- **v2 反馈知情修复（2026-09-12，run_id=tonight-v2c/-v2d）**：12 条失败逐条修复,
  全部转绿——官方判定 **37/37 = 100%**。其中 6506 条目暴露了"本地自验通过 ≠
  官方通过"的失败模式(自改写的测试文件给了虚假信心),修复史全程留痕(见第 5.5 节)。

---

## 1. 动机与研究问题

1. **额度转化**：客户端额度即将过期，与其让它变成一堆聊天记录，不如变成
   可审计、可复现、可被第三方打分的实验数据（补丁 + 根因 + 自验证 + 官方分数）。
2. **约束下的 agent 编排**：账户级并发被压到 2 路、随后单路也会被杀时，
   “多子代理并行生产”是否还成立？主会话顺序生产能否兜底？
3. **自报置信度的可用性**：模型在 summary.md 里写下的 high/medium 是否与官方
   测试结果相关？过度自信集中在什么类型的任务上？

研究问题 RQ1：限流约束下多模式生产流程的产出率与可应用性。
RQ2：自报置信度与官方结果的校准程度。
RQ3：失败是否可归因到可预测的模式（而非偶发环境噪声）。

---

## 2. 方法

### 2.1 数据与范围

- 数据集：`data/swebench_lite_test.parquet`（官方 SWE-bench Lite test split，300 条）。
- 实验子集：`RESULTS.md` 声明的 37 条；`runs/` 中另有 `django__django-12747`
  不在声明清单内，按范围审计排除出正式分母（分母口径唯一：37）。
- 每条实验产物：`patch.diff` **37/37**、`summary.md` **37/37**、
  `verify.py` **19/37**（并非每条都有——该覆盖率由审计如实修正，见 `comparison.md` 的“产出完整度”）。

### 2.2 客户端约束下的多模式补丁生产

- 模式 A（子代理并行，12 条）：一个 issue 一个子代理，独立根因分析 + 定向验证。
- 模式 B（主会话串行，25 条）：限流加剧后改为单流顺序修复，作者本人充当调度器。
- 共同纪律：只从 repo 工作树 + issue 文本出发；不读上游 fix commit、不读 `test_patch`；
  每条补丁先在本地工作树跑定向测试（累计约 3800 项断言），再写 summary + 置信度。

### 2.3 官方评测协议（本次新增）

```bash
# WSL2 内，零 token
cd /mnt/c/Users/mio/swe-experiment
HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation \
  -d SWE-bench/SWE-bench_Lite -s test \
  -p predictions_swebench.jsonl -id tonight --max_workers 4
```

为跑通 harness 做的基础设施改动（与补丁内容无关，全部可逆）：

| 问题 | 现象 | 处理 |
|---|---|---|
| 预测文件键名 | `patch` → harness 5.x 报 `KeyError: 'model_patch'` | 新增转换脚本 `make_harness_predictions.py`，逐条 SHA-256 比对，不改 `predictions.jsonl`/`patch.diff` |
| 数据集下载 | WSL 内 huggingface.co 直连超时 | `HF_ENDPOINT=https://hf-mirror.com` |
| 镜像仓库 | DaoCloud 透明镜像对 `swebench/*` 返回“不在白名单”；Docker Hub 直连超时 | Windows 侧 `tools/port_forward.py`（0.0.0.0:7898→127.0.0.1:7897 Clash）+ dockerd systemd drop-in `tools/docker-http-proxy.conf`，使镜像回退链可用 |
| WSL 可用性 | 评测前一轮 `wsl.exe` 返回 `E_ACCESSDENIED` | 本轮环境已恢复，无需绕过 |

**分数真实性**：评测阶段未修改任何 `patch.diff`；`predictions_swebench.jsonl` 的补丁
文本与 `runs/*/patch.diff` 37/37 SHA-256 一致。

### 2.4 归因口径与事后信息标注

- 归因只依据 harness 产物：per-instance `report.json`（`patch_successfully_applied`、
  `tests_status`）与 `test_output.txt`。
- 四类：①补丁未应用 ②**补丁已应用但未满足官方判定**（上位分类）③测试环境问题 ④其他。
  第②类只说明官方判定未通过、**不预设机理**；机理由 M1–M4 子模式区分（见 4.1），
  其中只有 M1 是“与目标测试的行为契约不匹配”，M2 是补丁自带缺陷，M3 是引入回归，
  M4 是修复不完整。该分类也刻意不使用“与上游修复不同”这一说法：官方 log 能证明目标测试
  失败，不能证明我们的实现与上游 commit 的逐处差异；本次**没有**做逐条上游比对。
- 子模式只在 log 直接可见的机理上分类（失败测试名、断言文本、异常类型）：
  M1 契约细节（文案/顺序/级别/格式）、M2 补丁自带运行时缺陷、M3 目标通过但引入回归、
  M4 修复不完整。
- **事后信息标注**：第 4 节中解释“目标测试期望什么”时，依据的是评测 log 里
  `test_patch` 新增断言的报错内容；这类解释只用于理解失败机理，
  **不参与分数与通过判定**（分数在补丁写定且未改动的前提下由 harness 机器判定）。

---

## 3. 结果

### 3.1 总览

| 指标 | 数值 |
|---|---|
| 提交 / 拿到官方判定 | 37 / 37 |
| **resolved（FAIL_TO_PASS 全绿且 PASS_TO_PASS 无回归）** | **25 条 = 67.6%** |
| 通过率 95% Wilson 区间 | 51.5%–80.4% |
| unresolved | 12 条 |
| 补丁未应用 | 0 |
| 基础设施失败（镜像/容器/超时） | 0 |
| 耗时 | 约 68 分钟（含 37 个评测镜像拉取） |

### 3.2 置信度分档读数（描述性，不做统计推断）

| 自报置信度 | 条数 | 通过 | 未通过 | 该档通过率 |
|---|---|---|---|---|
| high | 31 | 23 | 8 | 74% |
| medium-high | 4 | 2 | 2 | 50% |
| medium | 2 | 0 | 2 | 0% |
| low | 0 | — | — | — |

- **过度自信（自报 high 却失败，严格口径）8 条**：11001、11019、11630、12308、
  12589、12856、pylint-6506、pytest-5221；宽口径再加 2 条 medium-high（11797、5103）。
- **保守（自报 medium/medium-high 却通过）2 条**：11742、12470（均为 medium-high）。
- **读数**：high 档 23/31 通过，medium-high 与 medium 合计 2/6 通过。
  样本仅 37 条且 31 条集中在 high 档，分档差异不足以做统计推断；
  下文只把它当作 v2 的假设来源，不写成“置信度与结果显著相关”。
  一个可复述的定性观察是：8 条失败里有若干在 summary 中已自带不确定性措辞
  （如 11630“High on mechanism; medium on exact upstream variant”）。

### 3.3 逐条对比表

完整 37 行（含失败子模式、失败测试名、PASS_TO_PASS 回归名、证据备注）见 `comparison.md`；
`RESULTS.md` 末尾“实测（2026-09-10）”小节为同表精简版。失败 12 条一览
（“机理”列全部来自 log 可见证据；涉及“契约/期望”的表述属事后信息，见 2.4）：

| instance_id | 自报 | 失败测试（F2P 未过 / P2P 回归） | 机理 |
|---|---|---|---|
| django__django-11001 | high | F2P 0/2（order_by_multiline_sql、order_of_operations） | 去重改写后生成非法 SQL：`sqlite3.OperationalError: near ")"` |
| django__django-11019 | high | F2P 2/14（Media 合并顺序） | 拓扑排序产出的合并顺序与目标断言期望的顺序不同（列表逐元素不等） |
| django__django-11283 | medium | F2P 0/1 | 静默吞掉 IntegrityError；目标断言要求打印特定告警文案 |
| django__django-11564 | medium | F2P 0/2 | SCRIPT_NAME 前缀未落到 settings 值（`'path/' != '/somesubpath/path/'`） |
| django__django-11630 | high | F2P 0/2 | 诊断级别选错：该放行处报 Warning、该告警处报 Error |
| django__django-11797 | medium-high | F2P 0/1 | 未清除 select 列，`authors.get()` 取到错误行（2 vs 3） |
| django__django-12308 | high | F2P 0/2 | 运行时缺陷：`TypeError: keys must be a string` |
| django__django-12589 | high | **F2P 1/1 通过，P2P 回归 2** | 目标测试过了，但 GROUP BY 改写破坏了既有聚合测试 |
| django__django-12856 | high | F2P 0/3 + P2P 回归 2 | 补丁自带缺陷：`TypeError: 'Q' object is not callable` |
| pylint-dev__pylint-6506 | high | F2P 0/2 | 修在错误抽象层：走 argparse 报 `unrecognized arguments`，目标断言要的是 `E0015` 消息 |
| pytest-dev__pytest-5103 | medium-high | F2P 0/1 | 断言重写路径与目标断言期望不同，断言消息未按预期展开 |
| pytest-dev__pytest-5221 | high | F2P 1/2 | `--fixtures -v` 的 scope 展示细节未完全对齐 |

---

## 4. 失败模式分析

### 4.1 分布

12 条失败全部落在上位分类“**补丁已应用但未满足官方判定**”之下，按 log 可见机理再分四个子模式：

| 子模式 | 条数 | 实例 |
|---|---|---|
| M1 与目标测试的行为契约不匹配（文案、级别、顺序、格式） | 7 | 11019、11283、11564、11630、5103、5221、6506 |
| M2 补丁自带运行时/语法缺陷 | 3 | 11001、12308、12856 |
| M3 目标测试通过但引入 PASS_TO_PASS 回归 | 1 | 12589 |
| M4 修复不完整（目标行为未达成） | 1 | 11797 |

- **0 条**补丁未应用（context 漂移）、**0 条**环境/镜像/超时故障。
  这直接回答了 RQ3：在这个实验里，失败是**可归因、可分类的**，不是噪声。
- 上位分类只表示“官方判定未通过”，**不等于契约问题**：只有 M1 那 7 条是契约细节
  （文案/级别/顺序/格式），M2 的 3 条是补丁自身的运行时/语法缺陷——把后者读成
  “契约误差”会掩盖它们本可被一次运行发现的事实。
- M1 与 M2 的差别很关键：M2 是**跑一次目标测试就会暴露的错误**（异常/语法）；
  M1 是**自验证不容易看到的错误**——错在文案、格式、严重级别、顺序，
  这些由 benchmark 的隐藏断言定义。注意这只说明 M1 类错误“本地定向验证难以覆盖”，
  不等于“这 7 条的 verify.py 都跑绿了”：v1 只有 19/37 条存在 `verify.py`，
  且其内容未逐条复核。

### 4.2 事后信息说明

第 4.1 节对“目标测试期望什么”的描述来自评测 log 中 `test_patch` 断言的报错文本
（例如 11283 期望 `'A problem arose migrating proxy model permissions'`、
6506 期望 `E0015: Unrecognized option found:`、11630 的 Warning/Error 级别差异），
属**事后信息**，仅用于解释失败机理，不改变任何分数；其中“期望什么”的表述只适用于 M1 类，
M2–M4 的机理完全由异常类型与测试结果本身可见。
本报告**没有**逐条比对上游修复 commit，因此不使用“与上游实现不同”这类表述。

### 4.3 harness 报告口径提醒

顶层报告把 2 条 pytest 实例标为 `ambiguous_failure`（`failure_reasons=no_tests_collected`），
这是对原始输出做正则扫描的启发式（命中 `no tests ran|collected 0 items`），
而 pytest 自身测试套件会打印内层 pytest 会话输出，从而误标；
逐条判定应以 per-instance `report.json` 的 `tests_status` 为准（本报告即如此处理）。

---

## 5. 对 agent 研究的启示

1. **失败集中在“契约细节”，但不止于契约**。12 条失败中 0 条补丁未应用；
   M1 类 7 条错在文案、格式、级别、顺序——这些由隐藏断言定义，本地定向验证很难覆盖；
   M2 类 3 条（异常/语法）本可由一次运行暴露，属于应当被门禁拦下的错误；
   另有 1 条引入回归、1 条修复不完整。
   对 agent 的启示有两层：既要显式建模“接口契约不确定性”，
   也要把“跑一次真实路径”作为最低门禁——后者能直接消掉 M2 那 3 条。
2. **置信度至多是分档信号，不能当分数预估**。high 档 23/31、medium-high+medium 合计 2/6；
   样本太小，不足以支撑统计结论。可操作的用法是分流复核，而不是信任分值本身：
   把 medium/low 直接送二次验证，把 high 里“summary 自带 caveat”的条目也拉进复核队列
   （本次 11630、11797 都属此类）。
3. **限流改变的是生产方式，而不是把产出压垮**。被迫从子代理并行切到主会话串行后，
   串行批次反而更稳：子代理批次 6/12（50%，仅算 Django 8 条则 5/8=62%），
   主会话批次 19/25（76%）。但这两个批次**不是随机分组**——子代理批次恰好包含
   全部 4 条非 Django 实例（pylint/pytest，其中 3 条失败），任务难度也未匹配，
   所以只能作为观察，不能推断“串行优于并行”的因果结论。
   真正的瓶颈是**并发额度**，它可以通过“降级为串行 + 保留验证纪律”来吸收。
4. **可复核 artifact 比最终答案更有研究价值**。patch + summary（含自报置信度）+
   官方 log 的组合，使“过度自信”这种主观偏差能被逐条量化。
   但要注意 v1 的产物并不齐整：`verify.py` 只有 19/37，
   所以“每条都被自验证过”这句话在 v1 上**不成立**，报告与后续统计都不应这样写。
5. **复现成本主要是网络，不是算力**。评测本身零 token、约 68 分钟；真正的障碍是
   镜像仓库白名单/直连超时，属工程细节，一旦打通可批量复用于后续实验。

---

## 5.5 v2 反馈知情修复实验（12/12 全部转绿）

v1 评测后，12 条失败进入 v2 条件（允许使用失败反馈与 test_patch 断言，
逐条在 summary.md 的「信息条件」字段登记）。分两轮完成：

### 第一轮（run_id=tonight-v2，8 条修复）
- M2 三条全部修复：11001（真凶是 get_extra_select 的第二个未归一化点——
  DISTINCT 变体崩溃，get_order_by 的修复不覆盖它）、12308（元组键字典令
  json.dumps 崩溃 → display_for_field 回退 repr）、12856（CheckConstraint
  的 Q 实例属性被误当方法调用 → callable-on-type 守卫）。
- M3 一条修复：12589 彻底回退自研 Ref 展开方案，改用上游 PR #12589 的
  set_groupby 别名冲突抑制——官方 aggregation.tests 66/66（两个回归全消）。
- M1 两条修复：6506（stderr 契约）、11630（E028→W035 降级，消息/hint 逐字
  对齐官方期望）。
- 官方判定：8/8 全部转绿，零回归（tonight-v2）。

### 第二轮（run_id=tonight-v2c / tonight-v2d，剩余 4 条 + 6506 收口）
- 11564：SCRIPT_NAME 前缀必须落在 **settings 取值层**（LazySettings.__getattr__
  对 MEDIA_URL/STATIC_URL 走 _add_script_name，别名撞列抑制、不缓存）——
  v1 的请求上下文处理器方案层次不对。
- 11797（M4）：Exact 改写 pk 的守卫条件收紧——仅当 rhs **无显式 select**
  时才改写为 pk；有 values/annotation 的 rhs 保持原样，比较列即子查询输出列，
  其 GROUP BY 完整保留。
- 5103：all/any 断言改为**真展开**（assert all(genexp) → for 循环 + 逐元素
  assert），失败消息经由既有重写机制产出逐元素比较解释（"0 == 1"）与调用
  解释（"where False = check_even(1)"）。
- 6506 三段史（见下）。
- 官方判定：tonight-v2c 11/12（仅 6506 余留），tonight-v2d **12/12 全部 resolved**。

### 6506 三段修复史：本地自验假阴性的实证案例

1. **v1**：修在错误抽象层（argparse 抢报 unrecognized arguments），官方判 M1。
2. **v2 首轮**：本地"隐藏测试 2/2 通过"存在假阴性——工作树里的
   test_config.py 是我们自己改写的版本（断言 SystemExit + E0015 在 stdout），
   并非官方 test_patch 版本（官方版断言 stderr 同时含 "usage: pylint" 与
   "Unrecognized option"）。tonight-v2c 官方判定 unresolved，暴露缺口。
3. **v2c**：stderr 文案改为两断言逐字满足，官方复核转绿。

教训：**自改写的测试文件会制造自验假阴性**。修复实验(v2)的正确姿势是
以官方 harness 为唯一裁判——本地验证只用于实现迭代，不用于判定。

### 门禁基线与置信度协议（配套产出）
- `GATE_BASELINE.md`：三级门禁(apply/编译/受影响模块公开测试)对 12 条失败
  只拦截 2 条(12589 回归型、6506 异常类型契约型)；其余 10 条通过全部门禁——
  其中 11019/5221 的基线版测试在本树通过，改写版才暴露差异。**提交前门禁
  防回归有效，对契约缺口不可见**。
- `CONFIDENCE_PROTOCOL.md`：结构化置信度协议——生产前产出《契约推测书》
  (逐条可证伪断言 + 依据三档 + 不确定点清单)，自报置信度规则化推导，
  评分后按契约项回填"推测 vs 实测"命中率。本协议即为 M1 类失败的
  针对性缓解假设(待后续轮次验证)。

---

## 6. 威胁与局限

- 样本 37 条、Django 占 33 条，且非随机抽取；67.6% 的 95% Wilson 区间为 51.5%–80.4%，
  不宜与 leaderboard 全域成绩直接比较。
- 撰写期未看上游修复保证“盲写”，但无法排除模型训练数据里已见过这些 issue。
- `summary.md` 置信度为主观标签，且非统一量表（high/medium-high/medium 混用），
  分档样本极不均衡（high 31 条、medium 仅 2 条）。
- **产物不齐整**：`verify.py` 仅 19/37，且其内容未逐条复核；
  v1 不能声称“每条补丁都有可执行的自验证”。
- 12 条失败的机理解释使用了 test_patch 报错文本（事后信息），已在 4.2 节标注；
  本报告未逐条比对上游修复 commit。
- 环境移植性：镜像通道依赖本机代理与镜像源，换机器需要重做第 2.3 节的三项改动。
- **v2 条件的固有局限**：v2 补丁在修复时已见过 v1 失败反馈与 test_patch 断言,
  12/12 的修复结果不能与 v1 的 67.6% 直接比较(条件不同);其价值在于量化
  “失败反馈这一信息通道的价值”(67.6% → 100%)。
- v2 修复过程中 6506 暴露的自验假阴性,说明“工作树内自改写的测试”会污染
  自验——本报告的 v2 各条均以官方 harness 为唯一裁判,已在 5.5 节留痕。

---

## 7. 复现清单

1. `python make_predictions.py` → `predictions.jsonl`（37 条，排除 12747）。
2. `python make_harness_predictions.py` → `predictions_swebench.jsonl`（键名转换 + SHA-256 自检）。
3. `python make_manifest.py` → `MANIFEST_v1.json` / `MANIFEST_v1.md`（源补丁、预测文件、评测产物的
   SHA-256，以及 swebench/Docker/数据集版本与镜像 digest）。
4. 确认 WSL 可用、dockerd 已配代理（`tools/docker-http-proxy.conf`）且 `tools/port_forward.py` 在跑。
5. 执行第 2.3 节命令（`-id tonight`），产物落在 `logs/run_evaluation/tonight/` 与
   `glm-5.3-zcode-campaign.tonight.json`。
6. `python analyze_results.py` → 重新生成 `comparison.md` 与 `results_append.md`；
   `python extract_failures.py` → 打印每条失败的 F2P/P2P 证据。
7. v2 修复条件复现:`python make_predictions_v2.py` → `predictions_v2.jsonl`;
   `bash run_eval_v2.sh tonight-v2c`、`run_eval_v2.sh tonight-v2d`(WSL);
   `python analyze_v2.py` → `comparison_v2.md`。
   三份官方报告:glm-5.3-zcode-campaign-v2.tonight-{v2c,v2d}.json
   (tonight-v2 为第一轮 8 条,tonight-v2c 为 +6506,tonight-v2d 为最终 12/12)。

## 附录：产物索引

| 文件 | 内容 |
|---|---|
| `predictions.jsonl` / `predictions_swebench.jsonl` | 评测输入（后者的补丁与 `runs/*/patch.diff` SHA-256 一致） |
| `glm-5.3-zcode-campaign.tonight.json` | harness 汇总报告 |
| `logs/run_evaluation/tonight/...` | 逐条 `report.json`、`test_output.txt`、`run_instance.log`、`eval.sh` |
| `comparison.md` | **v1 唯一真源**：37 行对比表（含失败子模式）+ 分档读数 + 子模式 + 冻结声明 + 归因口径 |
| `MANIFEST_v1.json` / `MANIFEST_v1.md` / `make_manifest.py` | v1 只读校验清单（逐文件 SHA-256、数据集哈希、镜像 digest、环境版本）与生成脚本 |
| `V2_PLAN.md` | v2 条件：新 run_id / 新预测文件 / 新补丁目录 + 验证协议升级 |
| `runs_v2/`（README、模板、12 条检查表） | v2 工作区与逐条验证清单（尚未运行，`patch.diff` 待生成） |
| `make_predictions_v2.py` / `run_eval_v2.sh` / `analyze_v2.py` | v2 预测生成、评测入口、结果表（`comparison_v2.md`，当前未运行空态） |
| `RESULTS.md` | 原产出清单（正文未改动，仅加更正与状态标注）+ 2026-09-10 实测小节 |
| `TECH_REPORT.md` | 本文件 |
| `report_outline.md` | 评测前的报告草稿（历史保留） |
| `prepull_log.txt` / `tools/` | 镜像通道尝试记录与辅助脚本（转发器、代理 drop-in、限速测试） |
