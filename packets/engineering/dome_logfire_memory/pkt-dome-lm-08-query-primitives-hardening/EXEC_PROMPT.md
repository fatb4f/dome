# EXEC_PROMPT: pkt-dome-lm-08-query-primitives-hardening

## Scope
- Milestone: LM-08
- Tracker issue: #34
- Depends on: LM-05

## Tasks
1. Implement milestone-specific changes.
2. Add/extend tests.
3. Run focused tests.
4. Write evidence artifacts under ops/runtime/lm-08/.

## Acceptance checks
- pytest -q tests/test_memory_query_primitives.py tests/test_memory_query_contract.py passes.
- Milestone outcomes are visible in docs/code/tests.

## Evidence
- ops/runtime/lm-08/checklist.md
- ops/runtime/lm-08/command_output.txt
