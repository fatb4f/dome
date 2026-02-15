# EXEC_PROMPT: pkt-dome-lm-09-tracker-otlp-reconciliation

## Scope
- Milestone: LM-09
- Tracker issue: #35
- Depends on: LM-08

## Tasks
1. Reconcile observability naming to `OTLP backend` terminology with backend options.
2. Ensure tracker status language reflects shipped implementation truthfully.
3. Run focused observability tests.
4. Write evidence artifacts under `ops/runtime/lm-09/`.

## Acceptance checks
- `pytest -q tests/test_observability.py` passes.
- Tracker and observability docs reflect OTLP-backend naming and truthful status semantics.

## Evidence
- `ops/runtime/lm-09/checklist.md`
- `ops/runtime/lm-09/command_output.txt`
