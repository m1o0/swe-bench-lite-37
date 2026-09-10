"""Convert predictions.jsonl (key: "patch") into the layout expected by the
swebench 5.x harness (key: "model_patch").

Why this exists: swebench 5.0.2 reads predictions entries with the key
``model_patch`` (see swebench/harness/run_evaluation.py); the older
``patch`` key raises ``KeyError: 'model_patch'``.  Rather than editing the
original predictions.jsonl (produced by make_predictions.py), this script
writes a second file and leaves every patch byte-identical.

Safety checks:
  * reads the patch string from predictions.jsonl, never from a new source;
  * re-reads runs/<instance_id>/patch.diff from disk and compares SHA-256,
    so a divergence between the two is reported instead of silently graded.

Usage: python make_harness_predictions.py
Output: C:\\Users\\mio\\swe-experiment\\predictions_swebench.jsonl
"""
import hashlib
import json
import os

BASE = r"<EXP_ROOT>"
SRC = os.path.join(BASE, "predictions.jsonl")
DST = os.path.join(BASE, "predictions_swebench.jsonl")
RUNS = os.path.join(BASE, "runs")


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    count = 0
    mismatched = []
    missing = []
    with open(SRC, encoding="utf-8") as fin, open(DST, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            pred = json.loads(line)
            iid = pred["instance_id"]
            patch = pred["patch"]

            patch_path = os.path.join(RUNS, iid, "patch.diff")
            if not os.path.isfile(patch_path):
                missing.append(iid)
            else:
                with open(patch_path, encoding="utf-8") as f:
                    on_disk = f.read()
                if sha256(patch) != sha256(on_disk):
                    mismatched.append(iid)

            fout.write(
                json.dumps(
                    {
                        "instance_id": iid,
                        "model_name_or_path": pred["model_name_or_path"],
                        "model_patch": patch,
                    }
                )
                + "\n"
            )
            count += 1

    print("wrote %d predictions -> %s" % (count, DST))
    print("patches cross-checked against runs/<id>/patch.diff")
    print("  sha256 mismatches: %s" % (mismatched or "none"))
    print("  missing patch.diff: %s" % (missing or "none"))


if __name__ == "__main__":
    main()
