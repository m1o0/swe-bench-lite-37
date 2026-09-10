# django__django-11001 — Fix: multiline RawSQL order_by clauses incorrectly deduplicated

## Root cause analysis

`SQLCompiler.get_order_by()` deduplicates ORDER BY clauses using a `seen` set keyed by
`(without_ordering, params_hash)`, where the key is computed with:

```python
self.ordering_parts = re.compile(r'(.*)\s(ASC|DESC)(.*)')  # __init__, compiler.py:35
...
without_ordering = self.ordering_parts.search(sql).group(1)
```

Because the pattern is compiled **without** `re.DOTALL`, the `.*` groups cannot match
across line boundaries. When the compiled ORDER BY SQL is multiline (which happens with
multiline `RawSQL(...)` expressions, as in the issue report), `re.search()` can only match
a small fragment on/near the last line, so `group(1)` is just that fragment (e.g.
`"\t\t\t\t else null end"`) instead of the full expression minus its ASC/DESC suffix.

Consequence: two **distinct** multiline ordering expressions that merely share an identical
last line (and identical params) produce the same dedup key, so the second one is silently
dropped from the ORDER BY clause. Verified by direct regex simulation:

- old logic kept 4 of 6 orderings from the issue's example (the second multiline clause wrongly removed);
- with the fix, all 5 distinct orderings are kept and the one exact duplicate is still removed.

## What was changed and why

### 1. `django/db/models/sql/compiler.py` (the fix)

In `SQLCompiler.get_order_by()` the SQL is reduced to a single line before applying the
`ordering_parts` regex, so deduplication compares the **full** ordering expression:

```python
sql_oneline = ' '.join(sql.splitlines())
without_ordering = self.ordering_parts.search(sql_oneline).group(1)
```

Design notes:
- `splitlines()` (not `split()`) is used so only line boundaries (`\n`, `\r\n`, `\r`, and
  other Unicode line breaks) are normalized; intra-line whitespace is preserved exactly,
  which keeps the dedup key faithful to the SQL text and avoids collapsing whitespace
  inside string literals.
- `without_ordering` is used **only** as the dedup key here — the tuple returned by
  `get_order_by()` still carries the original multiline `sql`, so generated SQL is unchanged
  for single-line cases (behavior is identical whenever the SQL is already one line, because
  `splitlines()`/`join` is a no-op then apart from trailing/leading newline removal inside
  the key only).
- The second occurrence of `ordering_parts.search(...)` in `get_extra_select()` (compiler.py,
  DISTINCT ON handling) was deliberately left untouched: there the result is used as literal
  SELECT-clause SQL, and changing it would alter generated SQL beyond this issue. That spot
  could produce mangled extra select SQL for multiline orderings, but it is a separate,
  pre-existing quirk and out of scope for a minimal fix.

### 2. `tests/ordering/tests.py` (regression test)

Added `OrderingTests.test_order_by_multiline_raw_sql`: two multiline `RawSQL` orderings whose
last lines are identical (`id else null end`) but whose full expressions differ, ordered
`.asc()` and `.desc()`. It asserts both `CASE WHEN ...` terms survive into the compiled
`str(qs.query)` (whitespace-normalized). Param-less RawSQL with a SQL date literal is used so
the test is backend-agnostic (`Query.__str__` substitutes params via `%` formatting, so
placeholders would have been rewritten); the test compiles the query without executing it,
so it runs on any backend. With the old code the second ordering is dropped and the test
fails; with the fix it passes (verified via standalone simulation of both code paths).

## Files touched

- `D:\mio\worktrees\django__django-11001\django\db\models\sql\compiler.py` — fix in `get_order_by()` (+6/-2 incl. comment).
- `D:\mio\worktrees\django__django-11001\tests\ordering\tests.py` — regression test (+18/-1 incl. import).

## Verification performed

- `python -m py_compile` on both edited files: OK.
- Standalone simulation (`verify_fix.py`, `verify_test.py` in this directory) reproducing the
  compiler dedup loop on the issue's exact SQL: old logic drops a distinct multiline ordering;
  fixed logic keeps all distinct orderings and still drops genuine duplicates; CRLF input handled.
  (Django's test suite was not run, per instructions — no dependencies installed.)

## Confidence

**High.** The one-line root cause (regex cannot match across newlines, so dedup key degenerates
to the last line) is confirmed by direct simulation, and the fix normalizes the key input without
touching the SQL that is actually emitted. Single-line behavior is unchanged, and the only
interaction point (`get_extra_select`) consumes the untouched raw `sql` from the returned tuples.
