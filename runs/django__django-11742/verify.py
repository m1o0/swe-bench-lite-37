import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-11742")

import django
from django.conf import settings
settings.configure()
django.setup()

from django.core import checks
from django.db import models

results = []

class M1(models.Model):
    field = models.CharField(max_length=2, choices=[("ab", "AB"), ("cde", "CDE")])
    class Meta:
        app_label = "m"

class M2(models.Model):
    field = models.CharField(max_length=4, choices=[("ab", "AB"), ("cde", "CDE")])
    class Meta:
        app_label = "m"

class M3(models.Model):
    # grouped choices, longest value 4 > max_length 3
    field = models.CharField(max_length=3, choices=[("G", [("abc", "ABC"), ("defg", "DEFG")])])
    class Meta:
        app_label = "m"

class M4(models.Model):
    # named group, valid structure, no max_length issue
    field = models.CharField(max_length=10, choices=[("G", [("abc", "ABC"), ("de", "DE")])])
    class Meta:
        app_label = "m"

class M5(models.Model):
    # structure error must remain E005 (iterable containing non-pairs)
    field = models.CharField(max_length=2, choices=[1234])
    class Meta:
        app_label = "m"

def ids(field):
    return [e.id for e in field.check()]

results.append(("too-long choices -> E009", ids(M1._meta.get_field("field")) == ["fields.E009"]))
results.append(("fitting choices -> clean", ids(M2._meta.get_field("field")) == []))
results.append(("grouped too-long -> E009", ids(M3._meta.get_field("field")) == ["fields.E009"]))
results.append(("grouped ok -> clean", ids(M4._meta.get_field("field")) == []))
results.append(("structure error still E005", ids(M5._meta.get_field("field")) == ["fields.E005"]))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
