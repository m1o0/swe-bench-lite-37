import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12700")

import django
from django.conf import settings
settings.configure()
django.setup()

from django.views.debug import SafeExceptionReporterFilter
f = SafeExceptionReporterFilter()

MY_SETTING = {
    "foo": "value",
    "secret": "value",
    "token": "value",
    "something": [
        {"foo": "value"},
        {"secret": "value"},
        {"token": "value"},
    ],
    "else": [
        [
            {"foo": "value"},
            {"secret": "value"},
            {"token": "value"},
        ],
        [
            {"foo": "value"},
            {"secret": "value"},
            {"token": "value"},
        ],
    ],
}

cleansed = f.cleanse_setting("MY_SETTING", MY_SETTING)

results = []
results.append(("top secret", cleansed["secret"] == f.cleansed_substitute))
results.append(("top token", cleansed["token"] == f.cleansed_substitute))
results.append(("nested list dict secret", all(
    d["secret"] == f.cleansed_substitute for d in cleansed["something"]
    if "secret" in d
)))
results.append(("deep nested list-of-lists secret", all(
    d["secret"] == f.cleansed_substitute
    for lst in cleansed["else"] for d in lst if "secret" in d
)))
results.append(("non-sensitive untouched", cleansed["foo"] == "value"))
results.append(("list type preserved", isinstance(cleansed["something"], list)))
results.append(("nested list type preserved", isinstance(cleansed["else"], list)))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
