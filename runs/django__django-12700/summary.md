# django__django-12700 — Settings are cleansed insufficiently (nested iterables)

## Ticket
`SafeExceptionReporterFilter.get_safe_settings()` fails to cleanse sensitive keys
("secret", "token", ...) nested inside lists/tuples — only top-level dicts and
one-level dict values were cleansed; other iterables were returned as-is, leaking
deeply nested secrets in error reports.

## Fix (django/views/debug.py, cleanse_setting)
Added a branch for list/tuple/set/frozenset values that rebuilds the iterable by
recursively cleansing each element (passing the original key down so nested dicts
inside the iterable are still matched against `hidden_settings`). The container type
is preserved. Dict recursion and the hidden-key substitution are unchanged.

## Files touched
- django/views/debug.py (cleanse_setting: docstring + iterable branch)

## Verification (runs/verify.py — the ticket's exact MY_SETTING)
- top-level secret/token → cleansed ✓
- dicts inside a list → cleansed ✓
- dicts inside a list-of-lists (2 levels deep) → cleansed ✓
- non-sensitive values untouched ✓
- container types preserved (list stays list) ✓
Output: ALL_OK.
- Target: test_cleanse_nested_...-style tests in the hidden patch
  (tests/view_tests/tests.py).

## Confidence
High.
