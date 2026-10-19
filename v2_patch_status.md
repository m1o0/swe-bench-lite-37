# v2 补丁状态（生成时间与 predictions_v2.jsonl 同步）

模式：v2-repair（v1 的 12 条失败）；条目数：12；输出：`predictions_v2.jsonl`（model_name_or_path=`glm-5.3-zcode-campaign-v2`）。

> v2 是**评测后修复条件**：其补丁可以使用 v1 的失败反馈。v2 结果与 v1 分数必须分列报告，不得合并统计（见 `V2_PLAN.md`）。

| instance_id | 与 v1 补丁的关系 | v2 sha256(前16) | v1 sha256(前16) |
|---|---|---|---|
| django__django-11001 | 已修改 | `c1e5dde83f59ecec` | `25d5ebcd1c78e8eb` |
| django__django-11019 | 已修改 | `c14b1f5c9e2834d9` | `d0e61122620494b7` |
| django__django-11283 | 已修改 | `ba3e575b1c072d20` | `c05c1fdb69697cd5` |
| django__django-11564 | 已修改 | `29497b5346fa5a7d` | `3f5a740e36fb8a21` |
| django__django-11630 | 已修改 | `68f9aa363051c271` | `ca4012ab2122f85f` |
| django__django-11797 | 已修改 | `1f4f559912f4b033` | `9cdcd76068e2908f` |
| django__django-12308 | 已修改 | `fb410730d716bc25` | `f577cbc106247b49` |
| django__django-12589 | 已修改 | `7fc2220405e9116a` | `29259a0d1f7293db` |
| django__django-12856 | 已修改 | `aa1dd528c79b36f0` | `07a6849b9940229b` |
| pylint-dev__pylint-6506 | 已修改 | `0deac2b78b637118` | `b9a490de709b29dc` |
| pytest-dev__pytest-5103 | 已修改 | `e72bf0042dab6f1d` | `0eb3c976dc44caa9` |
| pytest-dev__pytest-5221 | 已修改 | `e3ee5bfb35d5c17e` | `1bddfd690f056759` |

## 提醒

- 每条 v2 目录必须含：`patch.diff`、`summary.md`（根因/置信度/验证命令/已知不确定性/信息条件）、`verify_output.txt`；M1 类另需 `CONTRACT_CHECKLIST.md` 填好（模板见 `runs_v2/CHECKLIST_TEMPLATE.md`）。
- 若上表出现“与 v1 完全相同”，说明该条尚未真正修复，不应计入 v2 的修复率分母。
