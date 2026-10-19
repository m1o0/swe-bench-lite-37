import sys
sys.path.insert(0, "/mnt/d/mio/worktrees/django__django-11630")

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

import django.core.checks.model_checks as mc
from django.core import checks

results = []


class Model1:
    class _meta:
        label = "repro.Model1"
        db_table = "test_table"
        managed = True
        proxy = False
        indexes = []
        constraints = []

    @classmethod
    def check(cls, **kwargs):
        return []


class Model2:
    class _meta:
        label = "repro.Model2"
        db_table = "test_table"
        managed = True
        proxy = False
        indexes = []
        constraints = []

    @classmethod
    def check(cls, **kwargs):
        return []


def run_checks():
    orig = mc.apps.get_models
    mc.apps.get_models = lambda *a, **k: iter([Model1, Model2])
    try:
        return [e for e in mc.check_all_models() if getattr(e, "id", "") in ("models.E028", "models.W035")]
    finally:
        mc.apps.get_models = orig


# 1. routers installed -> W035 warning, exact msg + hint
settings.DATABASE_ROUTERS = ["some.Router"]
errs = run_checks()
w = [e for e in errs if e.id == "models.W035"]
results.append(("routers -> W035 present", len(w) == 1))
if w:
    results.append(("W035 msg exact", w[0].msg == (
        "db_table 'test_table' is used by multiple models: "
        "repro.Model1, repro.Model2."
    )))
    results.append(("W035 hint exact", w[0].hint == (
        "You have configured settings.DATABASE_ROUTERS. Verify that "
        "repro.Model1, repro.Model2 are correctly routed to separate databases."
    )))
    results.append(("W035 level 30", w[0].level == 30))
else:
    results.extend([("W035 msg exact", False), ("W035 hint exact", False), ("W035 level 30", False)])

# 2. no routers -> E028 error (base behavior)
settings.DATABASE_ROUTERS = []
errs = run_checks()
results.append(("no routers -> E028", any(x.id == "models.E028" for x in errs)))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
