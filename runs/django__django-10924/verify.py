import sys, os, tempfile
sys.path.insert(0, r"D:\mio\worktrees\django__django-10924")

import django
from django.conf import settings
settings.configure()
django.setup()

from django.db import models

tmpdir = tempfile.mkdtemp()
open(os.path.join(tmpdir, "somefile.txt"), "w").write("x")

def path_callable():
    return tmpdir

f = models.FilePathField(path=path_callable)
print("field.path is callable:", callable(f.path))

ff = f.formfield()
print("formfield path evaluated:", ff.path == tmpdir)
print("formfield class:", type(ff).__name__)
print("choices built from evaluated path:", any("somefile.txt" in c[0] for c in ff.choices))

# string path keeps working
f2 = models.FilePathField(path=tmpdir)
print("string path formfield:", f2.formfield().path == tmpdir)

# deconstruct passes callable through (for migration serialization)
name, path, args, kwargs = f.deconstruct()
print("deconstruct keeps callable:", kwargs.get("path") is path_callable)

results = [callable(f.path), ff.path == tmpdir, type(ff).__name__ == "FilePathField",
           any("somefile.txt" in c[0] for c in ff.choices), f2.formfield().path == tmpdir,
           kwargs.get("path") is path_callable]
print("ALL_OK" if all(results) else "NOT_FIXED")
