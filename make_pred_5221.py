import json
import os

base = r"<EXP_ROOT>"
patch_path = os.path.join(base, "runs_v2", "pytest-dev__pytest-5221", "patch.diff")
patch = open(patch_path, encoding="utf-8").read()
entry = {
    "instance_id": "pytest-dev__pytest-5221",
    "model_name_or_path": "glm-5.3-zcode-campaign-v2",
    "model_patch": patch,
}
out = os.path.join(base, "pred_5221_v2.jsonl")
with open(out, "w", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")
print("wrote", out, len(patch), "bytes")
