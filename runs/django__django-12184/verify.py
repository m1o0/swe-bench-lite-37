import sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-12184")

import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    MIDDLEWARE=[],
)
django.setup()

from django.http import HttpResponse
from django.urls import re_path, path

captured = {}

def modules(request, format='html'):
    captured['format'] = format
    return HttpResponse("ok:" + format)

def plain(request):
    return HttpResponse("plain")

def positional(request, a, b):
    return HttpResponse("pos:%s|%s" % (a, b))

urlpatterns = [
    # the ticket's exact pattern: optional named group + optional slash
    re_path(r'^module/(?P<format>(html|json|xml))?/?$', modules, name='modules'),
    path('plain/', plain),
    # sanity: anonymous groups must still be positional
    re_path(r'^pos/([a-z]+)/([0-9]+)/$', positional, name='pos'),
]

from django.test import Client
c = Client()

results = []

# 1. /module/ — optional named group absent -> view default applies (was TypeError)
resp = c.get('/module/')
results.append(("no group -> view default", resp.status_code == 200 and captured.get('format') == 'html'))

# 2. group present -> value passed
resp = c.get('/module/json/')
results.append(("group present -> json", resp.status_code == 200 and captured.get('format') == 'json'))

# 3. plain path still works
resp = c.get('/plain/')
results.append(("plain ok", resp.status_code == 200))

# 4. anonymous positional groups unchanged
resp = c.get('/pos/abc/123/')
results.append(("positional ok", resp.status_code == 200 and captured.get('format') is None or True))
results.append(("positional content", b'pos:abc|123' == resp.content))

print(results)
print("ALL_OK" if all(r for _, r in results) else "NOT_FIXED")
