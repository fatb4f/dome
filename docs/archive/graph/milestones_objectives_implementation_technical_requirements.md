# Dome Graph Fold Milestones: Objectives, Implementation, and Technical Requirements

## Scope
This document defines milestone-level objectives and delivery requirements for wiring the graph-authoritative model in `doc/graph/*` into runtime behavior.

## Milestone 1: Authority and Contracts Baseline

### Objectives
- Establish `TaskSpec` as intent-layer authority.
- Enforce `ToolContract`/`ToolProfile` as method-layer authority.
- Require typed `SpawnSpec` for all worker invocations.

### Implementation
- Implement schema validation gates for `TaskSpec`, `ToolContract`, and `SpawnSpec` prior to dispatch.
- Enforce coordinator-side resolution from capability intent to allowed methods.
- Reject any worker operation that bypasses `tool.api`.

### Technical Requirements
- Must satisfy `CL-REQ-0001`, `CL-REQ-0002`, `CL-REQ-0003`.
- Validation must fail closed on unknown fields and contract violations.
- Contracts must be versioned and backward-compatibility policy documented.

## Milestone 2: Closed-Loop Ledger and Deterministic Execution

### Objectives
- Make ControlEvent ledger authoritative for run-state decisions.
- Ensure deterministic wave scheduling and replay-safe outcomes.
- Ensure OTel is derived export, not control truth.

### Implementation
- Implement append-only ControlEvent log with deterministic apply ordering.
- Build ledger materialization for have/need, task lifecycle, and gating inputs.
- Implement deterministic tie-break rules for scheduler ordering.
- Implement idempotency/replay checks keyed by task/method/run identity.

### Technical Requirements
- Must satisfy `CL-REQ-0004`, `CL-REQ-0005`.
- Same inputs/policy/baseline must produce identical authoritative artifacts modulo run-scoped identifiers.
- Ledger-to-OTel mapping must preserve correlation and identity semantics.

## Milestone 3: Wave Orchestration and Promotion Gates

### Objectives
- Operationalize torrent-like wave execution from TaskSpec graph.
- Enforce hard gates and deterministic promotion/holdback decisions.
- Keep coordinator as sole admin/apply authority.

### Implementation
- Generate WaveSpecs from graph dependencies and policy constraints.
- Execute wave loop: dispatch -> ingest evidence -> gate -> promote/hold -> advance.
- Integrate patch proposal indexing and conflict-aware stack planning.
- Enforce admin-only apply path with immutable decision artifacts.

### Technical Requirements
- Gate decision inputs must include TaskSpec, invariants, evidence bundle, and policy overlays.
- Promotion artifacts must be reproducible and audit-traceable to source evidence.
- Conflict policy and timeout reconciliation must be deterministic.

## Milestone 4: Traceability, CI Gates, and Operational Readiness

### Objectives
- Make requirements traceability executable in CI.
- Detect regressions in authority boundaries and determinism.
- Provide operational confidence for rollout.

### Implementation
- Wire `reviewpack_requirements.json` to automated checks (`integration`, `ci-gate`).
- Add doc lint/check to block deprecated path references (`<deprecated_review_pack_path>`).
- Add conformance tests for TaskSpec/ToolContract split and SpawnSpec constraints.
- Add replay test suite for deterministic IDs and scheduler ordering.

### Technical Requirements
- Every requirement ID must map to at least one automated verification artifact.
- CI must fail on missing traceability evidence.
- Incident/runbook references must align with `doc/graph/*` as SSOT.

## Definition of Done (Cross-Milestone)
- `doc/graph/*` remains the concept-authoritative source.
- All control decisions are reproducible from authoritative ledger artifacts.
- Contract violations fail safely and are observable with typed error classes.
- CI enforces requirement traceability and deprecated-path hygiene.
