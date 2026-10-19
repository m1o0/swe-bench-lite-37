import json
import os

base = r"<EXP_ROOT>"
out = os.path.join(base, "pred_v2b_check.jsonl")

entries = []
for iid in ("django__django-12308", "django__django-12856"):
    p = os.path.join(base, "runs_v2", iid, "patch.diff")
    patch = open(p, encoding="utf-8").read()
    entries.append({
        "instance_id": iid,
        "model_name_or_path": "glm-5.3-zcode-campaign-v2b",
        "model_patch": patch,
    })

with open(out, "w", encoding="utf-8") as f:
    for e in entries:
        f.write(json.dumps(e) + "\n")
print("wrote", len(entries), "->", out)
