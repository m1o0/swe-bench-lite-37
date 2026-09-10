import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12308")

import django
from django.conf import settings
settings.configure()
django.setup()

from django.contrib.admin.utils import display_for_field
from django.db import models

results = []

jf = models.JSONField()

# 1. dict value renders as valid JSON
out = display_for_field({"foo": "bar"}, jf, "-")
print("dict  ->", repr(out))
results.append(("dict as JSON", out == '{"foo": "bar"}'))

# 2. list value
out = display_for_field([1, 2, "x"], jf, "-")
print("list  ->", repr(out))
results.append(("list as JSON", out == '[1, 2, "x"]'))

# 3. None value -> empty display (untouched)
out = display_for_field(None, jf, "-")
results.append(("None -> empty display", out == "-"))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
