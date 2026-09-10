import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12286")

import django
from django.conf import settings
settings.configure(USE_I18N=True)
django.setup()

from django.core.checks.translation import check_language_settings_consistent

results = []


def check_with(lang_code, languages):
    settings.LANGUAGE_CODE = lang_code
    settings.LANGUAGES = languages
    errs = check_language_settings_consistent(None)
    return any(e.id == "translation.E004" for e in errs)


# 1. de-at with only de available -> no E004 (the bug)
results.append(("de-at with de -> no error",
                not check_with("de-at", [("de", "German"), ("en", "English")])))

# 2. de-at with nothing matching -> E004 stays
results.append(("de-at without de -> error",
                check_with("de-at", [("es", "Spanish"), ("en", "English")])))

# 3. exact match -> no error (unchanged behavior)
results.append(("exact es-ar -> no error",
                not check_with("es-ar", [("es-ar", "Argentinian Spanish"), ("en", "English")])))

# 4. en-us fallback still fine
results.append(("en-us fallback -> no error",
                not check_with("en-us", [("de", "German")])))

# 5. completely unknown base -> error
results.append(("unknown base -> error",
                check_with("xx-yyy", [("de", "German"), ("en", "English")])))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
