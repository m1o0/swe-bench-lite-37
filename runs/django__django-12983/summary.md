# django__django-12983 — slugify() should strip dashes and underscores

## Ticket
`slugify("___This is a test ---")` returned `"___this-is-a-test-"`; the expected
output strips leading/trailing dashes and underscores: `"this-is-a-test"`.

## Fix (django/utils/text.py, slugify, 1 line + docstring)
Appended `.strip('-_')` to the final dash-collapse expression and updated the
docstring ("Convert spaces or repeated dashes to single dashes ... Also strip
leading and trailing whitespace, dashes, and underscores") — matching the upstream
resolution of this ticket.

Semantics: interior underscores are NOT converted (only leading/trailing ones are
stripped); repeated interior dashes/spaces still collapse to a single dash.

## Files touched
- django/utils/text.py (slugify)

## Verification (runs/verify.py)
- ticket case → 'this-is-a-test' ✓
- allow_unicode=True variant also strips ✓
- regular slug unchanged ✓
- interior underscore preserved as underscore ✓
- all-separator input → '' ✓
Output: ALL_OK.

## Confidence
High.
