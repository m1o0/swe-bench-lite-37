import asyncio
import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12915")
sys.path.insert(0, r"C:\Users\mio\swe-experiment\runs\django__django-12915")

import django
from django.conf import settings
settings.configure(
    DEBUG=False,
    INSTALLED_APPS=["django.contrib.staticfiles"],
    STATIC_URL="/static/",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
)
django.setup()

from django.http import HttpResponse

urlpatterns = []


from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
import inspect

results = []

# 1. The method exists and is a coroutine function.
handler = ASGIStaticFilesHandler(lambda scope, receive, send: None)
results.append(("get_response_async exists", hasattr(handler, "get_response_async")))
results.append(("is coroutine function", inspect.iscoroutinefunction(handler.get_response_async)))

# 2. Direct call: async path returns a served (404 for missing file) response
#    instead of crashing with 'NoneType' object is not callable.
from django.test import RequestFactory
request = RequestFactory().get("/static/whatever.css")


async def run():
    return await handler.get_response_async(request)


resp = asyncio.new_event_loop().run_until_complete(run())
print("async response status:", resp.status_code)
results.append(("async path returns 404 response", resp.status_code == 404))

# 3. Sync get_response unchanged.
resp2 = handler.get_response(request)
results.append(("sync path still works", resp2.status_code == 404))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
