# django__django-11620 — Http404 in path converter to_python should give a technical 404 when DEBUG=True

## Root cause (two-stage failure chain, found via traceback)
1. A converter's `to_python()` raising `Http404` propagates correctly out of URL
   resolution to the request handler, which (DEBUG=True) correctly calls
   `debug.technical_404_response()`.
2. `technical_404_response()` re-resolves `request.path` (django/views/debug.py,
   `resolve(request.path)`) to display the "raising view name", catching only
   `Resolver404`. The converter raises plain `Http404` again during this
   re-resolution; `Resolver404` is a *subclass* of `Http404`, so
   `except Resolver404` does not catch it — the debug page itself blows up and the
   request collapses into a 500 "A server error occurred".

Reproduced on the unpatched tree with runs/repro.py: converter raising Http404 →
traceback through debug.py:485 → Http404 escapes (see repro output).

## Fix (django/views/debug.py, 2 edits)
- Import Http404.
- `except Resolver404: pass` → additionally catch `Http404` (render the debug page
  without the "raising view name" in that case).

With this, `to_python()` Http404 yields the technical 404 page in DEBUG (verified:
status 404, "Page not found" debug page rendered), matching the ticket's request to
let converters use get_object_or_404-style behavior. Plain `ValueError` semantics
(try the next pattern) are unchanged.

## Files touched
- django/views/debug.py (import + except clause)

## Verification
- runs/repro.py on patched tree: status 404, technical page rendered (was: unhandled
  Http404 → 500 before the fix). Output: "status: 404 / technical 404 page: True".
- Target: test_technical_404_converter_raise_404 (view_tests DebugViewTests).

## Confidence
High — end-to-end repro verified both directions of the bug.
