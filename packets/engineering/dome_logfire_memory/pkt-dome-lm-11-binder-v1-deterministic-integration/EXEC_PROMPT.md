# EXEC_PROMPT: pkt-dome-lm-11-binder-v1-deterministic-integration

## Scope
- Milestone: LM-11
- Tracker issue: #37
- Depends on: LM-10

## Tasks
1. Implement binder v1 idempotency/upsert keys from section 9.4.
2. Enforce canonical fingerprint hashing and deterministic derived writes.
3. Add replay reprocessing tests proving no duplicate derived artifacts.
4. Write evidence artifacts under `ops/runtime/lm-11/`.

## Acceptance checks
- `pytest -q tests/test_memory_binder.py tests/test_memory_query_contract.py` passes.
- Binder outputs are deterministic and replay-safe.

## Evidence
- `ops/runtime/lm-11/checklist.md`
- `ops/runtime/lm-11/command_output.txt`
