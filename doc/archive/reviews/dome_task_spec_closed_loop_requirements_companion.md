# Dome TaskSpec Closed-Loop Companion Requirements

Companion to:
- `doc/reviews/dome_task_spec_skills_closed_loop_v2.md`

Purpose:
- Translate the conceptual architecture into explicit functional and technical requirements by topic.

## 1. Purpose and Scope

### Functional Requirements
- The system must execute TaskSpec-driven work in a closed loop from planning through promotion decision.
- The system must treat TaskSpec as the execution authority for worker actions.
- The system must use telemetry-backed evidence as the source for gate and promotion decisions.

### Technical Requirements
- All run-scoped entities must carry `run_id`.
- All task-scoped entities must carry stable `task_id`.
- The pipeline must expose machine-readable artifacts for wave status, gate result, and promotion result.

## 2. Roles and Ownership

### Functional Requirements
- Planner must author TaskSpec graph and wave snapshots.
- Coordinator must execute waves, maintain ledger state, and compute gate/promotion outcomes.
- Workers must execute TaskActions and emit evidence only.
- Git operations must be coordinator-only.

### Technical Requirements
- Role boundaries must be enforced by API-level permissions.
- Worker runtime must not include callable git-history methods.
- Coordinator must expose auditable logs for gate/promotion actions.

## 3. Skills and API Surfaces

### Functional Requirements
- The system must provide separate API surfaces for TaskSpec crafting, loop orchestration, tool execution, and git operations.
- The loop API must support init, dispatch, status, gate computation, and promotion computation.

### Technical Requirements
- Each API method must have versioned request/response schemas.
- API methods must return deterministic status/error codes.
- API calls must be traceable via correlation IDs linked to `run_id` and `task_id`.

## 4. Packet as RunToken

### Functional Requirements
- Packet must be ingress-only and used only to derive TaskSpec and initial wave context.
- Packet must carry intent, baseline refs, policy refs, and budgets.
- Packet must not carry sandbox/permission mechanics.

### Technical Requirements
- Packet schema must be versioned and validated at ingress.
- Packet fingerprint must be reproducibly computed from canonical packet content.
- Budget fields must be normalized to explicit units and validated against policy limits.

## 5. Planner Decomposition (Primitives and TaskSpecs)

### Functional Requirements
- Planner must decompose work into primitives, atomic sets, and TaskSpecs.
- Each TaskSpec must bind to one primitive or an explicitly declared atomic cluster.
- Planner must publish immutable WaveSpec snapshots.

### Technical Requirements
- TaskSpec schema must require `primitive_id`, container, action bindings, and capability constraints.
- WaveSpec must include `wave_id`, `plan_hash`, and ordered task references.
- Planner revisions must create new `wave_id` values.

## 6. Wave Scheduling

### Functional Requirements
- Scheduler must prioritize blockers and avoid starvation.
- Scheduler must support constrained-piece prioritization and optional endgame handling.

### Technical Requirements
- Scheduling policy must define strict precedence and deterministic tie-break rules.
- Wave ordering decisions must be persisted with rationale metadata.
- Recomputing schedule with identical inputs must yield identical task ordering.

## 7. TaskSpec Execution Contract

### Functional Requirements
- Workers must execute only declared TaskActions.
- Container semantics (`read`, `write`, `update`, `test`) must be enforced.
- Workers must emit PatchProposal artifacts for coordinator-side git application.

### Technical Requirements
- Container-to-method allowlists must be explicit and validated before dispatch.
- Execution engine must reject undeclared actions and capability escalation attempts.
- PatchProposal artifacts must include deterministic content hashes.

## 8. `tool.api` Contract

### Functional Requirements
- `tool.api` must be the only worker-visible side-effect boundary.
- `tool.api` must enforce per-container allowlists and idempotent responses.

### Technical Requirements
- ToolRequest envelope must be versioned and schema-validated.
- Idempotency ledger must return cached outcomes for repeated idempotency keys.
- `tool.api` must exclude git-history methods by contract.

## 9. Closed Loop and OTel Control Evidence

### Functional Requirements
- Coordinator must treat control-plane OTel evidence as the run ledger.
- Task completion must require ingestion and acknowledgment of completion events.
- Worker exit must be gated on acknowledgment or explicit timeout policy.

### Technical Requirements
- Control events must include event IDs, sequence numbers, timestamps, and correlation fields.
- Coordinator must persist ack state transitions for every task completion event.
- Timeout/recovery paths must be explicitly modeled and auditable.

## 10. Hard Gate Confirmation

### Functional Requirements
- Gate decision must derive from TaskSpec, guardrails, invariants, overlays, and evidence bundles.
- Promotion must be blocked until required hard confirmation is recorded.

### Technical Requirements
- Gate computation inputs must be immutable snapshots.
- Overlay schema must allow observations only and reject authority expansion fields.
- Confirmation records must include signer identity, policy basis, and timestamp.

## 11. Out-of-Scope Boundaries

### Functional Requirements
- Sandbox/permission mechanics must remain in runtime state and TaskSpec constraints, not packets/tool.api.
- Git responsibilities must remain isolated in coordinator-only skill surface.

### Technical Requirements
- Boundary checks must fail closed when forbidden fields/functions are present.
- CI policy tests must verify no cross-boundary API regressions.

## 12. Determinism Contract

### Functional Requirements
- Identical inputs, policies, and baseline refs must produce identical TaskSpec, wave order, gate result, and promotion result.
- Replay execution must be behaviorally equivalent, including decision outcomes and evidence references.

### Technical Requirements
- Canonical serialization: all hashed payloads must use one canonical JSON format (UTF-8, sorted keys, stable number/string encoding).
- Hashing: hash algorithm and version must be fixed and declared (for example `sha256:v1`).
- Stable IDs:
  - `task_id = H(canonical(TaskSpec))`
  - `action_id = H(task_id + container + method + canonical(args))`
  - `idempotency_key = H(run_id + action_id + tool_version + canonical(constraints))`
- Ordering:
  - Event ordering must use `(sequence, event_id)` tie-break semantics.
  - Scheduler ordering must use policy precedence + deterministic tie-break fields.
- Time behavior:
  - Gate/promotion computations must not depend on wall-clock time beyond explicit policy windows.
  - Timeout recovery must be deterministic and idempotent.
- Version pinning:
  - `tool_version`, schema versions, and policy versions must be captured in every run manifest.
- Replay validation:
  - Determinism checks must compare plan hash, wave ordering, gate decision payload, and promotion decision payload.

