import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-11564")

from unittest.mock import patch

from django.conf import settings
settings.configure(STATIC_URL="/static/", MEDIA_URL="/media/")
django_ready = True

from django.template.context_processors import static, media

class FakeRequest:
    def __init__(self, meta):
        self.META = meta

results = []

# 1. SCRIPT_NAME set -> prefixed
r = FakeRequest({"SCRIPT_NAME": "/dsn/"})
results.append(static(r)["STATIC_URL"] == "/dsn/static/")
results.append(media(r)["MEDIA_URL"] == "/dsn/media/")

# 2. SCRIPT_NAME without trailing slash -> normalized
r = FakeRequest({"SCRIPT_NAME": "/dsn"})
results.append(static(r)["STATIC_URL"] == "/dsn/static/")

# 3. No SCRIPT_NAME -> unchanged
r = FakeRequest({})
results.append(static(r)["STATIC_URL"] == "/static/")
results.append(media(r)["MEDIA_URL"] == "/media/")

# 4. SCRIPT_NAME identical to prefix -> no double prefix
r = FakeRequest({"SCRIPT_NAME": "/static/"})
results.append(static(r)["STATIC_URL"] == "/static/")

# 5. Empty url stays empty
with patch.object(settings, "STATIC_URL", ""):
    r = FakeRequest({"SCRIPT_NAME": "/dsn/"})
    results.append(static(r)["STATIC_URL"] == "")

print("ALL_OK" if all(results) else ("NOT_FIXED", results))
