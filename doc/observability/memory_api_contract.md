# Memory API Contract

Date: 2026-02-15

## Endpoints

1. `memory.query_priors`
   - Inputs:
     - `scope`: `task|run|repo`
     - `filters`: optional (`failure_reason_code`, `task_status`)
       - compatibility alias: `reason_code` maps to `failure_reason_code`
     - `limit`: bounded to max 200
   - Output:
     - ordered rows from `task_fact` sorted by `updated_ts DESC, run_id ASC, task_id ASC`

2. `memory.upsert_capsule`
   - Inputs:
     - evidence capsule payload
     - `run_id`, `task_id`, `status`, `failure_reason_code`
     - optional `policy_reason_code` / `guard_reason_code` for guard denials
   - Behavior:
     - validates against `ssot/schemas/evidence.capsule.schema.json`
      - upserts `task_fact` pointer row

3. `memory.get_run_summary`
   - Inputs:
     - `run_id`
   - Output:
     - `{run, tasks}` from `run_fact` and `task_fact`

4. `memory.health`
   - Inputs:
     - optional checkpoint path
   - Output:
     - daemon checkpoint status and processed run count

## Determinism Requirements

- Identical query inputs against identical DB snapshots must return identical ordering.
- `limit` must be bounded to avoid unbounded retrieval.

## Semantics Contract

- `failure_reason_code` is the canonical retrieval/classification field for domain/task failure semantics.
- `policy_reason_code` (or `guard_reason_code`) is separate control-plane denial semantics and must not overwrite `failure_reason_code`.

## Cross-Repo Dependencies

- `dome`: owns API implementation and backward-compatible aliasing (`reason_code` -> `failure_reason_code`).
- `xtrlv2`: owns SSOT schema/policy contracts that define reason and guard semantics.
