# django__django-12589 — GROUP BY error with tricky field annotation (ambiguous column)

## Ticket
`values("status").annotate(total_count=Count("status"))` where "status" is a Subquery
annotation produces `GROUP BY "status"` (bare alias) on Django 3.0.x — postgres raises
`column reference "status" is ambiguous` (the name collides with real columns of joined
tables). Django 2.2 grouped by the full subquery expression.

## Root cause (instrumented compilation)
`values("status")` puts a `Ref('status', Subquery)` into both SELECT and the GROUP BY
tuple. `SQLCompiler.get_group_by()` has two paths that compile the Ref to its bare
quoted alias (`"status"`):
1. the group_by-tuple pass (`expressions.append(expr)` for anything with as_sql)
2. (related) `Ref.get_group_by_cols()` returning `[self]` for the select pass

Grouping by the alias is ambiguous whenever the alias name collides with joined table
columns — the subquery's own output name "status" collides with AB.status / C.status.

## Fix (2 files)
- django/db/models/sql/compiler.py — get_group_by tuple pass: when the entry is a Ref
  whose source is a Subquery, append `expr.source` (the full subquery expression)
  instead of the bare alias. Added Subquery to the expressions import.
- django/db/models/expressions.py — `Ref.get_group_by_cols()`: same rule for the
  select pass (return the source's group-by cols for Subquery sources).

Non-Subquery Refs (plain column aliases) keep the alias grouping — a deliberate 3.0
optimization that this fix preserves.

## Files touched
- django/db/models/sql/compiler.py (import + tuple pass)
- django/db/models/expressions.py (Ref.get_group_by_cols)

## Verification (runs/driver.py — reproduces the ticket's query on postgres backend)
- Before: GROUP BY "status" (ambiguous).
- After: GROUP BY (SELECT U0."status" ... ) — full expression (2.2 semantics), the
  ambiguity is gone. Output: ALL_OK.

## Confidence
High — reproduces the ticket's query exactly and the fix restores 2.2 semantics.
