# django__django-12497 — Wrong hint about recursive relationship

## Ticket
When an m2m field's intermediary model has more than two ForeignKeys and
`through_fields` is not set, the check error's hint suggested:
`use ForeignKey("%s", symmetrical=False, through="%s")` — but `symmetrical` and
`through` are ManyToManyField keyword arguments, and `symmetrical=False` has been
unnecessary for recursive m2m-with-through since Django 3.0.

## Fix (django/db/models/fields/related.py, 2 occurrences)
The hint text in `_check_relationship_model` (both the "from" and "to" ambiguous-FK
branches, fields.E338/E339) now reads:

```python
'If you want to create a recursive relationship, '
'use ManyToManyField("%s", through="%s").'
```

## Files touched
- django/db/models/fields/related.py (2 hint strings)

## Verification
- py_compile passes; zero occurrences of the old `symmetrical=False, through` hint
  remain in the module.
- Message-only change: no behavioral surface beyond the hint text.

## Confidence
High — matches the upstream resolution of this ticket.
