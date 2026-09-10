# django__django-11630 — 输出契约检查表（M1：级别 + 分支）

> v1 失败证据（事后信息，见 `../../comparison.md`）：F2P 0/2，
> 一个用例期望"不产生任何检查消息"，另一个期望"产生 Warning(level=30)"；
> v1 在放行处报了 Warning、在应告警处报了 Error，两个方向都反了。
> 填写纪律：不读 `test_patch`。

## 必须确定的分支 × 级别矩阵

| 场景 | 期望结果（无消息 / Warning / Error） | 依据来源 |
|---|---|---|
| 同一 app 内两张表同名，未安装 database router | | ticket / 既有检查器写法 |
| 同一 app 内两张表同名，**已安装** router | | |
| 跨 app 同名，未安装 router | | |
| 跨 app 同名，**已安装** router（v1 在此方向失败） | | |

补充项：

| 项 | 问题 | 依据来源 | 结论 |
|---|---|---|---|
| 级别数值 | Warning 是 `level=30` 吗？ | Django 检查框架既有用法 | |
| 消息 id | 检查项 id（如 `models.E0xx` / `models.W0xx`） | 既有 `db_table` 检查 | |
| 是否可屏蔽 | 是否受 `SILENCED_SYSTEM_CHECKS` 影响 | 框架既有行为 | |

## 必做验证

1. 用 `Model.check(databases=...)` 直接断言返回的消息列表（id + level + msg），四个分支全覆盖。
2. 断言**空列表**的分支必须显式测（v1 漏了这个方向）。
3. 回归：`check_framework.test_model_checks` 模块跑通。
4. 命令与原始输出写入 `verify_output.txt`。

## 已知不确定性

- 若 router 分支的确切语义无法从仓库证据确定，必须在 summary 中标注为不确定。
