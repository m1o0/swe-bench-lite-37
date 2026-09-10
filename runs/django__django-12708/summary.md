# django__django-12708 — Migration crashes deleting index_together when unique_together exists on the same fields

## Ticket
With `unique_together` and `index_together` on the same columns, removing only the
index_together crashes in `_delete_composed_index()` with
`ValueError: Found wrong number (2) of constraints` — introspection reports both the
unique constraint and the plain index, and on many backends a UNIQUE constraint is
itself backed by an index (`index=True`), so `{'index': True}` matches both.

## Fix (django/db/backends/base/schema.py, alter_index_together)
When deleting an index_together, exclude unique constraints from the lookup:

```python
self._delete_composed_index(
    model, fields, {'index': True, 'unique': False}, self.sql_delete_index)
```

`_constraint_names()` already supported `unique=False` filtering — the call site
simply didn't use it.

## Files touched
- django/db/backends/base/schema.py (alter_index_together deletion call)

## Verification (runs/verify.py — real sqlite schema editor end-to-end)
- setup: unique constraint AND plain index both exist on (field1, field2) ✓
- `alter_index_together(Thing, {old}, set())` succeeds (pre-fix: ValueError) ✓
- the unique constraint survives the removal ✓
- the plain index is actually removed ✓
Output: ALL_OK.

## Confidence
High — behavioral verification on a real backend, both directions.
