"""Usage: python pick_task.py <repo_name> <instance_id>
repo_name: django | sympy | pylint | pytest (subdir under D:\\mio\\repos)"""
import json, subprocess, sys

repo, iid = sys.argv[1], sys.argv[2]
card = json.load(open(rf"<EXP_ROOT>\tasks\{iid}.json", encoding="utf-8"))
wt = rf"D:\mio\worktrees\{iid}"
print("base_commit:", card["base_commit"])
r = subprocess.run(
    ["git", "-C", rf"D:\mio\repos\{repo}", "worktree", "add", wt, card["base_commit"]],
    capture_output=True, text=True)
print((r.stdout + r.stderr)[-300:])
print("WORKTREE_READY" if r.returncode == 0 else "WORKTREE_FAILED")
