# Implementation Plan (Milestone Ordered)

## Planning Inputs
- Requirements registry: `doc/graph/reviewpack_requirements.json`
- Normative requirements doc: `doc/graph/dome_task_spec_closed_loop_requirements_companion_v5.md`
- Milestone baseline: `doc/graph/milestones_objectives_implementation_technical_requirements.md`

## Milestone 1: Authority and Contracts Baseline

### Objectives
- Deliver TaskSpec/ToolContract authority split.
- Enforce typed SpawnSpec at dispatch boundary.

### Work Packages
1. Implement TaskSpec authority guardrails (`C1`).
2. Implement ToolContract/ToolProfile side-effect enforcement in `tool.api` (`C2`).
3. Implement SpawnSpec schema + coordinator fail-closed validation (`C3`).

### Exit Criteria
- No worker method execution outside ToolContract-resolved allowlist.
- SpawnSpec rejects unknown fields and missing required fields.
- `CL-REQ-0001..0003` mapped to automated checks.

## Milestone 2: Closed-Loop Ledger and Deterministic Execution

### Objectives
- Make ControlEvent ledger authoritative.
- Ensure deterministic replay outcomes.

### Work Packages
1. Implement append-only ControlEvent log with sequence/correlation keys (`C4`).
2. Implement deterministic ledger materialization with explicit apply ordering (`C5`).
3. Implement scheduler/selection/conflict tie-break contracts (`C6`).

### Exit Criteria
- OTel export is projection-only from ControlEvent records.
- Replay tests pass for deterministic IDs, ordering, and decision artifacts.
- `CL-REQ-0004..0005` covered by integration + CI/replay checks.

## Milestone 3: Wave Orchestration and Promotion Gates

### Objectives
- Run wave dispatcher loop with deterministic gating/promotion.
- Keep coordinator as sole apply/admin authority.

### Work Packages
1. Implement wave dispatcher and bounded worker spawn flow (`C7`).
2. Implement gate/promotion engine with evidence-linked artifacts (`C8`).

### Exit Criteria
- Dispatch->ingest->gate->promote loop works from authoritative ledger.
- Promotion decisions are reproducible and evidence-traceable.

## Milestone 4: Traceability and CI Hard Gates

### Objectives
- Enforce requirement traceability in CI.
- Prevent spec/doc drift and deprecated path regressions.

### Work Packages
1. Implement requirement-to-check resolver and artifact reporter (`C9`).
2. Implement CI policy gates and lint checks (`C10`).

### Exit Criteria
- CI fails if any `CL-REQ-*` lacks mapped checks/artifacts.
- CI fails on deprecated path references in active docs.
- Traceability reports are published per run.

## Suggested Delivery Sequence
1. M1 foundations (`C1-C3`)
2. M2 determinism core (`C4-C6`)
3. M3 operational loop (`C7-C8`)
4. M4 governance hardening (`C9-C10`)
