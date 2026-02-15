# EXEC_PROMPT: pkt-dome-lm-10-semantics-migration-completion

## Scope
- Milestone: LM-10
- Tracker issue: #36
- Depends on: LM-09

## Tasks
1. Complete reason semantics migration (`failure_reason_code` vs `policy_reason_code`).
2. Keep `reason_code` only as compatibility alias at API/ingress boundaries.
3. Add/extend regression tests for split invariants.
4. Write evidence artifacts under `ops/runtime/lm-10/`.

## Acceptance checks
- `pytest -q tests/test_observability.py tests/test_memory_query_contract.py tests/test_memoryd_idempotency.py` passes.
- Tracker/docs/code/tests consistently enforce the semantics split.

## Evidence
- `ops/runtime/lm-10/checklist.md`
- `ops/runtime/lm-10/command_output.txt`
