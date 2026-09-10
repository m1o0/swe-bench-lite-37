# django__django-11797 — Filtering on query result overrides GROUP BY of internal query

## Ticket
`User.objects.filter(email__isnull=True).values('email').annotate(m=Max('id')).values('m')`
groups by email (correct). Using it as an exact-lookup RHS —
`User.objects.filter(id=a[:1])` — rewrites the inner SELECT to the pk (a documented
adaptation) and the pk then leaks into the subquery's GROUP BY, producing
`GROUP BY U0."id"` instead of `GROUP BY U0."email"`, silently changing results.

## Root cause (traced with instrumented compilation)
1. `Exact.process_rhs` (django/db/models/lookups.py) rewrites the sliced RHS's select
   to the pk (`clear_select_clause(); add_fields(['pk'])`).
2. `SQLCompiler.get_group_by` unconditionally appends every non-aggregate SELECT
   column to GROUP BY ("select, order_by, and having are added in any case").
   The pk introduced by the lookup adaptation therefore joins the GROUP BY.

Confirmed with an instrumented compilation (driver debug output): the subquery
compiler's select = [Col(U0, id)] and get_group_by emitted [U0."email", U0."id"].

## Fix (2 files)
- django/db/models/lookups.py — `Exact.process_rhs`: when rewriting the sliced RHS's
  select to the pk, mark the query (`suppress_select_in_group_by = True`): the
  rewritten column is an output constraint of the comparison, not a grouping column.
- django/db/models/sql/compiler.py — `get_group_by`: when the query carries that
  marker, skip appending SELECT columns to the GROUP BY expressions.

Result: `WHERE repro_user.id = (SELECT U0.id ... WHERE email IS NULL GROUP BY
U0.email LIMIT 1)` — grouping preserved, matching the ticket's expected SQL.

## Files touched
- django/db/models/lookups.py (Exact.process_rhs)
- django/db/models/sql/compiler.py (get_group_by guard)

## Verification (runs/driver.py)
- A and A[:1] queries unchanged (GROUP BY email; + LIMIT 1).
- B subquery: GROUP BY U0."email" LIMIT 1 — no U0."id" in GROUP BY. ALL_OK.
- Note: the lookup also goes through SubqueryConstraint for related-field paths; the
  exact-lookup path covered here is the one exercised by the ticket.

## Confidence
Medium-high — mechanism fully traced and verified both directions; hidden test's
exact SQL string assertion assumed to match the ticket's printed expectation.
