import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12983")

import django
from django.conf import settings
settings.configure()
django.setup()

from django.utils.text import slugify

results = []

# 1. The ticket's exact case.
out = slugify("___This is a test ---")
print("ticket case ->", repr(out))
results.append(("ticket case", out == "this-is-a-test"))

# 2. allow_unicode variant strips too.
out = slugify("___Ünïcode---", allow_unicode=True)
print("unicode case ->", repr(out))
results.append(("unicode strips", out == "ünïcode"))

# 3. Regular slugs unchanged.
results.append(("regular unchanged", slugify("This is a test") == "this-is-a-test"))

# 4. Interior underscores are NOT converted (only leading/trailing stripped).
results.append(("interior preserved", slugify("a_b -- c") == "a_b-c"))

# 5. All-dashes/underscores input -> empty string.
results.append(("all separators -> empty", slugify("---___") == ""))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
