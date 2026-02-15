# Implementation Kickoff Plan (dome + xtrlv2)

Date: 2026-02-15

## Scope

This kickoff plan covers the dual-repo architecture:
- `dome`: integration owner (planner/daemon/materialization/inference/retrieval)
- `xtrlv2`: SSOT owner (guardrails, reason semantics, state/transition contracts)

## Objectives

1. Operationalize TaskSpec-rooted closed-loop adaptation.
2. Enforce failure vs policy semantics split end-to-end.
3. Make 9.4 pattern binding deterministic and auditable.
4. Ship contract tests that prevent cross-repo drift.

## Milestones

### K0: Contract Baseline (must pass before feature expansion)

- Pin `xtrlv2` SSOT versions consumed by `dome`.
- Confirm schema compatibility for:
  - guardrails bundle
  - reason semantics fields (`failure_reason_code`, `policy_reason_code`)
  - transition/guard evaluation records
- Lock API compatibility alias: `reason_code` -> `failure_reason_code`.

Exit criteria:
- Cross-repo contract tests pass in `dome` CI.

### K1: TaskSpec + Wrapper Ingestion Hardening (`dome`)

- Enforce TaskSpec-required fields in planner outputs:
  - `scope`, `target.kind`, `target.id`, `action.kind`, `failure_reason_code`
- Enforce wrapper envelope fields:
  - `run_id`, `group_id`, `signal`, `wrapper_policy`, evidence refs
- Persist deterministic envelope lineage:
  - `event_id`, `sequence`, `run_id`

Exit criteria:
- Invalid wrappers are rejected/quarantined with explicit errors.
- Replay of same envelope snapshot yields same stored facts.

### K2: Binder v1 (Section 9.4 operationalization)

- Implement binder idempotency key:
  - `(run_id, task_id, group_id, binder_version)`
- Implement derived upsert key:
  - `(scope, target.kind, target.id, action.kind, failure_reason_code, fingerprint_hash, binder_version)`
- Canonicalize and hash fingerprints:
  - sorted gate set, normalized versions/env, canonical JSON bytes, `sha256`
- Expose stable query primitives:
  - `mv_recent_failures_by_taskspec`
  - `mv_gate_rollup_by_failure_reason_code`
  - `mv_guard_denials_by_policy_reason_code`

Exit criteria:
- Reprocessing same input snapshot produces no duplicate derived artifacts.
- Fingerprint hash remains stable across reruns.

### K3: Capsule Maintenance + Prescriptive Gating

- On every binding update:
  - maintain `support_count`, `last_seen_ts`, contradiction counters
- Enforce prescriptive eligibility:
  - confidence threshold
  - staleness threshold
  - guard/policy compatibility
- Enforce fallback semantics:
  - `Strict`, `Hybrid`, `Lenient` with versioned anomaly triggers

Exit criteria:
- Contradiction/staleness degrades prescriptive eligibility deterministically.
- Strict mode never mints derived capsules without explicit failure/denial wrappers.

### K4: python_standard + Pattern Runtime

- Enforce `python_standard` subchecks:
  - contract validity + canonical serialization
  - determinism test(s)
  - side-effects policy enforcement
  - observability semantics split
  - spec-as-test generated assertions
- Add pattern docs into execution wiring:
  - secure map-reduce
  - memory layering model

Exit criteria:
- Capsule-to-tool conformance is gate-verified before trusted use.

## Workstream Breakdown

### Workstream A (`dome`)

1. Planner TaskSpec validation and wrapper schema enforcement.
2. Daemon ingestion + checkpoint/idempotency hardening.
3. Binder v1 implementation (keys, hashing, upserts, views).
4. Retrieval/inference alignment to `failure_reason_code`.
5. CI contract tests against pinned `xtrlv2` artifacts.

### Workstream B (`xtrlv2`)

1. Stabilize and version SSOT schema contracts used by `dome`.
2. Preserve semantics split definitions and migration notes.
3. Provide compatibility fixtures for `dome` contract tests.

## Test Plan (minimum)

1. Semantics split test:
- guard denial must set `policy_reason_code` without overwriting `failure_reason_code`.

2. Binder idempotency test:
- replay same source facts twice -> no duplicate derived rows.

3. Fingerprint stability test:
- identical canonical inputs -> identical `fingerprint_hash`.

4. Wrapper fallback test:
- strict/hybrid/lenient modes produce expected derivation behavior.

5. Query primitive determinism test:
- identical snapshot + identical filters -> identical ordered results.

## Rollout Strategy

1. Shadow mode:
- run binder derivations and confidence maintenance without changing planner selection.

2. Guided mode:
- planner consumes priors as suggestions (no auto-apply).

3. Prescriptive mode:
- enable single-shot eligibility only after thresholds and contradiction safeguards are green.

## Tracking

- Use one issue per milestone (`K0`..`K4`).
- Require explicit “exit criteria met” evidence before milestone closure.
- Keep migration notes in `dome` docs whenever pinned `xtrlv2` schema versions change.
