# Summary: pytest-dev/pytest#5103 — Unroll the iterable for all/any calls to get better reports

## Approach

The assertion rewriter (`AssertionRewriter` in `src/_pytest/assertion/rewrite.py`) visits
every `ast.Call` while rewriting an assert's test expression. I hooked into both call
handlers (`visit_Call_35` and `visit_Call_legacy`) with a new `_unroll_all_any()` method
that intercepts calls of the form `all(<comprehension>)` / `any(<comprehension>)` where the
single argument is a `GeneratorExp`, `ListComp` or `SetComp`.

Instead of rewriting the comprehension into an explicit for-loop (which would require
renaming the comprehension's target variables to avoid leaking them into the enclosing
scope), the rewrite keeps the comprehension as a real comprehension — preserving Python's
comprehension scoping — and only changes what it produces:

`assert all(pred(x) for x in xs)` is rewritten (conceptually) to:

```python
@py_assert0 = [(pred(x), x) for x in xs]          # one (element value, item) pair per iteration
@py_assert1 = [value for value, item in @py_assert0]
@py_assert2 = all(@py_assert1)                     # calls the builtin via @py_builtins
```

On failure, the explanation is built from %-placeholders (evaluated only in the failure
path) using pytest's existing `\n{...}` nested-`where` explanation syntax:

```
assert False
 +  where False = all([False, False, False])
 +    where falsy items: [1, 3, 5]
```

For `any()`, the second line shows the full item list (`where items: [...]`) because `any()`
failing means no item was truthy. Tuple/list comprehension targets (e.g.
`all(a < b for a, b in pairs)`) are captured as tuples and reported accordingly. Multiple
`for` clauses and `if` filters work unchanged (they stay inside the comprehension).

## What I changed

1. `src/_pytest/assertion/rewrite.py`
   - New `AssertionRewriter._comprehension_target_loads()` helper: flattens a comprehension
     target into Load expressions for each bound name, returning `None` for unsupported
     targets (e.g. anything containing a `Starred`) so the caller can fall back.
   - New `AssertionRewriter._unroll_all_any()`: validates the call shape (plain name
     `all`/`any`, exactly one positional argument, no keywords/starargs, argument is a
     `GeneratorExp`/`ListComp`/`SetComp`, all targets are plain names/tuples), emits the
     pair-building list comprehension plus the value extraction and `all()`/`any()` calls,
     and builds the nested explanation. Falls back (returns `None`) to the generic call
     handling for anything it does not recognize.
   - Both `visit_Call_35` and `visit_Call_legacy` try `_unroll_all_any()` first.
2. `testing/test_assertrewrite.py`
   - New `TestAssertionRewrite.test_all_any_unrolled` covering: `all()`/`any()` over a
     generator expression, `all()` over a list comprehension, `all()` with a tuple target,
     and a passing `all()` (`must_pass=True`) to assert evaluation still succeeds.
3. `changelog/5103.feature.rst` (new file, untracked — therefore not part of `git diff`):
   towncrier news fragment describing the feature.

## Verification

- `python -m py_compile` passes on both edited `.py` files.
- The repo itself cannot be imported on the local Python 3.12 (pytest 4.5 imports the
  `imp` module, removed in 3.12) and dependencies were not installed, per the rules, so the
  feature was verified with a standalone harness that extracts the real
  `AssertionRewriter` class from the patched file, stubs its module-level dependencies,
  rewrites sample functions and executes them. 24 scenarios were checked, including:
  genexp/listcomp/setcomp args, tuple targets, multiple `for` clauses, `if` filters,
  `assert not all(...)`/`assert not any(...)`, empty iterables, interaction with `and`/`or`,
  unrolled calls inside comparisons, custom assert messages, two `all()` asserts in one
  function, and fallbacks (plain-iterable args, starred targets, keyword calls, non-`all`
  calls). The exact message strings asserted in the new test were reproduced by the harness.

## Limitations

- **Full materialization / no short-circuit:** the whole iterable is consumed and every
  element is evaluated before `all()`/`any()` runs (this is inherent to "unrolling").
  Side effects per item are preserved (each element/predicate is still evaluated exactly
  once), but laziness is not: infinite or very large iterables, or iterables whose later
  items would raise, now behave differently on failure paths. Comprehension arguments only;
  `all(some_iterable)` is left untouched.
- **Assumes `all`/`any` are the builtins:** a user shadowing the names `all`/`any` before an
  affected assert gets builtin semantics. (The rewriter already makes a similar assumption
  by emitting `AssertionError` directly.)
- **Element expressions are not re-explained:** the element of the comprehension is not
  visited by the rewriter (rewriting it would place intermediate statements outside the
  comprehension scope), so the report shows per-item *values* rather than e.g.
  `where False = is_even(1)`.
- **Starred targets** (`for a, *b in ...`) and calls with keyword/starred arguments fall
  back to the old, opaque message (conservative, never wrong).
- **Async comprehensions** (`x async for ...`) are passed through structurally intact but
  were not exercised in the harness.
- Python-2 compatibility was preserved in the code style (no f-strings, `ast.comprehension`
  constructed with a `TypeError` fallback for pre-3.6 which lacks `is_async`) but not
  executed — no Python 2 interpreter is available here.

## Files touched (all inside the worktree)

- `D:\mio\worktrees\pytest-dev__pytest-5103\src\_pytest\assertion\rewrite.py` (modified)
- `D:\mio\worktrees\pytest-dev__pytest-5103\testing\test_assertrewrite.py` (modified)
- `D:\mio\worktrees\pytest-dev__pytest-5103\changelog\5103.feature.rst` (new, untracked)

## Confidence

**Medium-high.** The rewrite logic, the generated AST shape, the explanation rendering and
all fallback paths were verified end-to-end by executing the actually patched code against
24 scenarios (including the exact strings used in the new unit test); the main residual
risks are the intentional semantic change (full materialization instead of short-circuiting)
and interactions this environment could not run (the repo's own test suite on its supported
interpreter matrix, Python 2, async comprehensions).
