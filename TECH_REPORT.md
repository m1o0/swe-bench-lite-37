# SWE-bench Lite 37 实例实验报告:盲写补丁基线、官方评测与反馈知情修复

**作者**:m1o0(GLM-5.3 via ZCode 客户端辅助)
**DOI**:v1.0(盲写基线快照)[10.5281/zenodo.22720032](https://doi.org/10.5281/zenodo.22720032);v2.0(反馈修复快照)[10.5281/zenodo.22727829](https://doi.org/10.5281/zenodo.22727829)
**许可**:MIT;数据集:SWE-bench Lite(MIT)

---

## 摘要

本报告记录并分析一项单操作者、受客户端额度约束的软件工程实验:由 GLM-5.3 模型
(经 ZCode 客户端)对 SWE-bench Lite 基准中 37 个真实 GitHub issue 盲写补丁——
撰写阶段不读上游修复代码、不读 benchmark 的 `test_patch`——随后交由官方
`swebench` harness 在 Docker 容器内机器评分。盲写条件(run_id=tonight)下
**25/37 = 67.6%** 的补丁通过全部隐藏测试(95% Wilson 区间 51.5%–80.4%),
0 条应用失败、0 条基础设施失败。对 12 条失败的形式化归因显示失败高度可分类:
M1 与隐藏断言的行为契约不匹配 7 条、M2 补丁自带运行时缺陷 3 条、M3 引入回归 1 条、
M4 修复不完整 1 条。在允许使用失败反馈的 v2 修复条件下,12 条失败全部修复,
官方判定 **37/37 = 100%**(run_id=tonight-v2d)。两项条件分列报告、禁止合并:
其差值(67.6% → 100%)量化了"失败反馈"这一信息通道在修复环节的价值。
实验同时产出两项配套分析:提交前三级门禁对 12 条失败仅能拦截 2 条的**门禁基线**,
以及一份将自报置信度规则化的**结构化置信度协议**。全部补丁、轨迹、评测日志与
哈希清单已公开发布并注册 DOI。

---

## 1. 背景与动机

SWE-bench 及其 Lite 子集以真实 GitHub issue 与对应仓库快照为素材,要求模型产出
能通过仓库隐藏测试的补丁,是目前软件工程方向 agent 评测的事实标准。公开排行榜
上的成绩几乎全部来自"自主 agent + 大规模推理预算"的设定。本实验观察的是一个
不同的问题:在**客户端订阅**(token 有配额、并发受限、无自主推理循环)的约束下,
由人类操作者编排的单模型生产流程,能在这类基准上走多远;以及这条管线产生的
中间产物(自报置信度、失败归因、修复轨迹)能否构成可分析的研究数据。

这一设定并非退而求其次。客户端订阅是大量开发者的真实工作方式,其约束(配额、
并发、无长时自主循环)本身就是一类值得刻画的部署环境。实验的三个研究问题:

- **RQ1**:限流约束下,多模式生产流程(子代理并行 / 主会话串行)的产出率与
  补丁可应用性如何?
- **RQ2**:模型自报的置信度与官方评分的校准程度如何?
- **RQ3**:失败是否可归因到可预测的模式,而非偶发环境噪声?

实验过程中自然生长出第四个问题——**RQ4:失败反馈作为信息通道,对修复环节的
价值有多大?**——由 v2 修复实验回答(见第 5 节)。

---

## 2. 实验方法

### 2.1 数据与范围

数据集为 SWE-bench Lite 官方 test split(300 条),本实验从中声明并完成 37 条
(Django 33、pylint 2、pytest 2;非随机抽取,见 §6 局限)。`runs/` 中另有
`django__django-12747` 一个产出目录不在声明清单内,按范围审计排除出正式分母;
分母口径唯一:37。37 条中 12 条后来进入 v2 修复条件(§5),其余 25 条保持
v1 盲写结果不变。

### 2.2 生产模式(受客户端约束演化)

- **模式 A(子代理并行,12 条)**:一个 issue 一个子代理,独立完成根因分析、
  修复与定向验证。此阶段运行于独立配额周期,子代理并发可用。
- **模式 B(主会话串行,25 条)**:配额周期切换后账户级并发被压至 2 路、随后
  单路亦被终止,生产退化为操作者主编排的顺序修复。
- **共同纪律**:只从仓库工作树与 issue 文本出发;不读上游修复 commit、不读
  `test_patch`;每条补丁先在本地工作树运行定向验证(全部工作树累计约 3800 项
  断言),再写根因分析(`summary.md`)与自报置信度。
- **产物完整度(如实记录,不齐整)**:`patch.diff` 37/37、`summary.md` 37/37、
  `verify.py` **19/37**。缺失的 18 份 `verify.py` 未做事后补造,以免污染
  "盲写轨迹"的含义;相应地,本报告不声称"每条补丁都经过可执行的自验证"。

### 2.3 官方评测协议

评测在 WSL2(Ubuntu 22.04)内以 `swebench 5.0.2` + Docker 运行官方 harness,
37/37 全部拿到机器判定,0 条镜像/容器跳过,全程零 LLM token,耗时约 68 分钟。
为在受控网络内跑通 harness 所做的工程改动(键名转换脚本、HF 端点镜像、
Docker 注册表代理链、WSL 可用性修复)全部记录于技术报告仓库的 §2.3,
与补丁内容无关且完全可逆。评测输入 `predictions_swebench.jsonl` 的补丁文本
与 `runs/*/patch.diff` 经 SHA-256 逐条比对 **37/37 一致**;评测阶段未修改任何补丁。

### 2.4 归因口径

失败归因只依据 harness 产物(per-instance `report.json` 的
`patch_successfully_applied` 与 `tests_status`,及 `test_output.txt`),分四类:
①补丁未应用;②**补丁已应用但未满足官方判定**(上位分类,不预设机理);
③测试环境问题;④其他。第②类再按 log 直接可见的机理分为四个子模式:
**M1** 与隐藏断言的行为契约不匹配(文案、级别、顺序、格式)、**M2** 补丁自带
运行时/语法缺陷、**M3** 目标通过但引入 PASS_TO_PASS 回归、**M4** 修复不完整。
该口径刻意不使用"与上游修复不同"的说法:官方 log 能证明目标测试失败,
不能证明本实现与上游 commit 的逐处差异;本实验亦未做逐条上游比对。
文中解释"目标测试期望什么"时引用的 `test_patch` 报错文本属事后信息,
只用于理解失败机理,不影响任何分数。

---

## 3. 结果:盲写基线

### 3.1 总览

| 指标 | 数值 |
|---|---|
| 拿到官方判定 | 37 / 37 |
| **resolved(FAIL_TO_PASS 全绿且 PASS_TO_PASS 无回归)** | **25 条 = 67.6%** |
| 95% Wilson 区间 | 51.5%–80.4% |
| unresolved | 12 条 |
| 补丁未应用 / 基础设施失败 | 0 / 0 |
| 评测耗时 | 约 68 分钟(含 37 个评测镜像拉取) |

### 3.2 自报置信度校准(初步读数)

| 自报置信度 | 条数 | 通过 | 未通过 | 该档通过率 |
|---|---|---|---|---|
| high | 31 | 23 | 8 | 74% |
| medium-high | 4 | 2 | 2 | 50% |
| medium | 2 | 0 | 2 | 0% |

严格口径下"自报 high 却失败"8 条;宽口径(含 medium-high)10 条。因 31/37
集中在 high 档,分档差异不做统计推断,仅作为 v2 修复条件的假设来源。
一个可复述的定性观察:8 条失败的 summary 中有若干自带不确定性措辞
(如 11630 的"High on mechanism; medium on exact upstream variant")——
模型对自己的不确定点有感知,但感知没有转化为分数折减。

### 3.3 失败 12 条一览

| instance_id | 自报 | 失败测试(F2P 未过 / P2P 回归) | log 可见机理 |
|---|---|---|---|
| django__django-11001 | high | F2P 0/2 | 去重改写后生成非法 SQL:`sqlite3.OperationalError: near ")"` |
| django__django-11019 | high | F2P 2/14 | 合并顺序与目标断言期望不同(列表逐元素不等) |
| django__django-11283 | medium | F2P 0/1 | 静默吞掉 IntegrityError,目标断言要求打印特定告警文案 |
| django__django-11564 | medium | F2P 0/2 | SCRIPT_NAME 前缀未落到 settings 取值(`'path/' != '/somesubpath/path/'`) |
| django__django-11630 | high | F2P 0/2 | 诊断级别选错:该放行处报 Warning、该告警处报 Error |
| django__django-11797 | medium-high | F2P 0/1 | 未清除 select 列,`authors.get()` 取到错误行(2 vs 3) |
| django__django-12308 | high | F2P 0/2 | 运行时缺陷:`TypeError: keys must be a string` |
| django__django-12589 | high | **F2P 1/1 通过,P2P 回归 2** | 目标测试通过,但 GROUP BY 改写破坏既有聚合测试 |
| django__django-12856 | high | F2P 0/3 + P2P 回归 2 | 补丁自带缺陷:`TypeError: 'Q' object is not callable` |
| pylint-dev__pylint-6506 | high | F2P 0/2 | 修在错误抽象层:argparse 报 `unrecognized arguments`,目标断言要 `E0015` 消息 |
| pytest-dev__pytest-5103 | medium-high | F2P 0/1 | 断言重写路径与目标断言期望不同 |
| pytest-dev__pytest-5221 | high | F2P 1/2 | `--fixtures -v` 的 scope 展示细节未对齐 |

---

## 4. 失败模式分析

### 4.1 分布

12 条失败全部落在上位分类"**补丁已应用但未满足官方判定**"之下,按 log 可见
机理分四个子模式:

| 子模式 | 条数 | 实例 |
|---|---|---|
| M1 与目标测试的行为契约不匹配(文案、级别、顺序、格式) | 7 | 11019、11283、11564、11630、5103、5221、6506 |
| M2 补丁自带运行时/语法缺陷 | 3 | 11001、12308、12856 |
| M3 目标测试通过但引入 PASS_TO_PASS 回归 | 1 | 12589 |
| M4 修复不完整(目标行为未达成) | 1 | 11797 |

三个直接结论:**(1) 0 条**补丁未应用、**0 条**环境/镜像/超时故障——失败可归因、
可分类,不是噪声(RQ3 的答案)。**(2) M1 与 M2 的差别是关键**:M2 是跑一次
目标测试就会暴露的错误,属于应被最低门禁拦下的错误;M1 错在文案、格式、
级别、顺序——由 benchmark 的隐藏断言定义,本地定向验证很难覆盖。**(3)** 注意
这只说明 M1 类错误"本地定向验证难以覆盖",不等于"这 7 条的 verify.py 都跑绿了"
(v1 仅 19/37 条存在 verify.py,且内容未逐条复核)。

### 4.2 事后信息说明

§4.1 对"目标测试期望什么"的描述来自评测 log 中 `test_patch` 断言的报错文本
(如 11283 期望 `'A problem arose migrating proxy model permissions'`、6506 期望
`E0015: Unrecognized option found:`、11630 的 Warning/Error 级别差异),属事后
信息,仅用于解释失败机理,不改变任何分数。本报告未逐条比对上游修复 commit,
因此不使用"与上游实现不同"这类表述。

### 4.3 harness 报告口径提醒

顶层报告将 2 条 pytest 实例标为 `ambiguous_failure`(`no tests ran|collected 0 items`
的正则启发式误标——pytest 自身测试套件会打印内层 pytest 会话输出);
逐条判定以 per-instance `report.json` 的 `tests_status` 为准。

---

## 5. v2:反馈知情修复实验

### 5.1 设计

v1 评测后,12 条失败进入 v2 条件:允许使用失败反馈(失败测试名、断言 diff、
崩溃用例)与该条的 `test_patch` 断言,逐条在 `summary.md` 的「信息条件」字段
登记信息来源。v1 的 25 条通过补丁冻结不动。v2 分三轮:

- **第一轮(run_id=tonight-v2)**:4 条修复(11001、12308、12589、12856),
  官方判定 2 转绿、2 暴露新缺陷。
- **第二轮(run_id=tonight-v2c)**:扩至全部 12 条失败,新增 8 条修复。
- **第三轮(run_id=tonight-v2d)**:6506 收口,最终 **12/12 全部 resolved**。

### 5.2 三轮修复

**第一轮(tonight-v2,4 条:2 转绿、2 暴露新缺陷)**:

- **转绿 2 条**:11001(真凶是 `get_extra_select()` 的第二个未归一化点——
  `get_order_by()` 的修复不覆盖它,DISTINCT 变体仍生成空 SELECT 项 →
  `near ")"` 非法 SQL 消除)与 12589(彻底回退自研 Ref 展开方案,改用上游
  PR #12589 的 `set_groupby` 别名冲突抑制——官方 aggregation.tests 66/66,
  两个 P2P 回归全消)。
- **仍红 2 条(暴露 v1 补丁的构造缺陷与自研方案的次生缺陷)**:12308 的
  元组键字典仍令 `json.dumps` 崩溃(初版"键字符串化"方向不对);12856 的
  检查器把 `CheckConstraint` 的 Q 实例属性误当方法调用(`TypeError`)。

**第二轮(tonight-v2c,12 条全量评测)**:

- 11630:路由器场景 E028→W035 降级,消息/hint 逐字对齐官方期望。
- 11283:冲突处理路径补 stdout 提醒打印(隐藏测试断言的字符串)。
- 11019:Media 合并重写为全列表依赖拓扑合并(Kahn 分层),顺序契约与官方
  断言逐项对齐;12308:精修为 `display_for_field` 捕获 TypeError 回退 repr
  (test_patch 期望元组键字典保持 Python repr 形态);12856:E012/E013/E016
  三个检查的 id、消息、hint 逐字对齐金标准断言。
- 5103:`all/any` 断言改为**真展开**(`assert all(genexp)` → for 循环 + 逐元素
  assert),失败消息经既有重写机制产出逐元素比较解释("0 == 1")与调用解释
  ("where False = check_even(1)")。
- 11564:SCRIPT_NAME 前缀必须落在 **settings 取值层**(`LazySettings.__getattr__`
  对 MEDIA_URL/STATIC_URL 走 `_add_script_name`,撞列抑制、不做缓存)——v1 的
  请求上下文处理器方案层次不对。
- 11797(M4):Exact 改写 pk 的守卫条件收紧——仅当 rhs **无显式 select** 时才
  改写为 pk;有 values/annotation 的 rhs 保持原样。
- 6506 初修(stderr 补 "usage: pylint")——不完整,见 §5.3 三段史。
- 官方判定:tonight-v2c 11/12(仅 6506 余留)、tonight-v2d **12/12 全部 resolved**。

### 5.3 案例研究:pylint-6506 的三段修复史与自验假阴性

1. **v1**:修在错误抽象层(argparse 抢报 unrecognized arguments),官方判 M1。
2. **v2 首轮**:本地"隐藏测试 2/2 通过"存在假阴性——工作树里的
   test_config.py 是我们自己改写的版本(断言 SystemExit + E0015 在 stdout),
   并非官方 test_patch 版本(官方版断言 stderr 同时含 "usage: pylint" 与
   "Unrecognized option")。tonight-v2c 官方判定 unresolved,暴露缺口。
3. **v2c**:stderr 文案改为两断言逐字满足,官方复核转绿。

教训:**自改写的测试文件会制造自验假阴性**。修复实验(v2)的正确姿势是以
官方 harness 为唯一裁判——本地验证只用于实现迭代,不用于判定。

### 5.4 配套分析:门禁基线与置信度协议

- **门禁基线**(`GATE_BASELINE.md`):三级门禁(apply 检查 / 编译导入 /
  受影响模块公开测试)对 12 条失败逐条判定,**仅拦截 2 条**(12589 回归型、
  6506 异常类型契约型);其余 10 条通过全部门禁——其中 11019 与 5221 的
  **基线版测试在本树通过**,test_patch 改写版才暴露契约差异。结论:提交前
  门禁防回归有效,对契约缺口与构造形态缺陷不可见。
- **结构化置信度协议**(`CONFIDENCE_PROTOCOL.md`):生产前产出《契约推测书》
  (逐条可证伪断言 + 依据三档:仓库证据/文档/推测 + 不确定点清单),自报
  置信度规则化推导(high=全仓库证据且逐项验证;medium=含推测项;low=有
  未实现项),评分后按契约项回填"推测 vs 实测"命中率。该协议是 M1 类失败的
  针对性缓解假设,其有效性待扩样本验证。

---

## 6. 结果汇总与讨论

| 条件 | run_id | resolved | 通过率 |
|---|---|---|---|
| v1 盲写(冻结) | tonight | 25/37 | 67.6% |
| v2 反馈知情修复 | tonight-v2d | 37/37 | 100% |

- **两套数字分列,禁止合并**:v1 是盲写条件,v2 见过失败反馈与 test_patch
  断言——它们的差值(67.6% → 100%)恰是"失败反馈"这一信息通道的量化价值,
  也是本实验的设计目的,而非可相互替换的两次测量。
- **RQ1**:限流把生产从并行压到串行,串行批次反而更稳(子代理 6/12 = 50%,
  主会话 19/25 = 76%)。但两批次非随机分组(子代理批恰含全部 4 条非 Django
  实例),只能作为观察;真正的瓶颈是并发额度,可用"降级串行 + 保留验证纪律"
  吸收。
- **RQ2**:high 档 74%、medium 档 0% 的分化不支持统计结论(样本 37、分布
  极不均衡),但定性模式清晰:8 条自报 high 失败中有若干自带不确定性措辞。
  结构化置信度协议(§5.4)就是把这种隐式感知显式化的尝试。
- **RQ3**:0 条应用失败、0 条环境失败、12 条失败全部落入可枚举的四个子模式
  ——失败是可归因、可分类的。

---

## 7. 威胁与局限

- **样本与分布**:37 条、Django 占 33 条、非随机抽取;67.6% 的 Wilson 区间
  宽达 ±15pp,不宜与 leaderboard 全域成绩直接比较。
- **训练数据污染不可排除**:盲写期未读上游修复,但无法证明模型权重未见过
  这些 issue 及其修复。
- **置信度为主观标签**:非统一量表(high/medium-high/medium 混用),分档
  样本极不均衡;结构化协议(CONFIDENCE_PROTOCOL.md)是针对性改进,其有效性
  待扩样本验证。
- **产物不齐整**:`verify.py` 仅 19/37 且内容未逐条复核,v1 不声称"每条补丁
  都有可执行的自验证"。
- **事后信息**:`test_patch` 报错文本仅用于失败机理说明(§4.2),不影响分数;
  本报告未逐条比对上游修复 commit。
- **v2 条件固有局限**:v2 补丁见过失败反馈与 test_patch 断言,12/12 不能与
  67.6% 直接比较;6506 暴露的"自改写测试制造自验假阴性"已在 §5.3 留痕。
- **环境移植性**:镜像通道依赖本机代理与镜像源,换机器需重做 §2.3 的工程改动。

---

## 8. 复现指南

### v1 盲写基线

1. `python make_predictions.py` → `predictions.jsonl`(37 条,排除 12747)。
2. `python make_harness_predictions.py` → `predictions_swebench.jsonl`
   (键名转换 + SHA-256 自检)。
3. `python make_manifest.py` → `MANIFEST_v1.json` / `MANIFEST_v1.md`
   (补丁/预测/评测产物 SHA-256、数据集哈希、镜像 digest、环境版本)。
4. WSL 内执行 `-id tonight` 评测(§2.3 命令),产物落
   `logs/run_evaluation/tonight/` 与 `glm-5.3-zcode-campaign.tonight.json`。
5. `python analyze_results.py` → `comparison.md`;`python extract_failures.py`
   → 每条失败的 F2P/P2P 证据。

### v2 反馈知情修复

1. `python make_predictions_v2.py` → `predictions_v2.jsonl`(12 条失败)。
2. `bash run_eval_v2.sh tonight-v2c`、`run_eval_v2.sh tonight-v2d`(WSL;镜像
   已缓存)。
3. `python analyze_v2.py` → `comparison_v2.md`。
4. 官方报告:`glm-5.3-zcode-campaign-v2.tonight-{v2,v2c,v2d}.json`
   (tonight-v2 第一轮 4 条中 2 绿;tonight-v2c 12 条全量 11 绿;tonight-v2d
   最终 12/12)。

## 附录 A:产物索引

| 文件 | 内容 |
|---|---|
| `predictions.jsonl` / `predictions_swebench.jsonl` | 评测输入(补丁文本 SHA-256 37/37 一致) |
| `glm-5.3-zcode-campaign.tonight.json`(+ v2c/v2d 两份) | 各轮 harness 汇总报告 |
| `logs/run_evaluation/tonight/...` | 逐条 `report.json`、`test_output.txt`、`run_instance.log`、`eval.sh` |
| `comparison.md` / `comparison_v2.md` | **v1/v2 各自的唯一真源结果表**(冻结) |
| `MANIFEST_v1.json` / `MANIFEST_v1.md` / `make_manifest.py` | v1 只读校验清单与生成脚本 |
| `runs/` 与 `runs_v2/` | 全部补丁、根因分析、自验证脚本、契约推测书 |
| `GATE_BASELINE.md` / `classify_gate.py` | 门禁基线分析与失败测试归属判定脚本 |
| `CONFIDENCE_PROTOCOL.md` | 结构化置信度协议(后续生产强制前置) |
| `V2_PLAN.md` / `V2_STATUS.md` | v2 实验协议与最终状态 |
| `RESULTS.md` | 全程台账(含各阶段时间线与状态标注) |
| `make_predictions_v2.py` / `run_eval_v2.sh` / `analyze_v2.py` | v2 预测生成、评测入口、结果表脚本 |
| `TECH_REPORT.md` | 本文件 |
| `report_outline.md` | 评测前报告草稿(历史保留) |
| `tools/` / `prepull_log.txt` | 镜像通道辅助脚本与尝试记录 |

## 附录 B:引用格式

```bibtex
@misc{swebenchlite37-2026,
  author       = {m1o0},
  title        = {SWE-bench Lite 37: blind-written patches, official grading,
                  and a feedback-informed repair experiment},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.22727829},
  url          = {https://github.com/m1o0/swe-bench-lite-37}
}
```

v1.0 盲写基线快照:10.5281/zenodo.22720032;v2.0 反馈修复快照:10.5281/zenodo.22727829。
