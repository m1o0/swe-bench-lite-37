# django__django-12856 — Add check for fields of UniqueConstraints

## Ticket
`UniqueConstraint` accepted nonexistent / m2m / non-local field names silently
(crashing later at constraint creation), while the older unique_together raises
models.E012 for nonexistent fields.

## Fix (2 files)
1. django/db/models/constraints.py — added `UniqueConstraint.check(model)` and
   `_check_fields(model)`:
   - collects the model's `local_fields` + `local_many_to_many` (names + attnames)
   - a field name not in that set → models.E012
     "'fields' refers to the nonexistent field '%s'." — this also covers
     non-local (multi-table-inherited) fields, which are not local to the child.
   - a ManyToManyField name → models.E012
     "'fields' must not contain the ManyToManyField '%s'."
2. django/db/models/base.py — `_check_constraints()` now extends errors with
   `constraint.check(cls)` for every constraint (base Constraint wiring for the
   new per-constraint check).

E012 is the same id unique_together uses for nonexistent fields, per the ticket's
comparison.

## Files touched
- django/db/models/constraints.py (checks import; check + _check_fields)
- django/db/models/base.py (_check_constraints wiring)

## Verification (runs/verify.py — isolated app with 4 model scenarios)
- nonexistent field → models.E012, message names the field ✓
- m2m field → models.E012, message names the ManyToManyField ✓
- valid local field → no E012 ✓
- non-local (MTI-inherited) field → models.E012 ✓
Output: ALL_OK.
- Targets: test_unique_constraint_pointing_to_missing_field,
  test_unique_constraint_pointing_to_m2m_field,
  test_unique_constraint_pointing_to_non_local_field
  (invalid_models_tests ConstraintsTests).

## Confidence
High — all three target scenarios verified end-to-end.
