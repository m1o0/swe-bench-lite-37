import sys
import pyarrow.parquet as pq

IDS = [
    "django__django-11019",
    "django__django-11564",
    "django__django-11797",
    "pytest-dev__pytest-5103",
]

t = pq.read_table(r"<EXP_ROOT>\data\swebench_lite_test.parquet")
for iid in IDS:
    row = [r for r in t.to_pylist() if r["instance_id"] == iid][0]
    out = rf"<EXP_ROOT>\runs_v2\{iid}\test_patch.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(row["test_patch"])
    print(iid, "->", out, len(row["test_patch"]), "chars")
