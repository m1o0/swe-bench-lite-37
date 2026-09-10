import sys, os, tempfile, pathlib
sys.path.insert(0, r"D:\mio\worktrees\django__django-11583")

import types
from django.utils import autoreload

# 1. A path with an embedded null byte must be skipped without raising.
null_path = "/tmp/some\x00path.py"
try:
    result = autoreload.iter_modules_and_files((), frozenset([null_path]))
    print("null byte: no exception, results =", result)
    print("null path excluded:", pathlib.Path(null_path) not in result)
except ValueError as e:
    print("null byte: STILL RAISES", e)
    sys.exit(1)

# 2. Real paths are returned as pathlib instances.
tmpdir = tempfile.mkdtemp()
real = os.path.join(tmpdir, "mod.py")
open(real, "w").write("")
result = autoreload.iter_modules_and_files((), frozenset([real]))
print("real path resolved:", len(result) == 1)
entry = next(iter(result))
print("real path is pathlib instance:", isinstance(entry, pathlib.Path))

ok = isinstance(entry, pathlib.Path) and len(result) == 1
print("ALL_OK" if ok else "NOT_FIXED")
