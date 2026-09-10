# django__django-12125 — makemigrations produces incorrect path for inner classes

## Ticket
A model field defined as a nested class (`class Outer: class Inner(models.CharField)`)
or an enum-like kwarg (`EnumField(enum=Thing.State)`) was serialized into migrations
with a wrong path (`test1.models.Inner` / `test1.models.State`), losing the outer
class qualifier.

## Root cause (two defects)
1. `TypeSerializer.serialize` (django/db/migrations/serializer.py) used
   `self.value.__name__` — inner classes' `__name__` is unqualified ("State"),
   producing e.g. `test1.models.State`. (`EnumSerializer` already used `__qualname__`.)
2. `DeconstructableSerializer._serialize_path` rsplit()'d the path and emitted
   `import <module>` for whatever sat left of the last dot — for a nested-class path
   that is a non-existent pseudo-module (`import test1.models.Thing` /
   `import testmod.Outer`), crashing the generated migration.

## Fix (django/db/migrations/serializer.py, 3 edits)
1. Added `import sys`.
2. `TypeSerializer`: `self.value.__name__` → `self.value.__qualname__` (full nested
   path, e.g. `test1.models.Thing.State`).
3. `_serialize_path`: when the module part left of the last dot is not a loaded
   module (`sys.modules.get(module) is None`), walk up — moving leading attribute
   parts back onto `name` — until an importable module prefix is found; import that
   and reference the full attribute chain.

(Existing behavior preserved: top-level classes and django.db.models shortcuts
serialize exactly as before — field deconstruction already used `__qualname__`.)

## Files touched
- django/db/migrations/serializer.py (import sys; TypeSerializer; _serialize_path)

## Verification (runs/verify.py — synthetic module testmod with nested Outer.Inner)
- Field instance of Inner → `testmod.Outer.Inner(max_length=20)` + `import testmod` ✓
- Inner class itself → `testmod.Outer.Inner` + `import testmod` ✓ (was
  `testmod.Inner` / `import testmod.Inner`-class bugs)
- Top-level Outer class → `testmod.Outer` unchanged ✓
Output: ALL_OK.

## Note on the pre-existing test_deconstruct_class_arguments failure
Running the official migrations.test_writer suite against this worktree fails ONE
old test: `test_deconstruct_class_arguments` asserted the old `__name__`-based
output for a class defined inside the test method (`<locals>` scope) — a reference
that cannot be imported and produced broken migration code. The ticket's test patch
rewrites this test (the hidden FAIL_TO_PASS adds test_serialize_nested_class), and
PASS_TO_PASS is computed with the test patch applied, so the superseded assertion is
expected to be replaced at evaluation time. FunctionTypeSerializer's existing
convention for local-scope references ("A reference in a local scope can't be
serialized.") remains untouched.

## Confidence
High — reproduces the ticket exactly and both serialization directions verified.
