#!/usr/bin/env bash
# Run the v2 (post-evaluation repair) harness evaluation in WSL.
#
# Prerequisites (already true after the v1 run):
#   * the 37 instance images are cached locally, so normally nothing is re-pulled;
#   * if pulls are needed again, the Windows-side proxy forwarder
#     (tools/port_forward.py) plus the dockerd drop-in (tools/docker-http-proxy.conf)
#     must be running, because registry-1.docker.io is unreachable from this WSL network.
#
# Usage: bash run_eval_v2.sh [run_id]
# Default run_id: tonight-v2

set -euo pipefail

BASE=<EXP_ROOT_POSIX>
RUN_ID="${1:-tonight-v2}"
PREDS="$BASE/predictions_v2.jsonl"

if [ ! -f "$PREDS" ]; then
    echo "missing $PREDS — run: python make_predictions_v2.py (on Windows)" >&2
    exit 1
fi

count=$(wc -l < "$PREDS")
echo "run_id=$RUN_ID predictions=$PREDS entries=$count"

cd "$BASE"
HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation \
    -d SWE-bench/SWE-bench_Lite \
    -s test \
    -p predictions_v2.jsonl \
    -id "$RUN_ID" \
    --max_workers 4

echo
echo "done. next: python analyze_v2.py   (on Windows) -> comparison_v2.md"
