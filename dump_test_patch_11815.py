import pyarrow.parquet as pq

t = pq.read_table(r"<EXP_ROOT>\data\swebench_lite_test.parquet")
row = [r for r in t.to_pylist() if r["instance_id"] == "django__django-11815"][0]
open(r"<EXP_ROOT>\runs_v2\django__django-11815\test_patch_11815.diff", "w", encoding="utf-8").write(row["test_patch"])
print("written", len(row["test_patch"]), "chars")
