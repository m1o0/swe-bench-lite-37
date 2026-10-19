import pyarrow.parquet as pq
import json, sys

iid = sys.argv[1]
t = pq.read_table(r"<EXP_ROOT>\data\swebench_lite_test.parquet")
row = [r for r in t.to_pylist() if r["instance_id"] == iid][0]
print("FAIL_TO_PASS:", row["FAIL_TO_PASS"])
print("PASS_TO_PASS count:", len(json.loads(row["PASS_TO_PASS"])) if row["PASS_TO_PASS"] else 0)
tests = json.loads(row["FAIL_TO_PASS"]) if row["FAIL_TO_PASS"] else []
print("first test:", tests[0] if tests else "-")
