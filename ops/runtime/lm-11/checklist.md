# LM-11 Checklist

- [x] Created tracker issue: #37.
- [x] Added packet artifacts for `pkt-dome-lm-11-binder-v1-deterministic-integration`.
- [x] Added deterministic binder implementation in `tools/telemetry/memory_binder.py`.
- [x] Added binder storage substrate to `tools/telemetry/memory_schema.sql`:
  - `binder_fact` table
  - binder indexes
- [x] Implemented canonical fingerprint hashing (`sha256` over canonical JSON bytes).
- [x] Implemented deterministic idempotency/upsert keys for binder rows.
- [x] Added replay/idempotency tests in `tests/test_memory_binder.py`.
- [x] Updated execution tracker milestone state for LM-11.
- [x] Ran focused LM-11 test suite.
