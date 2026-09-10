import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12453")

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
)
django.setup()

import py_compile
py_compile.compile(r"D:\mio\worktrees\django__django-12453\django\db\backends\base\creation.py", doraise=True)
print("COMPILE_OK")

from django.db.backends.base.creation import BaseDatabaseCreation
import inspect
src = inspect.getsource(BaseDatabaseCreation.deserialize_db_from_string)
results = [("atomic wraps deserialization", "with transaction.atomic" in src)]

# Execute the method against a real connection: the atomic block runs and
# deserialization errors still propagate (mechanism unchanged for errors).
from django.db import connections
creation = connections["default"].creation
try:
    creation.deserialize_db_from_string('[{"model": "nope.nope", "pk": 1, "fields": {}}]')
    print("UNEXPECTED success on bogus payload")
    results.append(("bogus payload", False))
except Exception as e:
    print("bogus payload ->", type(e).__name__)
    results.append(("bogus payload propagates", type(e).__name__ == "DeserializationError"))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
