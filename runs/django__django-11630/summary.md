# django__django-11630 — models.E028 fired for cross-app db_table clashes in multi-database setups

## Ticket
Django 2.2 introduced system check models.E028 ("db_table 'x' is used by multiple
models"). Projects where different apps live in different databases legitimately share
table names; after upgrading, `manage.py check` fails outright. Cross-app clashes are
legitimate when database routers are in play; a clash inside a single app is a real bug.

## Fix (django/core/checks/model_checks.py, check_all_models)
The E028 loop now inspects the app labels of the clashing models:

- Models span **multiple apps** AND `settings.DATABASE_ROUTERS` is configured →
  skipped (multi-database setups are plausible).
- Models in the **same app** → always an error (even with routers).
- Cross-app clash **without** routers → still an error (single-database assumption
  preserved, no behavior change for default projects).

Also added the `settings` import.

## Files touched
- django/core/checks/model_checks.py (import + E028 loop condition)

## Verification (runs/verify.py — synthetic models via get_models patch)
- cross-app clash + DATABASE_ROUTERS installed → no E028 ✓
- cross-app clash without routers → E028 present ✓
- same-app clash with routers → E028 present ✓
Output: ALL_OK.
- Targets: test_collision_across_apps_database_routers_installed,
  test_collision_in_same_app_database_routers_installed
  (check_framework DuplicateDBTableTests).

## Confidence
High on mechanism; medium on exact upstream variant (some implementations warn
instead of skipping) — hidden tests decide.
