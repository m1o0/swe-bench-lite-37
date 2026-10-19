import pyarrow.parquet as pq

t = pq.read_table(r"<EXP_ROOT>\data\swebench_lite_test.parquet")
row = [r for r in t.to_pylist() if r["instance_id"] == "django__django-11001"][0]
print(row["test_patch"])
