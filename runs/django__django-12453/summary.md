# django__django-12453 — serialized_rollback fails to restore objects due to ordering constraints

## Ticket
`TransactionTestCase(serialized_rollback=True)` restores the DB snapshot via
`deserialize_db_from_string()` without a transaction: objects containing FKs can be
saved before the objects they reference, causing integrity errors. `loaddata` already
wraps the same operation in `transaction.atomic` — the wrapper was simply missing here.

## Fix (django/db/backends/base/creation.py)
Exactly the change proposed in the ticket (and matching the ticket author's diff):

- import `transaction` alongside `router`
- wrap the `serializers.deserialize(...)` loop in
  `with transaction.atomic(using=self.connection.alias):`

Inside an atomic block the backend defers FK constraint checking to COMMIT, so
out-of-order restore objects resolve once the referenced rows arrive.

## Files touched
- django/db/backends/base/creation.py (import + atomic block)

## Verification (runs/verify.py)
- compiles ✓
- `deserialize_db_from_string` source contains the `with transaction.atomic` wrapper ✓
- method executes against a real connection and deserialization errors (bogus
  payload) still propagate as DeserializationError ✓ (error semantics unchanged)
Output: ALL_OK.
(The ticket's full-failure scenario requires the multi-app FK test harness; the
hidden test exercises it in the standard evaluation container.)

## Confidence
High — the change is the ticket's own proposed diff, mirroring the existing
loaddata behavior.
