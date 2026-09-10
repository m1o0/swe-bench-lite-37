import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12856")
sys.path.insert(0, r"C:\Users\mio\swe-experiment\runs\django__django-12856")

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["repro"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from repro.models import M1, M2, M3, M4

results = []

errs = [e.id for e in M1.check()]
results.append(("missing field -> E012", "models.E012" in errs))
msgs = [e.msg for e in M1.check() if e.id == "models.E012"]
results.append(("missing field message", any("missing_field" in m for m in msgs)))

errs = [e.id for e in M2.check()]
results.append(("m2m field -> E012", "models.E012" in errs))
msgs = [e.msg for e in M2.check() if e.id == "models.E012"]
results.append(("m2m message", any("ManyToManyField" in m for m in msgs)))

errs = [e.id for e in M3.check()]
results.append(("valid constraint -> no E012", "models.E012" not in errs))

errs = [e.id for e in M4.check()]
results.append(("non-local field -> E012", "models.E012" in errs))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
