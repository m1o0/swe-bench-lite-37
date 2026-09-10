# django__django-10924 — Allow FilePathField path to accept a callable

## Root cause (design limitation)
`models.FilePathField` treated `path` strictly as a string: it was baked into
migrations verbatim, making per-machine absolute paths unportable. The documented
Django convention for machine-dependent values (callables evaluated at runtime) was
unsupported: passing a callable reached `forms.FilePathField.__init__` un-evaluated,
which then called `os.scandir()` on a function object and crashed.

## Fix (django/db/models/fields/__init__.py, formfield(), 1 line)
`'path': self.path` → `'path': self.path() if callable(self.path) else self.path`

Semantics:
- `field.path` keeps the callable untouched (deconstruct() already passes callables
  through, so migrations serialize the function reference instead of a baked string).
- `formfield()` evaluates the callable once when constructing the form field, so
  choices are built from the machine-specific directory at use time.
- String paths behave exactly as before.

## Files touched
- django/db/models/fields/__init__.py (formfield, 1 line)

## Verification (runs/verify.py, with pytz+sqlparse installed locally)
- field.path stays callable: True
- formfield().path == evaluated callable result: True
- form field is FilePathField with choices built from the evaluated dir: True
- string path unchanged: True
- deconstruct() keeps the callable reference: True
Output: ALL_OK.

## Confidence
High — matches the upstream resolution (formfield evaluates callable; callable flows
into migrations as a serializable reference).
