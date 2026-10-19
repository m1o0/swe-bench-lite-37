#!/usr/bin/env bash
# usage: bash run_wsl_tests.sh <worktree_name> <test_labels...>
WT="/mnt/d/mio/worktrees/$1"
cd "$WT/tests" || { echo "NO_TESTS_DIR"; exit 1; }
shift
export PYTHONPATH="$WT"
export DJANGO_SETTINGS_MODULE="test_sqlite"
python3 runtests.py "$@" -v 1 --noinput --parallel 1 2>&1 | tail -40
