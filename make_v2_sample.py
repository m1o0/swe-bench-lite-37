"""分层随机抽样:v2 扩样本(目标 63 条,与已完成 37 条合计约 100)

规则:
- 排除已完成/已产出的 37 条
- django 上限 25 条(修正 v1 的 Django 偏斜)
- 其余按各仓库剩余数量比例分配
- 固定随机种子,可复现
"""
import pyarrow.parquet as pq
import json
import random
import collections

SEED = 20260912
TARGET = 63
DJANGO_CAP = 25
EXCLUDE = set()

# 已完成的 37 条(来自 predictions.jsonl)
for line in open(r"<EXP_ROOT>\predictions.jsonl", encoding="utf-8"):
    EXCLUDE.add(json.loads(line)["instance_id"])

t = pq.read_table(r"<EXP_ROOT>\data\swebench_lite_test.parquet")
rows = [r for r in t.to_pylist() if r["instance_id"] not in EXCLUDE]

by_repo = collections.defaultdict(list)
for r in rows:
    by_repo[r["repo"]].append(r["instance_id"])

random.seed(SEED)

sample = []

# django:先抽满上限
django_pool = sorted(by_repo.get("django/django", []))
random.shuffle(django_pool)
sample.extend(django_pool[:DJANGO_CAP])
sample_set = set(sample)
print("DEBUG django_pool:", len(django_pool), "| django taken:", len(sample),
      "| sample_set:", len(sample_set))

# 非 django:按剩余数量比例分配余量
others = {repo: ids for repo, ids in by_repo.items() if repo != "django/django"}
total_other = sum(len(v) for v in others.values())
quota = {}
allocated = 0
for repo, ids in sorted(others.items(), key=lambda kv: -len(kv[1])):
    q = round(TARGET - DJANGO_CAP) * len(ids) // total_other
    quota[repo] = min(q, len(ids))
    allocated += quota[repo]
# 余数补给剩余最多的仓库
short = (TARGET - DJANGO_CAP) - allocated
order = sorted(others, key=lambda r: -len(others[r]))
i = 0
while short > 0:
    repo = order[i % len(order)]
    if quota[repo] < len(others[repo]):
        quota[repo] += 1
        short -= 1
    i += 1

for repo, q in quota.items():
    pool = sorted(others[repo])
    random.shuffle(pool)
    taken = [x for x in pool if x not in sample_set][:q]
    sample.extend(taken)
    sample_set.update(taken)

out = {
    "seed": SEED,
    "target": TARGET,
    "django_cap": DJANGO_CAP,
    "by_repo_quota": {k: v for k, v in sorted(quota.items())},
    "sample": sorted(sample),
}
with open(r"<EXP_ROOT>\V2_SAMPLE.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

dist = collections.Counter(r["repo"] for r in rows if r["instance_id"] in sample_set)
print("sampled:", len(sample_set))
print(dict(dist.most_common()))
