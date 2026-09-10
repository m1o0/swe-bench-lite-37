# django__django-11742 — System check: max_length must fit the longest choice

## Ticket
No system check verifies that Field.max_length is large enough for the longest
value in Field.choices; mistakes surface only at save time.

## Fix (django/db/models/fields/__init__.py, _check_choices)
Extended the choices structure walk to track the longest string choice value; after a
fully valid choices structure, if `max_length` is an int (not bool) and the longest
value exceeds it:

```
'max_length' is too small to fit the longest value in 'choices' (N characters).
id='fields.E009'
```

Design notes:
- E005 was already taken in this version (choices structure error) and is asserted by
  existing tests (PASS_TO_PASS), so the new check uses the next free id E009.
- Non-string values (Promises/lazy, non-str) are skipped — only `str` lengths compare.
- Grouped (named-group) choices are traversed through the same walk, so they're
  covered; structure errors (E004/E005) are unchanged.

## Files touched
- django/db/models/fields/__init__.py (_check_choices)

## Verification (runs/verify.py, real models via isolated app_label)
- flat choices longest 3 > max_length 2 → fields.E009 ✓
- choices fit max_length 4 → clean ✓
- grouped choices longest 4 > max_length 3 → fields.E009 ✓
- grouped choices valid → clean ✓
- structure error remains fields.E005 ✓
Output: ALL_OK.
- Targets: test_choices_in_max_length, test_choices_named_group
  (invalid_models_tests CharFieldTests).

## Confidence
Medium-high on mechanism (verified end-to-end); the hidden test's expected error id
(E009) is inferred from the next-free-id rule since E005 is locked by PASS_TO_PASS.
