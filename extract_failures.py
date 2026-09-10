"""Extract compact failure evidence for every unresolved instance.

For each instance with resolved=false, print:
  * which FAIL_TO_PASS tests failed and which PASS_TO_PASS tests regressed
  * the first assertion/error lines found in test_output.txt

Usage: python extract_failures.py [instance_id ...]
With no arguments, all unresolved instances from the harness report are used.
"""
import json
import os
import re
import sys

BASE = r"<EXP_ROOT>"
RUN_ID = "tonight"
MODEL = "glm-5.3-zcode-campaign"
LOG_ROOT = os.path.join(BASE, "logs", "run_evaluation", RUN_ID, MODEL)
TOP_REPORT = os.path.join(BASE, "%s.%s.json" % (MODEL, RUN_ID))


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def snippet_for(instance_id, wanted):
    """Return up to 3 short evidence windows around assertion/error lines."""
    text = read_text(os.path.join(LOG_ROOT, instance_id, "test_output.txt"))
    if not text:
        return ["<no test_output.txt>"]
    lines = text.splitlines()
    keys = ["AssertionError", "Error:", "assert ", "FAILED", "Traceback (most recent call last)"]
    out = []
    seen = set()
    for idx, line in enumerate(lines):
        if any(k in line for k in keys):
            window = lines[idx: idx + 4]
            sig = " / ".join(w.strip()[:90] for w in window[:2])
            if sig in seen:
                continue
            seen.add(sig)
            out.append(" | ".join(w.strip()[:120] for w in window if w.strip()))
            if len(out) >= 3:
                break
    return out or ["<no assertion line matched>"]


def main():
    top = json.loads(read_text(TOP_REPORT))
    ids = sys.argv[1:] or [
        i for i in top.get("completed_ids", []) if i not in set(top.get("resolved_ids", []))
    ]

    for inst in ids:
        rec_data = read_text(os.path.join(LOG_ROOT, inst, "report.json"))
        rec = json.loads(rec_data)[inst] if rec_data else None
        print("=" * 100)
        print(inst, "resolved=%s patch_applied=%s"
              % (rec and rec.get("resolved"), rec and rec.get("patch_successfully_applied")))
        if rec:
            status = rec.get("tests_status") or {}
            f2p = status.get("FAIL_TO_PASS") or {}
            p2p = status.get("PASS_TO_PASS") or {}
            print("  FAIL_TO_PASS ok=%d fail=%d" % (len(f2p.get("success") or []), len(f2p.get("failure") or [])))
            for name in (f2p.get("failure") or [])[:5]:
                print("    F2P-FAIL:", name)
            print("  PASS_TO_PASS ok=%d fail=%d" % (len(p2p.get("success") or []), len(p2p.get("failure") or [])))
            for name in (p2p.get("failure") or [])[:5]:
                print("    P2P-REGRESSION:", name)
        for ev in snippet_for(inst, None):
            print("   evidence:", ev[:300])


if __name__ == "__main__":
    main()
