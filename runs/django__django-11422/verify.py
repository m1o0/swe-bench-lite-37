import sys, tempfile, os, pathlib
sys.path.insert(0, r"D:\mio\worktrees\django__django-11422")

import types
from django.utils import autoreload

# The user's manage.py lives OUTSIDE the django repo; create a stand-in that exists.
tmpdir = tempfile.mkdtemp()
fake_script = os.path.join(tmpdir, "manage.py")
open(fake_script, "w").write("print('x')\n")

fake_main = types.ModuleType("__main__")
fake_main.__file__ = fake_script
fake_main.__spec__ = None
sys.modules["__main__"] = fake_main

files = autoreload.iter_all_python_module_files()
target = pathlib.Path(fake_script).resolve().absolute()
print("main script watched:", target in files)
print("ALL_OK" if target in files else "NOT_FIXED")
