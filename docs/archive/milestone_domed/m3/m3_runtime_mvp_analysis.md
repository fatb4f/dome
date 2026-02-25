# M3 Runtime MVP Analysis

## Baseline

- M2 delivered a frozen `domed.v1` proto and reproducible codegen.
- No runtime daemon currently serves the contract.
- No lifecycle store exists for `skill_execute -> status -> stream -> cancel`.

## Gap

- Missing runtime state model for jobs/events.
- Missing idempotency ledger semantics at daemon layer.
- Missing deterministic event sequence handling.

## Implementation slice (M3 now)

- Add in-repo runtime store abstraction for job/event lifecycle.
- Encode idempotency and transition guards in one place.
- Add unit tests for submit/status/cancel/stream invariants.

## Handoff to M4

- M4 consumes this runtime through generated stubs and thin-client wrappers.

