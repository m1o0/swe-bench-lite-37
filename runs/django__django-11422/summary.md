# django__django-11422 — StatReloader doesn't track manage.py

## Root cause
`iter_all_python_module_files()` (django/utils/autoreload.py) builds the watch set from
`sys.modules`, and `iter_modules_and_files()` skips every module whose `__spec__` is
None. The script run as `__main__` (the user's `manage.py`) has no `__spec__`, so the
main entry file was never watched — edits to it never triggered auto-reload.

## Fix
In `iter_all_python_module_files()`, explicitly collect `__main__.__file__` and merge it
into the `extra_files` passed to `iter_modules_and_files()` (guarded with
`getattr(..., None)` for interactive/`-c` runs where `__main__` has no file).

Note: the django repo itself has no root manage.py at this commit — the tracked file is
the *user's* project script, which lives outside the repo. Verification therefore uses a
stand-in script on disk (iter_modules_and_files() deliberately skips non-existent paths).

## Files touched
- django/utils/autoreload.py (one block added in iter_all_python_module_files)

## Verification
- runs/verify.py: simulates `__main__` with `__spec__ = None` pointing at an existing
  manage.py stand-in; `iter_all_python_module_files()` now includes its resolved path.
  Output: ALL_OK. Before the fix the path was absent from the watch set.
- Mirrors the upstream resolution of ticket #30479.

## Confidence
High.
