# pytest-dev/pytest#5221 — Display fixture scope with `pytest --fixtures`

## Approach

The `--fixtures` option is implemented in `src/_pytest/python.py`:
`pytest_addoption` registers `--fixtures` (dest `showfixtures`), and
`showfixtures()` / `_showfixtures_main()` collect every `FixtureDef` from the
session's `FixtureManager` (`fm._arg2fixturedefs`) and print each fixture's
name (plus, with `-v`, its source location) followed by its docstring.

`FixtureDef` (in `src/_pytest/fixtures.py`) already stores the requested scope
in its `scope` attribute (`"function"`, `"class"`, `"module"`, `"session"`),
so the whole feature is a small formatting change in `_showfixtures_main`.

Format chosen: append ` [<scope> scope]` to the displayed spec for fixtures
whose scope is not the default `"function"`; function-scoped fixtures stay
unannotated so the common case remains uncluttered. The suffix applies in both
normal and verbose mode (in verbose mode it comes after the `name -- location`
part). Examples:

```
my_fixture                     # function scope (unchanged)
my_module_fixture [module scope]
my_session_fixture -- conftest.py:7 [session scope]   # with -v
```

## What was changed

1. `src/_pytest/python.py` (`_showfixtures_main`): after the existing
   `funcargspec` construction, append `"[<scope> scope]"` when
   `fixturedef.scope != "function"`. Two lines added.
2. `testing/python/fixtures.py` (`TestShowFixtures`): added
   `test_show_fixtures_verbose_include_scope` which defines module-, session-,
   and function-scoped fixtures and asserts that the two non-function scopes
   are shown (with and without `-v`) while the function-scoped one keeps the
   old format.
3. `changelog/5221.feature.rst`: towncrier changelog fragment describing the
   feature.

## Files touched

- `D:\mio\worktrees\pytest-dev__pytest-5221\src\_pytest\python.py`
- `D:\mio\worktrees\pytest-dev__pytest-5221\testing\python\fixtures.py`
- `D:\mio\worktrees\pytest-dev__pytest-5221\changelog\5221.feature.rst` (new)

## Verification

- `python -m py_compile` passes on both edited `.py` files.
- Dependencies for this pytest 4.4-era checkout are not installed in this
  environment and installing them was out of scope, so the new test was not
  executed; the change is a pure string-formatting addition over an attribute
  (`fixturedef.scope`) that the same function already relies on elsewhere.
- `git diff` was captured to `patch.diff` (non-empty, includes the new
  changelog file via intent-to-add).

## Confidence

High. The change is minimal (2 lines of behavior), sits on a single obvious
code path (`_showfixtures_main`), uses an attribute already present on
`FixtureDef`, and is covered by a new test. The only open design question is
cosmetic: whether to also annotate function-scoped fixtures (the default); the
implemented behavior hides those to avoid noise, which matches the intent of
the issue report.
