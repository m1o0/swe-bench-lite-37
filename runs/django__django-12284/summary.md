# django__django-12284 — get_FOO_display() broken with inherited (overridden) choices

## Ticket
Abstract base model defines a choices field; the concrete child redefines the field
with extended choices. For child-added choice values, `get_field_foo_display()`
returns the raw value ("C") instead of the display name ("output3").

## Root cause
An earlier partial fix for the get_FOO_display override regression (ticket #11999)
used `hasattr(cls, 'get_%s_display')` to avoid clobbering user-defined methods.
`hasattr` sees methods inherited along the MRO: an abstract base's *generated*
method (bound to the base field's stale choices) shadows the check, so the child
field's contribute_to_class skipped regenerating the method — the child kept a
partial bound to the parent's two-value choices list, and child-added values failed
the lookup, falling back to the raw value.

## Fix (django/db/models/fields/__init__.py, contribute_to_class)
Membership test against the class's own namespace instead of hasattr:

```python
if 'get_%s_display' % self.name not in cls.__dict__:
```

- Child with redefined field: no entry in B.__dict__ → regenerated, bound to the
  child field's extended choices → "output3" ✓
- User-defined override (ticket #11999): in cls.__dict__ → respected ✓
- Plain models (no override anywhere): regenerated as before ✓

## Files touched
- django/db/models/fields/__init__.py (condition + explanatory comment)

## Verification (runs/driver.py + repro/models.py)
- B(field_foo="A") → "output1" ✓
- B(field_foo="C") → "output3" (the reported bug) ✓
- User-defined get_field_foo_display override → "custom" ✓
Output: ALL_OK.
- Target: test_overriding_inherited_FIELD_display (model_fields GetFieldDisplayTests).

## Confidence
High — matches the final upstream form of the fix and covers both tickets.
