import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-11630")

import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DATABASE_ROUTERS=[],
)
django.setup()

from django.core import checks

# Two models in DIFFERENT apps sharing a db_table (via isolated test apps).
from django.apps import registry
from django.db import models

results = []

class MetaA:
    pass

# Build two isolated app registries manually is complex; instead call the
# check function with a synthetic model set by monkeypatching apps.get_models.
class ModelA:
    class _meta:
        label = "app1.Thing"
        db_table = "shared_table"
        managed = True
        proxy = False
        indexes = []
        constraints = []
    @classmethod
    def check(cls, **kwargs):
        return []

class ModelB:
    class _meta:
        label = "app2.Thing"
        db_table = "shared_table"
        managed = True
        proxy = False
        indexes = []
        constraints = []
    @classmethod
    def check(cls, **kwargs):
        return []

class ModelC:
    class _meta:
        label = "app1.Other"
        db_table = "shared_table"
        managed = True
        proxy = False
        indexes = []
        constraints = []
    @classmethod
    def check(cls, **kwargs):
        return []

real_get_models = checks_models_get_models = None
import django.core.checks.model_checks as mc

orig = mc.apps.get_models
try:
    # cross-app clash, routers installed -> no E028
    settings.DATABASE_ROUTERS = ["some.Router"]
    mc.apps.get_models = lambda *a, **k: iter([ModelA, ModelB])
    errs = [e for e in mc.check_all_models() if e.id == "models.E028"]
    results.append(("cross-app + routers -> skipped", len(errs) == 0))

    # cross-app clash, NO routers -> E028 present
    settings.DATABASE_ROUTERS = []
    mc.apps.get_models = lambda *a, **k: iter([ModelA, ModelB])
    errs = [e for e in mc.check_all_models() if e.id == "models.E028"]
    results.append(("cross-app without routers -> error", len(errs) == 1))

    # same-app clash, routers installed -> E028 present
    settings.DATABASE_ROUTERS = ["some.Router"]
    mc.apps.get_models = lambda *a, **k: iter([ModelA, ModelC])
    errs = [e for e in mc.check_all_models() if e.id == "models.E028"]
    results.append(("same-app + routers -> error", len(errs) == 1))
finally:
    mc.apps.get_models = orig

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
