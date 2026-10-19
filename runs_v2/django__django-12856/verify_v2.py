import sys
sys.path.insert(0, "/mnt/d/mio/worktrees/django__django-12856")
sys.path.insert(0, "<EXP_ROOT_POSIX>/runs_v2/django__django-12856")

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["repro"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models
from repro.models import Child, M2MModel

results = []


def run(model, fields, cname):
    c = models.UniqueConstraint(fields=fields, name=cname)
    return [e for e in c.check(model) if e.id.startswith("models.E0")]


# 1. missing field -> E012 exact
errs = run(Child, ["missing_field"], "u_missing")
e = errs[0] if errs else None
results.append(("missing -> E012 exact msg", e is not None and e.id == "models.E012" and e.msg == (
    "'constraints' refers to the nonexistent field 'missing_field'."
)))

# 2. non-local (MTI parent field) -> E016 exact msg + hint
errs = run(Child, ["field1"], "u_nonlocal")
e = errs[0] if errs else None
results.append(("non-local -> E016 exact", e is not None and e.id == "models.E016" and e.msg == (
    "'constraints' refers to field 'field1' which is not local to model 'Child'."
) and e.hint == "This issue may be caused by multi-table inheritance."))

# 3. m2m -> E013 EXACT message (from test_patch)
errs = run(M2MModel, ["m2m"], "u_m2m")
e = errs[0] if errs else None
results.append(("m2m -> E013 exact msg", e is not None and e.id == "models.E013" and e.msg == (
    "'constraints' refers to a ManyToManyField 'm2m', but "
    "ManyToManyFields are not permitted in 'constraints'."
)))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
