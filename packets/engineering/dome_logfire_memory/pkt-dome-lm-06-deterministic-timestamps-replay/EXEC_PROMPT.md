# EXEC_PROMPT: pkt-dome-lm-06-deterministic-timestamps-replay

## Scope
- Milestone: LM-06
- Tracker issue: #32
- Depends on: LM-05

## Tasks
1. Implement milestone-specific changes.
2. Add/extend tests.
3. Run focused tests.
4. Write evidence artifacts under ops/runtime/lm-06/.

## Acceptance checks
- pytest -q tests/test_memory_query_contract.py tests/test_memoryd_idempotency.py passes.
- Milestone outcomes are visible in docs/code/tests.

## Evidence
- ops/runtime/lm-06/checklist.md
- ops/runtime/lm-06/command_output.txt
