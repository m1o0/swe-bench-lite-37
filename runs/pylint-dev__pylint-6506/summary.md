# Fix: raw traceback printed for unrecognized command-line option (pylint-dev/pylint#6506)

## Root cause

When an unrecognized command-line option is passed (e.g. `pylint -Q`), the flow is:

1. `pylint/config/config_initialization.py::_config_initialization()` parses the
   command line via `linter._parse_command_line_configuration()`; leftover tokens
   starting with `-`/`--` are collected as `unrecognized_options`. For each hit it
   adds the E0015 `unrecognized-option` message (the "handy" output) **and then
   raises `_UnrecognizedOptionError`** (line 85).
2. `pylint/lint/run.py::Run.__init__()` calls `_config_initialization()` without
   catching `_UnrecognizedOptionError`. The exception therefore propagates out of
   the `pylint` entry point (`run_pylint` -> `Run.__init__` -> ...) and Python
   prints a raw traceback right after the E0015 line.

Note the asymmetry: for unrecognized options in a *configuration file* the same
function catches `_UnrecognizedOptionError` at line 57 and just emits E0015; the
command-line branch had no such handling anywhere up the call stack.

## Change rationale

Catch `_UnrecognizedOptionError` at the point where the traceback escapes —
`Run.__init__` in `pylint/lint/run.py` — and convert it into a clean, user-facing
error, as requested in the issue (mypy-style):

- Keep the existing `Command line:1:0: E0015: Unrecognized option found: ...`
  message (the issue explicitly calls it handy).
- Print `pylint: error: unrecognized arguments: <options>` plus the usage tip
  `Use pylint --help for usage information.` to **stderr**.
- Exit with status **32**, matching the convention already used in `run.py` for
  other configuration/initialization errors (`ArgumentPreprocessingError`,
  unreadable config file, invalid `jobs`), which also exit unconditionally of the
  `exit` flag.

Catching in `Run.__init__` (rather than swallowing the exception inside
`_config_initialization`) keeps `_config_initialization`'s contract intact for
API users and fixes every entry point (`run_pylint`, `Run`, testutils `_Run`,
`epylint`) in one place. The config-file branch of `_config_initialization`
(message-only, no exit) is deliberately untouched.

## Files touched

- `pylint/lint/run.py`
  - import `_UnrecognizedOptionError` from `pylint.config.exceptions`
  - wrap the `_config_initialization(...)` call in `Run.__init__` in
    `try/except _UnrecognizedOptionError`; on error print the clean message and
    usage tip to stderr and `sys.exit(32)`
- `tests/config/test_config.py`
  - `test_unknown_option_name` and `test_unknown_short_option_name` previously
    asserted the buggy behavior (`pytest.raises(_UnrecognizedOptionError)`);
    updated to `pytest.raises(SystemExit)` while keeping the E0015 assertions.
  - removed the now-unused `_UnrecognizedOptionError` import.

## Confidence

High. The traceback path is fully traced from raise site
(`config_initialization.py:85`) to the uncaught propagation at
`run.py` (`_config_initialization` call site); a codebase-wide search shows those
are the only raise/catch sites of `_UnrecognizedOptionError`, and the only tests
depending on the exception were the two updated ones. `python -m py_compile`
passes on both edited files. Limitation: pylint's runtime deps (astroid, toml)
are not installed in this environment, so an end-to-end `pylint -Q` run was not
executed; behavior was verified by code analysis instead.

## Reproduction (before fix)

```
$ pylint -Q
************* Module Command line
Command line:1:0: E0015: Unrecognized option found: Q (unrecognized-option)
Traceback (most recent call last):
  ...
  File ".../pylint/config/config_initialization.py", line 85, in _config_initialization
    raise _UnrecognizedOptionError(options=unrecognized_options)
pylint.config.exceptions._UnrecognizedOptionError
```

## Expected after fix

- stdout: `Command line:1:0: E0015: Unrecognized option found: Q (unrecognized-option)` (unchanged)
- stderr: `pylint: error: unrecognized arguments: Q` + `Use pylint --help for usage information.`
- no traceback; exit code 32 (nonzero)
