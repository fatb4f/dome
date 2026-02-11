# Tasks: <feature-name>

> Filled by `/speckit.tasks`. Must be executable. Each task declares evidence.

## Phase 0 — Setup
- [ ] T001 Create/confirm SSOT artifacts and schemas exist
  - Evidence: files present + schema validation passes

## Phase 1 — PLAN (work DAG)
- [ ] T010 Define DAG node schema `{reqs,deps,provs,assert}` and work item lifecycle
  - Evidence: schema docs + example node validates

## Phase 2 — EXECUTE (signals)
- [ ] T020 Implement evidence bundle capture (exit codes, stdout/stderr, logs, artifacts, hashes)
  - Evidence: sample run produces full bundle

## Phase 3 — GATE (deterministic)
- [ ] T030 Implement gate predicates as pure functions over (state, evidence, node)
  - Evidence: replay test: same inputs => same outputs

## Phase 4 — Minimal integration
- [ ] T040 Minimal loop: next(S) → execute → gate → update state
  - Evidence: end-to-end demo with one feature directory

## Notes
- Prefer smallest increments.
- Do not mark DONE without evidence.
