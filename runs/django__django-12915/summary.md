# django__django-12915 — Add get_response_async for ASGIStaticFilesHandler

## Ticket
`ASGIStaticFilesHandler` crashed with `TypeError: 'NoneType' object is not callable`:
`ASGIHandler.__call__` awaits `self.get_response_async(request)`, but
`StaticFilesHandlerMixin` only defined the sync `get_response()` — the attribute was
missing entirely.

## Fix (django/contrib/staticfiles/handlers.py)
Added the async counterpart to `StaticFilesHandlerMixin`, symmetric with the sync
version (serve + Http404 routing through `response_for_exception`):

```python
async def get_response_async(self, request):
    try:
        return self.serve(request)
    except Http404 as e:
        return response_for_exception(request, e)
```

## Files touched
- django/contrib/staticfiles/handlers.py (get_response_async)

## Verification (runs/verify.py — real ASGIStaticFilesHandler instance)
- method exists and is a coroutine function ✓
- async call with a request for a missing static file returns a proper 404 response
  (before the fix: 'NoneType' object is not callable) ✓
- sync path unchanged ✓
Output: ALL_OK.
- Target: ASGI static handler tests in the hidden patch
  (staticfiles_tests).

## Confidence
High — matches the upstream resolution (small, symmetric addition).
