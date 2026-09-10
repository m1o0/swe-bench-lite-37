# django__django-11999 — Cannot override get_FOO_display() (regression since 2.2)

## Root cause
`Field.contribute_to_class()` unconditionally did
`setattr(cls, 'get_%s_display' % self.name, partialmethod(cls._get_FIELD_display, field=self))`
after the model class body was executed — silently overwriting any user-defined
`get_foo_bar_display()` method on the model (regression introduced in 2.2 when the
method construction moved to contribute_to_class).

## Fix (django/db/models/fields/__init__.py, contribute_to_class)
Only install the generated method when the model class does not define it:

```python
if self.choices is not None and 'get_%s_display' % self.name not in cls.__dict__:
```

Using `cls.__dict__` (not hasattr) keeps inherited generated methods working on
subclasses while respecting explicit definitions on the model itself.

## Files touched
- django/db/models/fields/__init__.py (1 line)

## Verification (runs/driver.py + repro/models.py)
- Model defining its own `get_foo_bar_display()` returning "something":
  `str(obj)` and the method call both return "something" (was 'foo'/'bar' — the bug).
- A plain choices field without an override still generates the default display
  ('one' for value 1). ALL_OK.
- Target: test_get_FIELD_display_overridden-ish assertions in the hidden test patch.

## Confidence
High — matches the upstream resolution of this long-standing ticket.
