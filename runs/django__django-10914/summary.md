# django__django-10914 — Set default FILE_UPLOAD_PERMISSIONS to 0o644

## Root cause analysis

By default, uploaded files ended up with unpredictable, size-dependent
permissions on `FileSystemStorage`:

- Files larger than `FILE_UPLOAD_MAX_MEMORY_SIZE` go through
  `TemporaryUploadedFile`, which buffers into
  `django.core.files.temp.NamedTemporaryFile` (i.e. Python's
  `tempfile.NamedTemporaryFile` / `tempfile.mkstemp`). Python's tempfile module
  creates those files with mode `0o600` for security reasons.
  `FileSystemStorage._save()` then relocates them with `file_move_safe()`
  (`os.rename`), which preserves the `0o600` mode.
- Smaller files stay in memory (`MemoryUploadedFile`) and are streamed into a
  file created by `os.open(full_path, O_WRONLY|O_CREAT|O_EXCL, 0o666)`, whose
  final mode is `0o666 & ~umask` (typically `0o644`, but umask-dependent).

`FileSystemStorage._save()` only calls `os.chmod(full_path, mode)` at the end
(after the temp file has been moved, or after the streamed file has been
closed) when `self.file_permissions_mode is not None`. Since the global
default of the `FILE_UPLOAD_PERMISSIONS` setting was `None`, no chmod ever ran
by default, so the resulting mode differed depending on which upload handler
handled the request — exactly the inconsistency reported in the issue.

## What was changed and why

1. `django/conf/global_settings.py`
   Changed `FILE_UPLOAD_PERMISSIONS = None` to `FILE_UPLOAD_PERMISSIONS =
   0o644` and documented the `None` fallback in the comment. This is the core
   fix: `FileSystemStorage.file_permissions_mode` (a cached property falling
   back to `settings.FILE_UPLOAD_PERMISSIONS`) now defaults to `0o644`, so the
   single `os.chmod()` call at the end of `_save()` — the point after the
   temporary file is moved/closed — uniformly applies `0o644` to every saved
   upload, regardless of upload handler. Files saved through `_save()` are
   always regular files (created with `O_CREAT|O_EXCL` or received via
   `file_move_safe`), so no extra regular-file guard is needed. Explicitly
   setting `FILE_UPLOAD_PERMISSIONS = None` keeps the old
   umask/`0o600`-dependent behavior for backwards compatibility.

   No change was required in `django/core/files/storage.py`: the existing
   chmod-at-end-of-`_save()` already applies the setting at the right place
   for both upload paths (and also covers files copied by `collectstatic`,
   which goes through `storage.save()`).

2. Tests updated for the new default:
   - `tests/file_storage/tests.py`: `test_file_upload_default_permissions` now
     runs against the default settings and asserts mode `0o644`; a new
     `test_file_upload_permissions_unset` keeps coverage of the explicit
     `None` → umask-dependent behavior.
   - `tests/staticfiles_tests/test_storage.py`:
     `test_collect_static_files_permissions` no longer overrides
     `FILE_UPLOAD_PERMISSIONS` and asserts the collected file gets `0o644`.
   - `tests/test_utils/tests.py`: `test_override_file_upload_permissions` now
     asserts `default_storage.file_permissions_mode == 0o644` before
     overriding.

3. Docs updated:
   - `docs/ref/settings.txt`: default changed to `0o644` (the `None`
     fallback paragraph is kept, still accurate).
   - `docs/howto/deployment/checklist.txt`: replaced the now-obsolete warning
     about inconsistent small-vs-large upload modes with a note that `0o644`
     is applied by default.
   - `docs/releases/3.0.txt`: added a backwards-incompatible "Miscellaneous"
     note about the new default and how to opt out with `None`.

## Files touched

- `django/conf/global_settings.py` (the fix)
- `tests/file_storage/tests.py`
- `tests/staticfiles_tests/test_storage.py`
- `tests/test_utils/tests.py`
- `docs/ref/settings.txt`
- `docs/howto/deployment/checklist.txt`
- `docs/releases/3.0.txt`

## Verification

- `python -m py_compile` passed on `django/conf/global_settings.py`,
  `django/core/files/storage.py`, `tests/file_storage/tests.py`,
  `tests/staticfiles_tests/test_storage.py`, `tests/test_utils/tests.py`.
- Functional smoke test (runs directory `smoke_test.py`, worktree on
  `sys.path`, pytz stubbed since the environment cannot install
  dependencies): `FileSystemStorage().file_permissions_mode == 0o644` by
  default; a small streamed upload and a `TemporaryUploadedFile`
  (temp-file-move) upload both save successfully; an explicit
  `FILE_UPLOAD_PERMISSIONS=None` override still reports `None` and saves
  without chmod. Exact on-disk mode bits could not be asserted on this
  Windows host (partial chmod/stat semantics), but the chmod branch executes
  and the mode logic is platform-independent.
- Full test suite not run, per instructions.

## Confidence

High. The change is a one-line default flip plus consistent test/doc updates;
the existing `_save()` chmod point already applies the permission bits after
the temporary file is moved (or the streamed file is closed), so both upload
handlers now yield `0o644` files by default, and explicit `None`/custom modes
retain their previous behavior.
