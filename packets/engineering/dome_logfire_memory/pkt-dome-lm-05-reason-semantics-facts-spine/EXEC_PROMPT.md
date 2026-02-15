# EXEC_PROMPT: pkt-dome-lm-05-reason-semantics-facts-spine

## Scope
- Milestone: LM-05 - reason semantics + task/event facts spine
- Tracker issue: #31
- Depends on: LM-04

## Tasks
1. Update telemetry schema/storage to support `failure_reason_code` + `policy_reason_code`.
2. Preserve `reason_code` as compatibility alias at API boundaries.
3. Extend `memoryd` to materialize `task_fact` and `event_fact` from run artifacts.
4. Add tests for semantics split and idempotent reprocessing of task/event facts.
5. Run focused tests.
6. Write evidence artifacts under `ops/runtime/lm-05/`.

## Acceptance checks
- query_priors supports `failure_reason_code` and alias `reason_code`.
- upsert_capsule can store optional policy denial reason without overwriting failure reason.
- memoryd --once materializes run/task/event facts from run directories.
- Focused memory tests pass.

## Evidence
- `ops/runtime/lm-05/checklist.md`
- `ops/runtime/lm-05/command_output.txt`
