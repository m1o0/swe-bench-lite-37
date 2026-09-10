"""Verify every artifact in this repository against MANIFEST_v1.json.

The manifest records, for each of the 37 instances, the SHA-256 of the patch, the
write-up, the optional verification script and the two harness evidence files, plus
the hashes of the prediction files and the harness summary report. This script
recomputes all of them, so a reader does not have to trust the claim in README.md.

Usage:
    python verify_manifest.py [repo_root]

Exit codes:
    0  every recorded hash matches
    1  at least one file is missing or differs
    2  the manifest itself could not be read
"""

import hashlib
import json
import os
import sys

RUN_ID = "tonight"
MODEL = "glm-5.3-zcode-campaign"

# manifest key -> repository-relative path template
EVIDENCE = {
    "runs_patch.diff": "runs/{i}/patch.diff",
    "runs_summary.md": "runs/{i}/summary.md",
    "runs_verify.py": "runs/{i}/verify.py",
    "harness_report.json": "logs/run_evaluation/%s/%s/{i}/report.json" % (RUN_ID, MODEL),
    "harness_test_output.txt": "logs/run_evaluation/%s/%s/{i}/test_output.txt" % (RUN_ID, MODEL),
}
AGGREGATE = {
    "predictions.jsonl": "predictions.jsonl",
    "predictions_swebench.jsonl": "predictions_swebench.jsonl",
    "harness_summary_report": "%s.%s.json" % (MODEL, RUN_ID),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(root, "MANIFEST_v1.json")
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as exc:
        print("cannot read %s: %s" % (manifest_path, exc))
        return 2

    checked = 0
    missing = []
    mismatched = []
    skipped_absent = []

    for entry in manifest.get("instances", []):
        inst = entry["instance_id"]
        for key, template in EVIDENCE.items():
            expected = entry.get("sha256", {}).get(key)
            if expected is None:
                skipped_absent.append("%s (%s: not part of the artifact set)" % (inst, key))
                continue
            rel = template.format(i=inst)
            path = os.path.join(root, rel)
            if not os.path.isfile(path):
                missing.append(rel)
                continue
            actual = sha256_file(path)
            checked += 1
            if actual != expected:
                mismatched.append((rel, expected, actual))

    for key, rel in AGGREGATE.items():
        expected = manifest.get("artifacts", {}).get(key)
        if not expected:
            continue
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            missing.append(rel)
            continue
        actual = sha256_file(path)
        checked += 1
        if actual != expected:
            mismatched.append((rel, expected, actual))

    print("manifest : %s" % manifest_path)
    print("instances: %d (run_id=%s)" % (len(manifest.get("instances", [])), manifest.get("run_id")))
    print("hashes checked: %d" % checked)
    print("absent by design: %d  (e.g. verify.py is only present for 19/37)" % len(skipped_absent))
    print("dataset parquet sha256 (not committed, verify against the official download): %s"
          % manifest.get("dataset", {}).get("sha256"))

    if not missing and not mismatched:
        print("RESULT: OK - every recorded hash matches")
        return 0

    if missing:
        print("\nMISSING (%d):" % len(missing))
        for rel in missing:
            print("  %s" % rel)
    if mismatched:
        print("\nMISMATCH (%d):" % len(mismatched))
        for rel, expected, actual in mismatched:
            print("  %s\n    expected %s\n    actual   %s" % (rel, expected, actual))
    print("\nRESULT: FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
