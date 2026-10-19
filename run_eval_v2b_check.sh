#!/usr/bin/env bash
set -euo pipefail
cd <EXP_ROOT_POSIX>
HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation \
    -d SWE-bench/SWE-bench_Lite \
    -s test \
    -p pred_v2b_check.jsonl \
    -id v2b-check \
    --max_workers 2
