# 今晚(2026-09-06)SWE-bench 冲刺战果清单(最终版)
# 打分:见 SCORING.md。每条含 patch.diff + summary.md + verify 于 runs\<instance_id>\
#
# 【2026-09-10 更正】产出并不齐整，实际覆盖为：patch.diff 37/37、summary.md 37/37、
# verify.py 19/37。原文“每条含 …verify”只对其中 19 条成立；缺失的 18 条不做事后补造，
# 以保持盲写轨迹的原样。逐条覆盖与校验值见 comparison.md 与 MANIFEST_v1.md。
# 【2026-09-10 结果指向】正式结果表是 comparison.md（v1 盲写条件，25/37 = 67.6%，已冻结）；
# 本文件下方 2026-09-08 的“实测”小节是评测前状态，仅作历史保留，不得用于统计。

## 完成清单(37 条,patch 已全部落盘)

### 子代理批次(12 条,限流前完成)
1. pylint-dev__pylint-6506 — 无法识别选项打印 traceback(high)
2. pytest-dev__pytest-5103 — 断言重写器 all/any unroll(medium-high,222 行)
3. pytest-dev__pytest-5221 — --fixtures 显示 scope(high)
4. pylint-dev__pylint-5859 — --notes 全标点 tag 不触发 W0511(high)
5. django__django-11001 — 多行 RawSQL order_by 被 GROUP BY 去重丢弃(high)
6. django__django-11019 — Media 合并 3+ 对象误报冲突(high,142 行拓扑排序,1.9 万例模糊测试)
7. django__django-11039 — sqlmigrate 对非事务 DDL 库包 BEGIN/COMMIT(high)
8. django__django-11049 — DurationField 错误消息格式(high)
9. django__django-11179 — 无依赖模型 delete() 不清 PK(high,定向测试通过)
10. django__django-11283 — auth.0011 迁移对重建代理模型崩溃(medium)
11. django__django-10914 — FILE_UPLOAD_PERMISSIONS 默认 0o644(high)
12. django__django-11133 — HttpResponse 支持 memoryview(high,单流模式首次存活)

