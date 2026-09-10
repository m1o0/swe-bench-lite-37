# django__django-12184 — Optional URL params crash some view functions

## Ticket (Django 3.0 regression)
`re_path(r'^module/(?P<format>(html|json|xml))?/?$', views.modules)` with
`def modules(request, format='html')` crashes with
`TypeError: modules() takes from 1 to 2 positional arguments but 3 were given`
when the optional named group does not participate in the match (/module/).

## Root cause (django/urls/resolvers.py, RegexPattern.match)
The None-filter for `groupdict()` was already present, but the positional fallback
checked the FILTERED kwargs: when every named group is None (optional group absent),
`kwargs` becomes `{}` and the code falls back to `match.groups()` — passing the
pattern's anonymous groups as positional arguments (view gets garbage positionals).

## Fix (one word)
The fallback must key off whether the pattern HAS named groups:

```python
args = () if match.groupdict() else match.groups()
```

With named groups present, non-participating ones are simply omitted from kwargs and
the view's own defaults apply (`view(request)` → format='html'). Patterns without
named groups keep the positional behavior (verified unchanged).

## Files touched
- django/urls/resolvers.py (RegexPattern.match, 1 line + comment)

## Verification (runs/verify.py, live Client requests)
- /module/ (optional group absent) → 200, view default 'html' applies (was TypeError)
- /module/json/ → format='json' passed ✓
- /plain/ unchanged ✓
- anonymous positional groups (`pos/abc/123/`) still positional ✓
Output: ALL_OK.

## Confidence
High — direct behavioral reproduction before/after; matches upstream resolution.
