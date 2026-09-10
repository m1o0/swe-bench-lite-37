import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12708")

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["repro"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

import py_compile
py_compile.compile(r"D:\mio\worktrees\django__django-12708\django\db\backends\base\schema.py", doraise=True)
print("COMPILE_OK")

from django.db import models, connection

from repro.models import Thing

results = []
editor = connection.schema_editor()
with editor:
    editor.create_model(Thing)

cols = ["field1", "field2"]

# Both a unique constraint and a plain index exist on the same columns.
uniq = editor._constraint_names(Thing, cols, unique=True)
idx = editor._constraint_names(Thing, cols, index=True, unique=False)
results.append(("setup: unique exists", len(uniq) >= 1))
results.append(("setup: index exists", len(idx) >= 1))

# Ticket scenario: remove ONLY the index_together (pre-fix: ValueError
# "Found wrong number (2) of constraints").
try:
    editor.alter_index_together(Thing, {("field1", "field2")}, set())
    results.append(("index_together removal succeeds", True))
except ValueError as e:
    print("crash:", e)
    results.append(("index_together removal succeeds", False))

# The unique constraint must survive.
uniq = editor._constraint_names(Thing, cols, unique=True)
results.append(("unique survives", len(uniq) == 1))
idx = editor._constraint_names(Thing, cols, index=True, unique=False)
results.append(("plain index removed", len(idx) == 0))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
