# django__django-11133 — HttpResponse doesn't handle memoryview objects

## Root cause analysis

`HttpResponse` (and other consumers of `HttpResponseBase.make_bytes`) failed on
`memoryview` content — e.g. a `BinaryField` value returned by PostgreSQL as a
`memoryview` — in two distinct ways, both in `django/http/response.py`:

1. **The `content` setter treated `memoryview` as an iterable of chunks**
   (`HttpResponse.content` setter). A `memoryview` has `__iter__` and is not
   `bytes`/`str`, so `hasattr(value, '__iter__') and not isinstance(value, (bytes, str))`
   routed it into the "consume iterator chunk by chunk" branch. Iterating a
   `memoryview` yields **integer byte values**, so each byte was rendered with
   `str(value).encode(charset)`, producing garbage like
   `b'771213267111110116101110116'` for `memoryview(b'My Content')`.
2. **`make_bytes()` fell through to `str(value)` for memoryview chunks**
   (`HttpResponseBase.make_bytes`). It only special-cased `bytes` and `str`,
   so any memoryview that reached it — via `HttpResponse.write(memoryview)`,
   `HttpResponse(iterable_containing_memoryview)`, or a
   `StreamingHttpResponse` chunk — was stringified, producing the repr
   `b'<memory at 0x...>'` (the exact symptom in the issue report).

Note that `force_bytes()` in `django/utils/encoding.py` already handles
`memoryview` via `bytes(s)`, but `make_bytes()` deliberately avoids
`force_bytes` (its docstring explains why: string content must be re-encoded
with the response charset, and `str` conversion must not happen first).

## What was changed and why

Two coordinated one-line changes in `django/http/response.py`, treating
`memoryview` as bytes-like everywhere response content is coerced:

1. `HttpResponseBase.make_bytes()`: `isinstance(value, bytes)` →
   `isinstance(value, (bytes, memoryview))`, returning `bytes(value)`. This is
   consistent with how `force_bytes` handles memoryview, fixes
   `HttpResponse.write(memoryview)`, memoryview items inside iterables, and
   memoryview chunks yielded by `StreamingHttpResponse.streaming_content`.
2. `HttpResponse.content` setter: `not isinstance(value, (bytes, str))` →
   `not isinstance(value, (bytes, memoryview, str))`, so a bare memoryview is
   no longer mistaken for an iterable of chunks and is instead converted as a
   single blob through `make_bytes()` → `HttpResponse(memoryview(b"My Content")).content`
   now returns `b'My Content'` (the expected behavior from the issue).

Bytes/str behavior is untouched (`bytes(value)` does not copy when `value` is
already `bytes`), and str content is still re-encoded with the response
charset, so no existing behavior changes.

## Verification

- Standalone repro (`repro.py`, run with the worktree checkout on `sys.path`):
  - before the fix: all memoryview cases fail (two failure modes above);
  - after the fix: all pass — issue case, `write(memoryview)`, memoryview in
    iterables, `StreamingHttpResponse` memoryview chunks, `serialize()`, and
    non-regression checks (str/bytes content, `charset='utf-16'` re-encoding).
- `python -m py_compile django/http/response.py` — OK.
- Targeted regression run of the worktree's `tests/httpwrappers` module
  (64 tests): OK before the fix, OK after the fix — no regressions.
  (`pytz`/`sqlparse`, unavailable in this environment, were stubbed for this
  offline check; full test suite intentionally not run.)

Known limitation (intentionally out of scope, keeps the fix minimal):
passing a *bare* `memoryview`/`bytes` as `StreamingHttpResponse` content is
outside the documented contract ("`streaming_content` should be an iterable
of bytestrings") and still gets iterated element-wise; memoryview *chunks*
inside an iterable are handled correctly by this fix.

## Files touched

- `D:\mio\worktrees\django__django-11133\django\http\response.py`
  (only file modified; 2 lines changed)

Helper scripts (not part of the fix, live in the runs directory):
`repro.py`, `run_httpwrappers_tests.py`, `search.py`.

## Confidence

**High** — the two failure modes were reproduced empirically before the fix
and eliminated after; the fix mirrors the existing memoryview handling in
`django.utils.encoding.force_bytes`; the entire `tests/httpwrappers` module
(64 tests) passes unchanged. The change is 2 lines and strictly widens the
accepted bytes-like types without altering str/bytes behavior.
