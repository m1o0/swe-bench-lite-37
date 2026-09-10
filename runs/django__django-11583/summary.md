# django__django-11583 — StatReloader intermittent "ValueError: embedded null byte"

## Root cause
`iter_modules_and_files()` (django/utils/autoreload.py) calls `path.resolve(strict=True)`
on every collected module file. On filesystems where a path contains an embedded null
byte (or where symlink resolution traverses such a path), the resolve raises
ValueError("embedded null byte") (Linux/py3.6-3.8 per the ticket traceback) /
OSError("embedded null character in path") (Windows/py3.12), crashing the reloader's
tick loop. `resolve(strict=True)` replaced the older exists()+resolve() flow in 3.1 dev,
moving the failure into resolve().

## Fix (django/utils/autoreload.py, iter_modules_and_files)
Added an except clause next to the existing FileNotFoundError handling:

```python
except (OSError, ValueError) as e:
    # Some paths (e.g. those with embedded null bytes/characters)
    # can't be resolved on the filesystem; skip them instead of
    # crashing the reloader.
    if 'embedded null' not in str(e):
        raise
    continue
```

The guard re-raises unrelated errors (no silent swallowing). Both exception types are
caught because the message differs across platforms/versions ("embedded null byte" on
Linux ValueErrors, "embedded null character" on Windows OSErrors).

## Files touched
- django/utils/autoreload.py (one except clause)

## Verification (runs/verify.py)
- A path containing \x00 is skipped without raising; it is absent from the result set.
- A real file is resolved and the result entry is a pathlib.Path instance.
Output: ALL_OK.
- Targets: test_path_with_embedded_null_bytes, test_paths_are_pathlib_instances
  (utils_tests TestIterModulesAndFiles).

## Confidence
High.
