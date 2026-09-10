import sys, types
sys.path.insert(0, r"D:\mio\worktrees\django__django-12125")

import django
from django.conf import settings
settings.configure()
django.setup()

# Synthetic module with a nested field class, as in the ticket.
mod = types.ModuleType("testmod")
exec("from django.db import models\n"
     "class Outer:\n"
     "    class Inner(models.CharField):\n"
     "        pass\n", mod.__dict__)
sys.modules["testmod"] = mod

from django.db.migrations.serializer import serializer_factory

results = []

# 1. Field INSTANCE of an inner class deconstructs and serializes with full path.
inst = mod.Outer.Inner(max_length=20)
s, imports = serializer_factory(inst).serialize()
print("field instance:", s, "|", imports)
results.append(("field path", "testmod.Outer.Inner(max_length=20)" == s))
results.append(("field import", imports == {"import testmod"}))

# 2. The inner CLASS itself (e.g. enum= kwarg) via TypeSerializer.
s, imports = serializer_factory(mod.Outer.Inner).serialize()
print("inner class:", s, "|", imports)
results.append(("class path", "testmod.Outer.Inner" == s))
results.append(("class import", imports == {"import testmod"}))

# 3. Top-level class still serializes normally.
s, imports = serializer_factory(mod.Outer).serialize()
print("outer class:", s, "|", imports)
results.append(("outer class", "testmod.Outer" == s))

print("ALL_OK" if all(results) else "NOT_FIXED")
