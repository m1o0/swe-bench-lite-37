# django__django-11019 — Fix summary

## Issue

Merging 3 or more `django.forms.Media` objects can raise spurious
`MediaOrderConflictWarning`s and produce a worse asset ordering than even the
naive pre-1.11 behavior, even though a valid ordering of the assets exists.

Repro (from the report): widgets with media `['color-picker.js']`,
`['text-editor.js']` and `['text-editor.js', 'text-editor-extras.js',
'color-picker.js']` combined in that order warned and resolved to
`['text-editor-extras.js', 'color-picker.js', 'text-editor.js']` instead of
the dependency-respecting `['text-editor.js', 'text-editor-extras.js',
'color-picker.js']`.

## Root cause

`Media.__add__` merely concatenates the contributors' `_js_lists` /
`_css_lists`, and the `_js` / `_css` properties then **reduce those lists
pairwise**, calling the insertion-based `Media.merge(accumulated, next)` in a
chain.

The pairwise chain loses the information about which element orderings were
actually *required* and which were *arbitrarily chosen*:

1. When `merge` combines two lists that share no elements (e.g.
   `['color-picker.js']` with `['text-editor.js']`), any order is valid, but
   the merged result is a concrete list that fixes one arbitrary order.
2. That arbitrary order is then fed back in as the accumulated list of the
   next merge, where its elements are treated as hard ordering constraints.
   In the repro, `color-picker.js` had been baked in *before*
   `text-editor.js`, while the third list requires `text-editor.js` first —
   the algorithm now sees a "conflict" that was manufactured by its own
   earlier arbitrary choice, warns, and emits an order that even violates the
   third list's declared dependencies (`text-editor.js` ends up last).

So the warning does not reflect a real contradiction between the declared
media definitions; it reflects an ordering decision the reducer itself made
along the way.

## Fix

Treat the problem as what it is — a topological ordering of all the declared
asset lists — and resolve all of them **in one pass**:

- `Media.merge` is now variadic (`merge(*lists)`) and implements a stable
  Kahn's-algorithm topological sort:
  - it builds a dependency graph from the **consecutive (adjacent) pairs** of
    each deduplicated input list (adjacent pairs suffice: the relation is
    transitive, and any genuine contradiction between lists always closes a
    directed cycle);
  - it emits an element as soon as all of its dependencies are emitted,
    preferring the element with the earliest first appearance
    `(list_index, position)` as a deterministic tie-break, which reproduces
    the old algorithm's output for duplicate-free acyclic two-list merges;
  - only a *cycle* in the dependency graph — a genuine contradiction between
    the declarations — raises `MediaOrderConflictWarning` (same category and
    message format as before); the cycle is broken by including the
    earliest-appearing remaining element, so a valid (if compromised) order
    is still returned;
  - duplicated elements within a single list are ignored for ordering
    ("duplicated media definitions are ignored" per the documented/tested
    behavior, #12879).
- `Media._js` now calls `merge(js, *rest)` — one topological sort across all
  accumulated definitions instead of a pairwise reduction. `Media._css` does
  the same per media type: it groups the raw per-definition lists of each
  medium (in first-appearance order of the media types) and merges each
  group in one call.
- The "single non-empty definition" fast path is preserved exactly: `_js` /
  `_css` still return the original first list object untouched when nothing
  needs merging, which keeps `Media.__repr__` showing the original
  tuples/objects (pinned by `test_construction`).

With this, the issue's example resolves to
`['text-editor.js', 'text-editor-extras.js', 'color-picker.js']` with **no**
warning — that order is in fact the unique topological order compatible with
all three declarations.

## Files touched

- `django/forms/widgets.py` — only file changed: `Media._css`, `Media._js`
  and `Media.merge` (public `__add__`, `media_property`, rendering and all
  other widget code unchanged).

## Verification (all standalone, in this runs directory; nothing installed,
no full test-suite run)

- `repro.py` — reproduces the issue on the unfixed tree (warning + wrong
  order) and shows the fix resolves both, at the `Media` level and through a
  real `Form` with the three widgets from the report.
- `verify.py` — 49 checks, all passing:
  - all six `test_merge` cases and the exact `test_merge_warning` message
    (`Detected duplicate Media files in an opposite order:\n1\n2`);
  - `test_merge_js_three_way` / `test_merge_css_three_way` expectations
    (unchanged results, no warnings);
  - combine/inheritance/dedup (#12879), `test_construction` repr & rendering,
    the docs example (`calendar + time`);
  - genuine 2-way and 3-way conflicts still warn;
  - differential fuzz of new `merge` against a verbatim copy of the OLD
    algorithm: 18,878 duplicate-free acyclic 2-list merges produce **byte
    identical output with no warnings**; 1,122 cyclic merges warn on both
    sides (0 mismatches);
  - multi-list property fuzz (20,000 random N-list merges): result is always
    a duplicate-free permutation that respects every input list's relative
    order unless a warning was raised (0 violations).
- `run_real_tests.py` — runs the actual upstream
  `tests/forms_tests/tests/test_media.py` module (17 tests) with a stubbed
  `pytz`/`sqlparse` (runs-dir stubs, not installed): **17/17 OK**.
- `python -m py_compile django/forms/widgets.py` — OK.

## Confidence

**High.** The fix makes the spurious warning impossible by construction
(warnings now require a real cycle among the declarations), matches every
behavior pinned by the existing test module and docs, and is
output-identical to the old algorithm for all duplicate-free two-list merges
(per 18,878-case differential fuzz). Multi-list merges can now differ from
the old pairwise chain only in cases where the old chain silently produced an
order that *violated* one of the declarations — exactly the bug being fixed —
or where duplicates inside one definition are dropped (documented as desired
behavior).

Files/paths:

- Patch: `C:\Users\mio\swe-experiment\runs\django__django-11019\patch.diff`
- Repro: `C:\Users\mio\swe-experiment\runs\django__django-11019\repro.py`
- Verification: `C:\Users\mio\swe-experiment\runs\django__django-11019\verify.py`,
  `run_real_tests.py`, `run_more_tests.py` (+ local `pytz.py`, `sqlparse.py`,
  `verify_settings.py` stubs used only by the scripts)
- Edited source: `D:\mio\worktrees\django__django-11019\django\forms\widgets.py`
