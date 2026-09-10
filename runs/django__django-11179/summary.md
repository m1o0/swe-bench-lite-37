# Fix summary: `delete()` on dependency-free model instances does not clear the PK

Repo: django/django (django__django-11179), base commit `19fc6376ce67d01ca37a91ef2f55ef769f50513a` (3.0 dev)
Worktree: `D:\mio\worktrees\django__django-11179`

## Root cause analysis

`Collector.delete()` in `django/db/models/deletion.py` has two code paths:

1. **General path** — used when the collector holds multiple objects/dependencies.
   After the SQL deletes it runs:

   ```python
   for model, instances in self.data.items():
       for instance in instances:
           setattr(instance, model._meta.pk.attname, None)
   ```

   so every collected in-memory instance gets its PK set to `None`.

2. **Fast path** — an optimization for "a single obj and no dependencies"
   (`len(self.data) == 1 and len(instances) == 1` and `can_fast_delete(instance)`).
   It executes `sql.DeleteQuery(model).delete_batch([instance.pk], self.using)`
   and then returns immediately. This path skipped the PK-clearing step, so
   `instance.pk` kept its old value after `delete()`. This is exactly the code
   the issue report points at ("See Django.db.models.deletion:276-281. Should
   update the model line 280.").

   Note: the fast path is taken precisely for models with no dependencies; the
   moment a model has dependent objects (or `pre_delete`/`post_delete` signal
   listeners), `can_fast_delete()` returns `False` and the general path — which
   does clear PKs — runs. Hence the reported inconsistency: dependency-free
   models kept their PK, dependent ones did not.

## What was changed and why

One line added to the fast path of `Collector.delete()`, mirroring the general
path's PK-clearing so both paths behave identically:

```python
        # Optimize for the case with a single obj and no dependencies
        if len(self.data) == 1 and len(instances) == 1:
            instance = list(instances)[0]
            if self.can_fast_delete(instance):
                with transaction.mark_for_rollback_on_error():
                    count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)
                setattr(instance, model._meta.pk.attname, None)   # <-- added
                return count, {model._meta.label: count}
```

- It uses `model._meta.pk.attname` (not `instance.pk = None`) for consistency
  with the general path and to bypass the FK descriptor cache correctly.
- It is placed after the `delete_batch()` call (outside the
  `mark_for_rollback_on_error()` block): if the DB delete fails and raises, the
  exception propagates before the PK is cleared, so the in-memory state stays
  consistent with the database.
- No queries, signals, or return-value shape are changed, so the existing
  `FastDeleteTests` (query-count assertions) are unaffected. The fast path is
  only reachable for models without parents/dependents/signal listeners, so
  multi-table-inheritance children are unaffected.

## Files touched

- `D:\mio\worktrees\django__django-11179\django\db\models\deletion.py` —
  one line added in `Collector.delete()` (fast-delete branch).

## Verification (no dependencies installed, no full test suite run)

- `python -m py_compile django/db/models/deletion.py` — OK.
- Behavioral smoke test (throwaway script, in-memory sqlite, Django 3.0 ORM):
  - dependency-free instance `s.delete()` → `s.pk is None` (this reproduced the
    bug before the fix: `FAIL: fast path did not clear pk (got 1)` on unpatched
    code; passes after);
  - delete() return value shape unchanged (`(1, {'_smoke_app.Simple': 1})`);
  - MTI parent/child deletes (general path) still clear pks of collected
    instances and remove all rows.
- Targeted Django test modules (sqlite, via `tests/runtests.py`):
  `delete delete_regress` → 60 tests OK (3 pre-existing skips);
  `model_inheritance model_inheritance_regress signals queries` → 449 tests OK
  (9 skips, 3 expected failures — all pre-existing).

## Confidence

**High.** The fix is a one-line, behavior-preserving-except-the-bug change that
makes the fast path consistent with the general path; the issue text points at
exactly this branch/line, the unpatched code reproduces the reported behavior,
and all deletion-related test modules pass.

## Deliverables

- `patch.diff` — `git diff` of the worktree (non-empty, 1 file, +1 line).
- `summary.md` — this file.
