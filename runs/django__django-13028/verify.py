import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-13028")
sys.path.insert(0, r"C:\Users\mio\swe-experiment\runs\django__django-13028")

import django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["repro"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db.utils import NotSupportedError
from django.db import models
from repro.models import ProductMetaDataType, ProductMetaData

results = []

# 1. The ticket scenario: filtering with a model instance whose model has a
#    'filterable' field must NOT raise NotSupportedError.
meta = ProductMetaDataType(label="brand", filterable=False)
q = ProductMetaData.objects.filter(value="x", metadata_type=meta)
try:
    sql = str(q.query)
    print("ticket query compiles OK")
    results.append(("ticket scenario fixed", True))
except NotSupportedError as e:
    print("still broken:", e)
    results.append(("ticket scenario fixed", False))

# 2. Expressions that explicitly opt out are still rejected (unit-level: the
#    pipeline resolves F() to a column before the check, so test the check
#    directly on an expression instance).
class NonFilterableExpr(models.F):
    filterable = False

expr = NonFilterableExpr(models.Value(1))
try:
    ProductMetaData.objects.none().query.check_filterable(expr)
    print("expression opt-out: no error (unexpected)")
    results.append(("expression opt-out rejected", False))
except NotSupportedError:
    print("expression opt-out: NotSupportedError as expected")
    results.append(("expression opt-out rejected", True))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
