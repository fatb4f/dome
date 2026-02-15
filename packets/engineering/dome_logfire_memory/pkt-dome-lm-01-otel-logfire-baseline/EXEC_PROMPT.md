# EXEC_PROMPT: pkt-dome-lm-01-otel-logfire-baseline

## Scope
- Milestone: LM-01 - OTel + Logfire baseline
- Tracker issue: #26
- Depends on: None

## Tasks
1. Add telemetry helpers for stage-level OTel spans.
2. Instrument orchestration stages with stable correlation attributes (`run.id`, task/gate attrs where applicable).
3. Add or update tests to verify basic instrumentation behavior does not break execution flow.
4. Run `just test`.
5. Write evidence artifacts under `ops/runtime/lm-01/`.

## Acceptance Checks
- `just test` passes.
- Stage instrumentation is present for planner, dispatcher/implementers, checker, promote, and state-write flow.
- Milestone checklist is fully checked in issue for LM-01.

## Evidence
- `ops/runtime/lm-01/checklist.md`
- `ops/runtime/lm-01/command_output.txt`
