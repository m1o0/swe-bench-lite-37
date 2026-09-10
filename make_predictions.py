"""Generate SWE-bench predictions.jsonl from runs/<instance_id>/patch.diff
Usage: python make_predictions.py
Output: C:\\Users\\mio\\swe-experiment\\predictions.jsonl
"""
import json
import os
import glob

runs_dir = r"<EXP_ROOT>\runs"
out_path = r"<EXP_ROOT>\predictions.jsonl"

preds = []
skipped = []
# The experiment scope is the 37 instances listed in RESULTS.md.  This run
# directory was created later and is intentionally excluded from the formal
# denominator until it is explicitly added to that list.
excluded_ids = {"django__django-12747"}
for d in sorted(glob.glob(os.path.join(runs_dir, "*"))):
    iid = os.path.basename(d)
    if iid in excluded_ids:
        skipped.append((iid, "outside declared 37-instance experiment scope"))
        continue
    patch_path = os.path.join(d, "patch.diff")
    if not os.path.isfile(patch_path):
        skipped.append((iid, "no patch.diff"))
        continue
    with open(patch_path, encoding="utf-8") as f:
        patch = f.read()
    if not patch.strip():
        skipped.append((iid, "empty patch"))
        continue
    preds.append({
        "instance_id": iid,
        "model_name_or_path": "glm-5.3-zcode-campaign",
        "patch": patch,
    })

with open(out_path, "w", encoding="utf-8") as f:
    for p in preds:
        f.write(json.dumps(p) + "\n")

print("wrote %d predictions -> %s" % (len(preds), out_path))
for iid, reason in skipped:
    print("skipped %s: %s" % (iid, reason))
