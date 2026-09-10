# django__django-11039 — Fix: sqlmigrate wraps output in BEGIN/COMMIT on backends without transactional DDL

## Root cause analysis

`sqlmigrate` controls whether its SQL output is wrapped in transaction statements via the
`output_transaction` flag. In `handle()` it was assigned as:

```python
self.output_transaction = migration.atomic
```

i.e. it only considered whether the migration is declared atomic.

At actual migration-run time, however, the migration executor only executes a migration inside a
transaction when the migration is atomic **and** the database supports transactional DDL:
`BaseDatabaseSchemaEditor.__init__` (`django/db/backends/base/schema.py`, line 97) computes
`self.atomic_migration = self.connection.features.can_rollback_ddl and atomic`, and
`BaseDatabaseFeatures.can_rollback_ddl` defaults to `False` (only PostgreSQL and SQLite set it to
`True`; MySQL, Oracle, etc. do not).

So on backends without transactional DDL support, `sqlmigrate` printed `BEGIN`/`COMMIT` around the
SQL even though `migrate` would never run that SQL inside a transaction — misleading output
(the wrapping itself is done by `BaseCommand.execute` in `django/core/management/base.py`, lines
366-372, using `connection.ops.start_transaction_sql()` / `end_transaction_sql()`).

## What was changed and why

1. `django/core/management/commands/sqlmigrate.py`
   - Changed the assignment to mirror the executor's behavior:
     `self.output_transaction = migration.atomic and connection.features.can_rollback_ddl`
   - Updated the accompanying comment. This is exactly the fix suggested in the issue report.

2. `tests/migrations/test_commands.py` (`MigrateTests`)
   - Added `test_sqlmigrate_for_non_transactional_ddl_database`, modeled on the existing
     `test_sqlmigrate_for_non_atomic_migration`. Instead of overriding `MIGRATION_MODULES` to point
     at a non-atomic migration, it uses the (atomic) `migrations.test_migrations` module and mocks
     `connection.features.can_rollback_ddl` to `False` with `mock.patch.object`, then asserts no
     `start_transaction_sql()` / `end_transaction_sql()` appears in the output.

## Files touched

- `D:\mio\worktrees\django__django-11039\django\core\management\commands\sqlmigrate.py`
- `D:\mio\worktrees\django__django-11039\tests\migrations\test_commands.py`

## Validation

- `python -m py_compile` succeeded on both edited files.
- Full test suite was intentionally not run (per task constraints, no dependency installation).
  The new test uses only already-imported names in `test_commands.py` (`mock`, `io`, `call_command`,
  `connection`, `override_settings`) and follows the exact assertion pattern of the existing
  non-atomic-migration test.

## Confidence

High. The one-line behavior change directly matches the executor's transactional-DDL logic cited in
the issue, and the added test mirrors the reporter's suggested approach.
