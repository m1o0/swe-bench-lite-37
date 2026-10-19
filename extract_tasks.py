import pyarrow.parquet as pq
import json, os

t = pq.read_table(r"<EXP_ROOT>\data\swebench_lite_test.parquet")
rows = t.to_pylist()
outdir = r"<EXP_ROOT>\tasks"
os.makedirs(outdir, exist_ok=True)

keep = ("repo", "instance_id", "base_commit", "problem_statement", "version",
        "environment_setup_commit")
n = 0
for r in rows:
    with open(os.path.join(outdir, r["instance_id"] + ".json"), "w", encoding="utf-8") as f:
        json.dump({k: r[k] for k in keep}, f, ensure_ascii=False, indent=1)
    n += 1
print("saved", n, "task cards total")
