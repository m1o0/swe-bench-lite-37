import sys
sys.path.insert(0, "/mnt/d/mio/worktrees/django__django-12308")

import django
from django.conf import settings
settings.configure()
django.setup()

from django.contrib.admin.utils import display_for_field
from django.db import models

results = []
jf = models.JSONField()

tests = [
    ({'a': {'b': 'c'}}, '{"a": {"b": "c"}}'),
    (['a', 'b'], '["a", "b"]'),
    ('a', '"a"'),
    ({('a', 'b'): 'c'}, "{('a', 'b'): 'c'}"),  # Invalid JSON -> repr fallback
    (None, '-'),
]
for value, expected in tests:
    out = display_for_field(value, jf, '-')
    print(repr(value), '->', repr(out))
    results.append(out == expected)

print(results)
print("ALL_OK" if all(results) else "NOT_FIXED")
