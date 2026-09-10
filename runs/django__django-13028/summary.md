# django__django-13028 — Queryset raises NotSupportedError when RHS has filterable=False attribute

## Ticket
A model with a field named `filterable` (BooleanField, default False) breaks every
filter that passes one of its instances as a value:
`ProductMetaData.objects.filter(metadata_type=<instance>)` → NotSupportedError
"ProductMetaDataType is disallowed in the filter clause."

## Root cause
`Query.check_filterable()` honored a `filterable` attribute on ANY object:
`if not getattr(expression, 'filterable', True): raise`. Model instances expose
their field names as attributes, so an instance of a model with a `filterable`
field reports `filterable=False` and is mistaken for an expression that opted out
of filtering. The `filterable` escape hatch was designed for expressions only.

## Fix (django/db/models/sql/query.py, check_filterable)
Gate the opt-out on the object being an expression:

```python
if (
    hasattr(expression, 'resolve_expression') and
    not getattr(expression, 'filterable', True)
):
    raise NotSupportedError(...)
```

Model instances (no `resolve_expression`) are never mistaken for expressions;
expressions that genuinely opt out are still rejected. Matches the upstream
resolution of this ticket.

## Files touched
- django/db/models/sql/query.py (check_filterable condition + comment)

## Verification (runs/verify.py)
- Ticket scenario: `filter(value="x", metadata_type=<instance>)` compiles without
  NotSupportedError ✓
- An expression subclass with `filterable = False` still raises
  NotSupportedError (unit-level check: the filter pipeline resolves plain F()
  objects to columns before the check) ✓
Output: ALL_OK.

## Confidence
High — matches the upstream resolution and verified in both directions.