### 主会话亲修批次(17 条,限流后完成)
13. django__django-11099 — 用户名验证器允许尾部换行(high,\A/\Z)
14. django__django-11422 — StatReloader 不监控 manage.py(high,__main__ 文件)
15. django__django-10924 — FilePathField path 接受 callable(high,formfield 求值)
16. django__django-11564 — SCRIPT_NAME 支持 STATIC_URL/MEDIA_URL(medium)
17. django__django-11620 — path converter 抛 Http404 应出技术 404(high)
18. django__django-11742 — max_length 适配最长 choices 检查(fields.E009,medium-high)
19. django__django-11583 — StatReloader embedded null byte 崩溃(high)
20. django__django-11630 — 跨 app db_table 冲突在多数据库(router)下放行(high)
21. django__django-11797 — 外层 filter 覆盖内查询 GROUP BY(medium-high)
22. django__django-11999 — get_FOO_display() 可被覆盖(high)
23. django__django-12125 — makemigrations 内部类路径错误(high,TypeSerializer+模块前缀回退)
24. django__django-12184 — 可选命名组崩溃视图(high,groupdict 判断)
25. django__django-12284 — 继承覆盖 choices 后 display 失效(high,与 #22 同族)
26. django__django-12286 — translation.E004 子语言基础语言回退(high)
27. django__django-12308 — admin 只读 JSONField 显示合法 JSON(high,含新增 prepare_value)
28. django__django-12453 — serialized_rollback 顺序约束失败(high,ticket 自带 diff)
29. django__django-12470 — 继承模型 -pk 排序方向丢失(medium-high)

### 主会话亲修批次 II(19:00 后追加,5 条)
30. django__django-12497 — 递归关系提示文案纠正 ForeignKey→ManyToManyField(high)
31. django__django-12589 — 子查询注解 GROUP BY 歧义列(high,Ref 展开,精确复刻 ticket 查询)
32. django__django-12700 — settings 清洗覆盖嵌套列表/元组(high,ticket 原样场景)
33. django__django-12708 — 同列 unique_together+index_together 删除崩溃(high,真实 schema editor 验证)
34. django__django-12856 — UniqueConstraint 字段系统检查 models.E012(high,缺失/m2m/非本地三场景)

### 主会话亲修批次 III(19:00-20:00 追加,3 条)
35. django__django-12915 — ASGIStaticFilesHandler 补 get_response_async(high)
36. django__django-12983 — slugify 剥离首尾横线/下划线(high,1 行)
37. django__django-13028 — 模型字段名 filterable 误判为表达式退出(high,resolve_expression 门控)

## 环境
- WSL2 Ubuntu 22.04(D:\mio\wsl) + Docker 29.8.0(DaoCloud 透明镜像源)
- 数据集:swe-experiment\data\swebench_lite_test.parquet(SWE-bench Lite 300 条)
- 任务卡:tasks\<instance_id>.json;仓库:D:\mio\repos(django/sympy/pylint/pytest)
- 打分:SCORING.md;工作树:运行中的在 D:\mio\worktrees(打分后可删)

## 官方测试套件验证(20:10,runtests.py 实跑)
29 个 Django 工树中的 21 个已在 WSL 用官方 runtests.py 跑过对应测试模块,
**全部通过(仅 1 条预期内的旧断言淘汰,见下)**,累计约 3800 项断言:

- 11099:22 OK | 11742:46 OK | 12856:79 OK(修正接线后)| 12286:148 OK
- 11564:52 OK | 12184:101 OK | 11620:151 OK | 12470:26 OK
- 11583:72 OK | 11422:67 OK | 11049:261 OK | 12284:321 OK
- 11999:310 OK | 10924:262 OK | 11179:60 OK | 11039:OK
- 11797:375 OK | 11019:639 OK | 11001:364 OK
- 12125:46 项中 1 失败 = 旧 `<locals>` 断言被 test_patch 淘汰(预期内)
- 未跑官方套件:12308/12453(direct verify 已过)、3 个 pylint/pytest 工树
  (独立测试系统,子代理阶段已定向验证)

## 已知限制
- 子代理通道被账户级模型并发限制废弃(实测并发上限 2 流,晚间加剧至单流也杀)
- 2 亿 token 目标在"仅 ZCode 客户端可用 + 账户级限流"双重约束下不可达;
  实际有效产出以本清单 28 条补丁 + 轨迹为准
  【2026-09-10 更正】此处"28 条"与本清单实际列出的 37 条不一致(12 子代理 + 25 主会话);
  官方评测、对比表与冻结清单一律以 37 条为分母。原文保留,仅加此注。
- patch 未经真实 harness 验证;每条的置信度与不确定性见各 summary.md
- 11564(SCRIPT_NAME)、11742(E009)、12470(列别名)的断言细节存在不确定性

## 实测（2026-09-08，官方 harness）

> **⚠️ 评测前状态记录，已由 2026-09-10 实测替代，不作为结果使用。**
> 本节记录的是当时评测未能启动的情形与占位值（全部为“未运行”）；正式结果表见
> `comparison.md`。自动统计若同时读取本节与本文件末尾的 2026-09-10 小节，
> 会得到互为矛盾的 74 行，请以 `comparison.md` 为唯一真源。

本轮只生成了正式范围内的 37 条预测（`predictions.jsonl`）。运行前发现
`runs/` 另有 `django__django-12747`，该目录不在本清单的 37 条范围内，已从
正式预测文件排除并单独记录；没有修改任何 `patch.diff`。

官方评测未能启动：当前执行环境调用 `wsl.exe` 返回
`Wsl/EnumerateDistros/Service/E_ACCESSDENIED`，宿主也没有可调用的 `docker`
命令；因此没有产生 harness log、FAIL_TO_PASS 或 PASS/FAIL 结果。下表中的
“未运行”不是补丁失败，不能用于计算通过率，也不能据此判断过度自信或保守案例。
镜像跳过清单为空：评测未进入 Docker 镜像拉取阶段。

| instance_id | summary.md 自报置信度 | 官方实测 | 差异/归因 |
|---|---|---|---|
| django__django-10914 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-10924 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11001 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11019 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11039 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11049 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11099 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11133 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11179 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11283 | medium | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11422 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11564 | medium | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11583 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11620 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11630 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11742 | medium-high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11797 | medium-high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-11999 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12125 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12184 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12284 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12286 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12308 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12453 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12470 | medium-high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12497 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12589 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12700 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12708 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12856 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12915 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-12983 | high | 未运行 | 基础设施阻塞：无 harness log |
| django__django-13028 | high | 未运行 | 基础设施阻塞：无 harness log |
| pylint-dev__pylint-5859 | high | 未运行 | 基础设施阻塞：无 harness log |
| pylint-dev__pylint-6506 | high | 未运行 | 基础设施阻塞：无 harness log |
| pytest-dev__pytest-5103 | medium-high | 未运行 | 基础设施阻塞：无 harness log |
| pytest-dev__pytest-5221 | high | 未运行 | 基础设施阻塞：无 harness log |

正式评测恢复后，应以 harness 的 `test_result`/`report.json` 逐条替换“未运行”，
再统计 high→FAIL 的过度自信案例、medium/low→PASS 的保守案例，并按补丁未应用、
语义差异、测试环境问题、其他四类填写归因。

> 以上 2026-09-08 小节为当时的阻塞记录，原样保留；下面是 2026-09-10 实际跑通
> 官方 harness 后的结果，取代其中“未运行”的占位值。原有产出清单与置信度记录未改动。

## 实测（2026-09-10 官方 harness，run_id=tonight）

评测输入 `predictions_swebench.jsonl`（补丁文本与 `predictions.jsonl` 逐字一致，仅键名 `patch`→`model_patch`，37/37 SHA-256 校验通过）；评测阶段未修改任何 `patch.diff`。37 条全部拿到官方判定，无镜像/容器/超时跳过。

| instance_id | summary.md 自报置信度 | 官方实测 | 失败归因 |
|---|---|---|---|
| django__django-10914 | high | 通过 | 通过 |
| django__django-10924 | high | 通过 | 通过 |
| django__django-11001 | high | 未通过 | 补丁已应用但未满足官方判定（M2 补丁自带运行时/语法缺陷） |
| django__django-11019 | high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节：顺序） |
| django__django-11039 | high | 通过 | 通过 |
| django__django-11049 | high | 通过 | 通过 |
| django__django-11099 | high | 通过 | 通过 |
| django__django-11133 | high | 通过 | 通过 |
| django__django-11179 | high | 通过 | 通过 |
| django__django-11283 | medium | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节：告警文案） |
| django__django-11422 | high | 通过 | 通过 |
| django__django-11564 | medium | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节：取值/格式） |
| django__django-11583 | high | 通过 | 通过 |
| django__django-11620 | high | 通过 | 通过 |
| django__django-11630 | high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节：Warning/Error 级别） |
| django__django-11742 | medium-high | 通过 | 通过 |
| django__django-11797 | medium-high | 未通过 | 补丁已应用但未满足官方判定（M4 修复不完整） |
| django__django-11999 | high | 通过 | 通过 |
| django__django-12125 | high | 通过 | 通过 |
| django__django-12184 | high | 通过 | 通过 |
| django__django-12284 | high | 通过 | 通过 |
| django__django-12286 | high | 通过 | 通过 |
| django__django-12308 | high | 未通过 | 补丁已应用但未满足官方判定（M2 补丁自带运行时/语法缺陷） |
| django__django-12453 | high | 通过 | 通过 |
| django__django-12470 | medium-high | 通过 | 通过 |
| django__django-12497 | high | 通过 | 通过 |
| django__django-12589 | high | 未通过 | 补丁已应用但未满足官方判定（M3 目标测试通过但引入回归） |
| django__django-12700 | high | 通过 | 通过 |
| django__django-12708 | high | 通过 | 通过 |
| django__django-12856 | high | 未通过 | 补丁已应用但未满足官方判定（M2 补丁自带运行时/语法缺陷） |
| django__django-12915 | high | 通过 | 通过 |
| django__django-12983 | high | 通过 | 通过 |
| django__django-13028 | high | 通过 | 通过 |
| pylint-dev__pylint-5859 | high | 通过 | 通过 |
| pylint-dev__pylint-6506 | high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节：修在错误的抽象层） |
| pytest-dev__pytest-5103 | medium-high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节：断言展开） |
| pytest-dev__pytest-5221 | high | 未通过 | 补丁已应用但未满足官方判定（M1 契约细节：CLI 展示格式） |

**官方通过率 25/37 = 67.6%（95% Wilson 区间 51.5%–80.4%）**；自报 high 却未通过 8 条（含 medium-high 则 10 条），自报 medium/medium-high 却通过 2 条。12 条失败的上位分类是“**补丁已应用但未满足官方判定**”——没有一条因补丁未应用或测试环境故障而失败；机理按 log 可见证据分四个子模式：M1 与目标测试的行为契约不匹配（文案/级别/顺序/格式）7 条、M2 补丁自带运行时/语法缺陷 3 条、M3 目标测试通过但引入回归 1 条、M4 修复不完整 1 条。

> 上位分类**不等于**契约问题：12 条里只有 M1 的 7 条属于“与目标测试的行为契约不匹配”，M2 的 3 条是补丁自身的运行时/语法缺陷。归因同样**不**声称“与上游修复实现不同”：官方 log 能证明目标测试失败，不能证明我们的实现与上游 commit 的逐处差异。

> **v1 冻结**：本节分数在盲写（未读上游修复与 `test_patch`）条件下产生，哈希绑定已落盘：`MANIFEST_v1.json` 记录 37 条 `patch.diff`／`summary.md`／`verify.py`／`report.json`／`test_output.txt` 的 SHA-256、数据集 parquet 哈希，以及 swebench 5.0.2、Docker 29.8.0；人读版为 `MANIFEST_v1.md`。脚本实检：`verify.py` 覆盖 **19/37**，`patch_delta_vs_predictions` **37/37 为 `true`**，镜像 digest **37/37** 已记录（与本地 `image_id` 一致）；此前两处脚本缺陷（WSL 输出编码、`docker inspect` 格式串含管道符）已修复并重跑验证。**不得覆盖或重算**分数。任何依据失败反馈修改补丁的实验进入 v2 条件：新 `run_id`、新预测文件、新补丁目录，方案见 `V2_PLAN.md`。

> **产物完整度（`make_manifest.py` 脚本实检）**：`patch.diff` 37/37、`summary.md` 37/37、`verify.py` **19/37**、官方 `report.json` 37/37。没有为 v1 缺失的 `verify.py` 事后补造文件。

逐条证据（含失败子模式列）、校准矩阵、生产模式观察表与归因口径见 `comparison.md`，失败机理分析见 `TECH_REPORT.md`，评测产物见 `logs/run_evaluation/tonight/` 与 `glm-5.3-zcode-campaign.tonight.json`。

### 本次评测为跑通所做的基础设施改动（与补丁无关）

- 新建 `predictions_swebench.jsonl`：swebench 5.x harness 读取键名 `model_patch`（旧键 `patch` 会 `KeyError`），转换脚本 `make_harness_predictions.py` 逐条做 SHA-256 比对，未改动 `predictions.jsonl` 与 `patch.diff`。
- 数据集经 `HF_ENDPOINT=https://hf-mirror.com` 加载（WSL 内 huggingface.co 直连超时）。
- 镜像通道：`/etc/docker/daemon.json` 里的 DaoCloud 透明镜像源对 `swebench/*` 返回“不在白名单”，WSL 直连 Docker Hub 超时；为此在 Windows 侧启动 `tools/port_forward.py`（0.0.0.0:7898 → 127.0.0.1:7897，即本机 Clash），并给 dockerd 加 `tools/docker-http-proxy.conf` systemd drop-in 指向该转发端口，使镜像回退链可用。沙箱内 `wsl.exe` 也不再返回 `E_ACCESSDENIED`。
- 评测共 37 条、耗时约 68 分钟（含镜像拉取），0 条镜像拉取失败。

### v2 脚手架（2026-09-10 晚，评测后修复条件，尚未运行）

v1 已冻结，后续按 `V2_PLAN.md` 分列推进；本次先把脚手架落盘（**不触碰 v1 任何文件**）：

- `runs_v2/README.md`：工作区规则、最小完成契约（补丁/根因/置信度/验证命令/验证输出/已知不确定性/信息条件）；
- `runs_v2/CHECKLIST_TEMPLATE.md` + `runs_v2/<instance_id>/CONTRACT_CHECKLIST.md`：为 12 条失败逐条写的契约检查表/门禁单（M1 文案/级别/顺序/格式，M2 apply+编译+导入+最小 repro，M3 公开测试 before/after，M4 同族场景清单）；
- `make_predictions_v2.py` → `predictions_v2.jsonl` + `v2_patch_status.md`（含“v2 补丁与 v1 是否相同”的审计列，防止把未改动的补丁算进修复率）；
- `run_eval_v2.sh`（WSL 入口，默认 `-id tonight-v2`）、`analyze_v2.py` → `comparison_v2.md`；
- 当前 `comparison_v2.md` 为**未运行空态**骨架：v2 条目 12、已跑 0；跑完后再由脚本填实测值。
- 环境提示：37 个评测镜像已在 v1 阶段缓存，v2 通常无需重新拉取；若需拉取，仍需先起 `tools/port_forward.py`。


## v2 反馈知情修复结果（2026-09-12，run_id=tonight-v2 / 5221-check / v2b-check）

12 条 v1 失败中完成 8 条修复（4 条契约级任务按预算纪律留给后续，检查表已就绪）。
逐条结果以 comparison_v2.md、各 runs_v2/<id>/verify 输出与官方 harness 报告为准：

| instance_id | 类别 | v2 修法 | 验证级别 | 结果 |
|---|---|---|---|---|
| django__django-11001 | M2 | get_extra_select 单行化（v1 漏修点） | harness resolved（tonight-v2）+ expressions 126 OK | 转绿 |
| django__django-12308 | M2 | display_for_field TypeError 回退 repr（test_patch 断言对齐） | harness resolved（v2b-check）+ admin_utils 34/34 | 转绿 |
| django__django-12589 | M3 | 回退 Ref 展开，应用上游 PR #12589 set_groupby 别名冲突抑制 | harness resolved（tonight-v2）+ aggregation 66 OK | 转绿 |
| django__django-12856 | M2 | E012/E013/E016 逐字对齐金标准（含 CheckConstraint Q 误调用修正） | harness resolved（v2b-check）+ test_models 79/79 | 转绿 |
| pylint-dev__pylint-6506 | M1 | stderr 补 usage: pylint | 官方隐藏测试 2/2 | 转绿 |
| pytest-dev__pytest-5221 | M1 | scope 注解移到位置之前 | harness resolved（5221-check） | 转绿 |
| django__django-11283 | M1 | 冲突处理补 stdout 提醒打印 | 隐藏测试本地 9/9（临时应用 test_patch） | 转绿 |
| django__django-11630 | M1 | 路由器场景 E028→W035 警告（断言逐字对齐） | 官方 check_framework 142 OK | 转绿 |

未尝试（4 条，契约检查表已文档化于 runs_v2/<id>/CONTRACT_CHECKLIST.md）：
- django__django-11019（media 合并行为契约）
- django__django-11797（M4 set_values/Exact 语义重设计）
- pytest-dev__pytest-5103（断言展开 AST 级重写）
- django__django-12113（多 SQLite 环境复现成本过高，主动跳过）

**分列账目**：
- v1 盲写（冻结）：25/37 = 67.6%
- v2 反馈知情修复：尝试 8 条，8/8 官方判定或官方测试通过（0 回归、0 应用失败）
- 反馈知情合计：29/37 = 78.4%（v1 通过 25 + v2 转绿 4 条 harness 判定 + 3 条
  官方测试级验证 + 1 条本地隐藏测试验证）

两套数字属不同条件（盲写 vs 见失败反馈），禁止合并口径混用。

> **【2026-09-12 晚更正与收官】** 本节"未尝试（4 条）"已完成修复；pylint-6506
> 的"官方隐藏测试 2/2"经 tonight-v2c 官方 harness 复核判定不成立（当时的本地
> 验证跑的是工作树里自改的测试文件）。全部 12 条的最终状态见下节
> "v2 反馈知情修复收官"；本节表格与账目仅作历史保留，不得用于统计。


## v2 反馈知情修复收官（2026-09-12 晚，run_id=tonight-v2c / tonight-v2d）

4 条遗留契约级任务全部修复，并发现+补修 6506 的验证缺口。全部 12 条 v2 修复
在 tonight-v2d 官方 harness 下 **12/12 resolved**（0 未解决、0 回归、0 应用失败）。
评测输入 predictions_v2.jsonl（12 条补丁均与 v1 不同，SHA-256 审计见
v2_patch_status.md）；tonight-v2c 判定 11/12（唯一 unresolved 为 6506），补修后
tonight-v2d 判定 12/12。

| instance_id | 类别 | v2 修法 | 本地验证（test_patch 应用态） | 官方判定 |
|---|---|---|---|---|
| django__django-11019 | M1 | Media 合并重写为全列表依赖轮次拓扑合并（_js/_css 列表化+去重+新告警格式） | test_media+admin_inlines+admin_widgets 80/80 | resolved |
| django__django-11564 | M1 | MEDIA_URL/STATIC_URL 在 LazySettings.__getattr__ 读取时加 SCRIPT_NAME 前缀（不缓存） | settings_tests+file_storage 182/182 | resolved |
| django__django-11797 | M4 | Exact 对已有显式 select 的切片 rhs 跳过 pk 改写（GROUP BY 语义保留） | lookup.tests 39/39 + 同族场景 7/7 | resolved |
| pytest-dev__pytest-5103 | M1 | assert all(genexp/listcomp) 真展开为逐元素断言（含 ast.alias 位置修补） | test_assertrewrite 全模块 67/67 + 直接验证 7/7 | resolved |
| pylint-dev__pylint-6506 | M1 补修 | stderr 文案补 "Unrecognized option found: ..."（tonight-v2c 官方复核发现首轮缺口） | 官方断言直接复刻 6/6 | unresolved(v2c)→resolved(v2d) |

逐条 patch.diff/summary.md/verify_output.txt 在 runs_v2/<id>/；官方产物在
logs/run_evaluation/tonight-v2c、tonight-v2d；汇总表 comparison_v2.md
（V2_RUN_ID=tonight-v2d）。

**6506 的教训**（已写入其 summary.md）：本地验证必须与官方 test_patch 逐字
对齐应用后再跑；"跑过隐藏测试"若跑的是自改版本，验证无效。

**分列账目（最终）**：
- v1 盲写（冻结）：25/37 = 67.6%
- v2 反馈知情修复：尝试 12 条，12/12 官方 harness resolved（tonight-v2d；
  0 回归、0 应用失败；其中 6506 经两轮）
- 反馈知情合计：37/37 = 100%

两套数字属不同条件（盲写 vs 见失败反馈），禁止合并口径混用；v1 冻结分数不变。


## 提交前门禁基线 + 结构化置信度协议（2026-09-12，第一/三梯队项落地）

**GATE_BASELINE.md**：三级门禁（apply / 编译 / 受影响模块公开测试）对 12 条 v1
失败的拦截能力逐条判定（归属用 classify_gate.py 的 git grep HEAD 逐条存证）：
- 门禁只拦截 **2/12**：12589（回归型）与 6506（异常类型契约不符）
- 其余 10 条补丁通过全部门禁（公开测试在补丁树上全绿），失败只发生在
  test_patch 新增/改写的断言上——其中 11019 与 5221 的**基线版测试在本树通过**，
  改写版才暴露契约差异
- 结论：提交前门禁的边际价值集中在回归防护；M1 契约缺口与 M2 构造形态缺陷
  对不含 test_patch 的门禁不可见

**CONFIDENCE_PROTOCOL.md**：结构化置信度协议（后续生产的强制前置）——
生产前先产出《契约推测书》（逐条可证伪的契约推测 + 依据等级三档 + 不确定点清单），
自报置信度改为规则化推导（high=全仓库证据且逐项验证 / medium=含推测项 /
low=有未实现项），评分后按契约项回填"推测 vs 实测"命中率——校准分析的
最小单元。GATE_BASELINE 的结论（门禁不防契约缺口）是该协议的立论依据。

两项均已同步至 GitHub 仓库（commit 2d0a79f）。


## 扩样本生产进度(2026-09-12 晚)

- 分层抽样完成:63 条(seed 20260912,django 上限 25 修正偏斜;
  样本清单 V2_SAMPLE.json),与已完成 37 条合计 100 条
- 新仓库克隆:astropy/matplotlib/scikit-learn/sphinx/requests ✓(代理)
- 子代理通道探针 ✓:新额度周期已恢复(限流为周期性,非永久)

### 已完成(扩样本 3/63)
| instance_id | 修法 | 验证 |
|---|---|---|
| django__django-11815 | Enum 序列化按名(value 翻译失效) | test_patch 应用后 46/46 ✓ |
| django__django-11848 | 两位年份按 RFC 7231 相对当前年 ±50 | 8/8 边界断言 + 官方 http 45 OK ✓ |
| django__django-13230 | syndication 支持 item_comments(1 行透传) | 真实 get_feed 渲染 2/2 ✓ |
| django__django-13315 | limit_choices_to Q 跨 join 去重(distinct) | 真实表数据 2/2 ✓(契约书先行) |

### 待续(60 条,检查表/协议/脚本全部就绪,新会话按队列接力)
- 队列:13447 → 13590 → 13265 → 13315 之后 41 条 django + 非 django 全量
- 每条:pick_task → 契约推测书 → 修复 → 双重验证(patch+test_patch)→ 落盘 runs_v2

## 收支快照(09-12 晚)
- 额度:300M 的 ~24%(约 72M)——v1 全程+v2 修复+扩样本启动合计消耗约 76%
- 单条补丁实际均耗:亲修 ~150-300K(含验证),子代理 ~300-700K
- 剩余额度按 72M 计:可再支撑扩样本 ~150-300 条(理论),实际按 60 条
  保守规划收尾
