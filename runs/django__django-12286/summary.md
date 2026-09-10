# django__django-12286 — translation.E004 shouldn't fire for sublanguages with an available base language

## Ticket
`LANGUAGE_CODE = "de-at"` raises `translation.E004` ("not in the LANGUAGES setting")
even though only `de` exists — while the documented runtime behavior is to fall back
to the base language. `es-ar` worked only because Django ships it.

## Fix (django/core/checks/translation.py, check_language_settings_consistent)
When LANGUAGE_CODE itself is absent from the (LANGUAGES + en-us) set, accept its base
language (the part before the first '-'):

```python
base_language = settings.LANGUAGE_CODE.split('-')[0]
if base_language not in available_tags:
    return [E004]
```

Exact matches and the en-us fallback are untouched; genuinely unknown bases still
error.

## Files touched
- django/core/checks/translation.py (check_language_settings_consistent)

## Verification (runs/verify.py)
- de-at with [de, en] → no error ✓ (the bug)
- de-at with [es, en] → E004 stays ✓
- exact es-ar match → no error ✓ (unchanged)
- en-us without LANGUAGES entry → no error ✓ (unchanged)
- xx-yyy unknown → E004 ✓
Output: ALL_OK.

## Confidence
High — matches the upstream resolution of this ticket.
