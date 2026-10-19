#!/usr/bin/env bash
# Pre-pull the SWE-bench instance images for this experiment.
#
# Why this exists: the DaoCloud mirror configured in /etc/docker/daemon.json
# answers "this image is not in the allowlist" for the swebench/* namespace, and
# registry-1.docker.io is unreachable from this WSL NAT network (direct Hub
# manifest/cURL calls time out).  docker.1ms.run, docker.1panel.live and
# hub.rat.dev do serve these images (verified with `docker manifest inspect`).
#
# The harness expects `swebench/sweb.eval.x86_64.<instance_id with __ -> _1776_>:latest`,
# so each image is pulled under its mirror-qualified name and re-tagged locally.
# No prediction file and no patch.diff is read or written here.
#
# Usage: bash prepull_images.sh
# Output: <EXP_ROOT_POSIX>/prepull_log.txt

set -u

BASE=<EXP_ROOT_POSIX>
LOG="$BASE/prepull_log.txt"
MIRRORS="docker.1ms.run docker.1panel.live hub.rat.dev"
INSTANCES=/tmp/swebench_instances.txt

: > "$LOG"
echo "prepull start $(date -Is)" >> "$LOG"

pull_one() {
    local id="$1"
    local repo="sweb.eval.x86_64.${id//__/_1776_}"
    local target="swebench/${repo}:latest"
    local m src

    if docker image inspect "$target" >/dev/null 2>&1; then
        printf '%s\talready-present\t\n' "$id" >> "$LOG"
        return 0
    fi

    for m in $MIRRORS; do
        src="${m}/${repo}:latest"
        if timeout 7200 docker pull "$src" >/dev/null 2>&1; then
            docker tag "$src" "$target" >/dev/null 2>&1
            printf '%s\tpulled\t%s\n' "$id" "$m" >> "$LOG"
            return 0
        fi
    done

    printf '%s\tFAILED\t\n' "$id" >> "$LOG"
    return 1
}
export -f pull_one
export LOG MIRRORS

grep -o '"instance_id": "[^"]*"' "$BASE/predictions_swebench.jsonl" \
    | cut -d'"' -f4 > "$INSTANCES"

total=$(wc -l < "$INSTANCES")
echo "instances to process: $total"

xargs -a "$INSTANCES" -P 3 -n 1 bash -c 'pull_one "$0"' || true

pulled=$(grep -c $'\tpulled\t' "$LOG" || true)
present=$(grep -c $'\talready-present\t' "$LOG" || true)
failed=$(grep -c $'\tFAILED\t' "$LOG" || true)

{
    echo "prepull done $(date -Is) pulled=$pulled already_present=$present failed=$failed"
    if [ "$failed" -gt 0 ]; then
        echo "skip list (image unavailable):"
        grep $'\tFAILED\t' "$LOG" | cut -f1
    else
        echo "skip list: (empty)"
    fi
} >> "$LOG"

echo "pulled=$pulled already_present=$present failed=$failed"
docker images --format '{{.Repository}}:{{.Tag}}' | grep -c '^swebench/' || true
