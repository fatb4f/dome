# Dome TaskSpec Closed-Loop Companion Requirements

Version: `v5`
Generated: `2026-02-16 15:12 UTC`
Canonical status: this is the active Mode A companion for implementation. Superseded revisions are archived under `doc/archive/reviews/` and are non-normative.

Companion to:
- `./dome_task_spec_skills_closed_loop_v5.md`

Purpose:
- Translate the conceptual architecture into explicit functional and technical requirements by topic.

## 1. Purpose and Scope

### Functional Requirements
- The system must execute TaskSpec-driven work in a closed loop from planning through promotion decision.
- The system must treat TaskSpec as the intent-layer authority for worker actions.
- The system must use committed control evidence (exportable to telemetry) as the source for gate and promotion decisions.

### Technical Requirements
- All run-scoped entities must carry `run_id`.
- All task-scoped entities must carry stable `task_id`.
- The pipeline must expose machine-readable artifacts for wave status, gate result, and promotion result.

## 2. Roles and Ownership

### Functional Requirements
- In starter mode, `codex-cli` must assume both planner and coordinator functions.
- `codex-cli` must author TaskSpec graph and wave snapshots.
- `codex-cli` must execute waves, maintain ledger state, and compute gate/promotion outcomes.
- Workers must execute TaskActions and emit evidence only.
- Git operations must be coordinator-only within `codex-cli`.

### Technical Requirements
- Role boundaries must be enforced by API-level permissions.
- Worker runtime must not include callable git-history methods.
- `codex-cli` must expose auditable logs for gate/promotion actions.

## 3. Skills and API Surfaces

### Functional Requirements
- The system must provide separate API surfaces for TaskSpec crafting, loop orchestration, tool execution, and git operations.
- The loop API must support init, dispatch, status, gate computation, and promotion computation.

### Technical Requirements
- Each API method must have versioned request/response schemas.
- API methods must return deterministic status/error codes.
- API calls must be traceable via correlation IDs linked to `run_id` and `task_id`.

## 3.1 Consolidated Pipeline-Skill-Tool Usage Model

### Functional Requirements
- The system must preserve a strict lifecycle: `Packet -> TaskSpec/WaveSpec -> loop dispatch -> worker tool usage -> gate/promotion -> git mutation`.
- Each pipeline stage must map to exactly one authoritative skill surface (craft, loop, tool, git).
- Tool usage must remain subordinate to pipeline stage and role authority.
- Worker spawns must be typed and bounded by `SpawnSpec`.

### Technical Requirements
- Every stage transition must emit a typed control event with `run_id`, `wave_id` (if applicable), and stage name.
- Worker-side side effects must be representable only as `ToolRequest` calls to `dome.api.tool.xtrlv2.*`.
- Coordinator-side repository mutations must be representable only as `dome.api.repo.git.*` calls.
- Traceability must support reverse lookup:
  - from promotion decision -> gate input evidence -> tool calls -> originating TaskSpec action.
- `SpawnSpec` must include:
  - `loop_token` (platform/coordinator-authored, injected at spawn time, immutable for worker execution)
  - `task_spec` slice/reference
  - scoped ToolSDK capability/allowlist
  - initial `action_spec`

## 3.2 Intent/Resolution Definitions

### Functional Requirements
- `task_spec` must encode intent in domain terms: goals, acceptance criteria, constraints, non-goals, and required evidence.
- `tool_contract` must encode the allowed resolution surface for a specific runtime environment.

### Technical Requirements
- `task_spec` must remain mostly tool-agnostic and must not encode concrete method calls.
- `tool_contract` must include method schemas, constraints, error taxonomy, and compatibility/version metadata.
- `task_spec` may declare container and capability requirements, while method-level binding must remain in `tool_contract`.

## 3.3 Type Boundaries: AISDK and ToolSDK

### Functional Requirements
- Workers may reason in AISDK space but may only perform side effects via ToolSDK.
- Violations of `ToolContract` must produce typed errors, not untyped failures.

### Technical Requirements
- AISDK types must include: `TaskSpec`, `WorkerInput`, `WorkerOutput`, `Artifact`, `Decision/Step`, `ErrorSummary`.
- ToolSDK types must include: `ToolContract`, `ToolCall`, `ToolResult`, `ToolError`.
- Execution runtime must enforce a typed bridge: `Decision/Step -> ToolCall -> ToolResult -> Artifact/WorkerOutput`.

## 3.4 `SpawnSpec` Schema Contract

### Functional Requirements
- Every worker invocation must be initialized from a typed `SpawnSpec`.
- `SpawnSpec` must bind one worker to one bounded task slice and one scoped tool contract.
- `SpawnSpec` must include an initial `action_spec` describing the next intended action.

### Technical Requirements
- `SpawnSpec` schema must include at minimum:
  - `spawn_spec_version`
  - `run_id`
  - `spawn_id`
  - `loop_token`
  - `task_ref` (`task_id` + `task_spec_ref`)
  - `tool_contract_ref`
  - `capability_scope`
  - `action_spec`
  - `limits`
  - `versions`
- `loop_token` must be coordinator/platform-authored, injected at spawn time, and immutable for worker execution.
- Runtime must reject any worker attempt to widen `capability_scope` or mutate `task_ref`.
- Runtime must validate all ToolSDK calls against both `tool_contract_ref` and `capability_scope`.

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
- TaskSpec schema must require `primitive_id`, container, ActionSpecs (capability requirements), and capability constraints.
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
- Container-to-capability allowlists must be explicit and validated before dispatch.
- Execution engine must reject undeclared actions and capability escalation attempts.
- PatchProposal artifacts must include deterministic content hashes.
- Worker runtime must be **schema-aware**: it must validate `task_spec` and `tool_contract` against versioned schemas before execution.
- Enforcement must be **strong typing + runtime validation**: compile-time types (TS/Rust/Go/Python) plus runtime validators (JSON Schema / Zod / Pydantic).
- Tool invocation must be guarded by validators:
  - ToolCall must validate against `tool_contract` method schemas before dispatch.
  - ToolResult must validate on decode; unexpected shapes must raise a schema mismatch error.
- Codegen is optional but recommended: generate tool stubs and validators from `tool_contract` schemas to keep the worker thin and prevent schema drift.



## 8. `tool.api` Contract

### Functional Requirements
- `tool.api` must be the only worker-visible side-effect boundary.
- `tool.api` must enforce per-container allowlists and idempotent responses.

### Technical Requirements
- ToolRequest envelope must be versioned and schema-validated.
- Idempotency ledger must return cached outcomes for repeated idempotency keys.
- `tool.api` must exclude git-history methods by contract.
- `tool_contract` must define capability-to-method bindings and resolver rules used to compile intent-level actions into concrete tool calls.

## 9. Closed Loop, Authoritative Ledger, and OTel Export

### Functional Requirements
- Coordinator must treat a ControlEvent ledger as the authoritative run ledger.
- Task completion must require ingestion and acknowledgment of completion events.
- Worker exit must be gated on acknowledgment or explicit timeout policy.

### Technical Requirements
- Control events must include event IDs, sequence numbers, timestamps, and correlation fields.
- Coordinator must persist ack state transitions for every task completion event.
- Timeout/recovery paths must be explicitly modeled and auditable.
- ControlEvent ledger records must be exportable to OTel without loss of identity/correlation semantics.

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
- Determinism is defined modulo `run_id` (authoritative outputs must be equal up to run-scoped identifiers unless `run_id` is deterministically derived).
- Replay execution must be behaviorally equivalent, including decision outcomes and evidence references.
- Determinism applies to authoritative artifacts (`TaskSpec`, `WaveSpec`, `GateResult`, `PromotionResult`, `ControlEvent` ledger); telemetry exports must preserve identity/correlation but may vary in timing fields.

### Technical Requirements
- Canonical serialization: all hashed payloads must use one canonical JSON format (UTF-8, sorted keys, stable number/string encoding).
- Hashing: hash algorithm and version must be fixed and declared (for example `sha256:v1`).
- Stable IDs:
  - `task_id = H(canonical(TaskSpec))`
  - `action_id = H(task_id + container + capability_id + canonical(intent_args))`
  - `tool_call_id = H(run_id + action_id + tool_id + tool_version + canonical(bound_args) + canonical(constraints))`
  - `idempotency_key = H(run_id + tool_call_id + tool_version + canonical(constraints))`
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


---

## 13. Requirement Traceability and Verification

### Functional Requirements
- Every normative requirement must have a stable requirement ID (`CL-REQ-XXXX`).
- Every requirement must define an explicit verification path.

### Technical Requirements
- Requirement records must include:
  - `requirement_id`
  - source section
  - verification type (`unit`, `integration`, `ci-gate`, `audit-query`, `manual-control`)
  - evidence artifact path
- CI must fail if normative requirements are missing IDs or verification mappings.
- Canonical requirement registry source of truth: `requirements.json`.

### Initial Requirement Registry
Snapshot of `requirements.json` for human readability:

| requirement_id | Requirement Summary | Source Section | Verification Type | evidence_artifact_path |
|---|---|---|---|---|
| CL-REQ-0001 | TaskSpec is intent-layer authority; ToolContract is method-layer authority | `doc/graph/dome_task_spec_skills_closed_loop_v5.md` §3.1 | `integration` | `TBD` |
| CL-REQ-0002 | Worker side effects are ToolSDK-only and contract-validated | `doc/graph/dome_task_spec_closed_loop_requirements_companion_v5.md` §3.3 | `integration` | `TBD` |
| CL-REQ-0003 | SpawnSpec required for every worker invocation | `doc/graph/dome_task_spec_closed_loop_requirements_companion_v5.md` §3.4 | `ci-gate` | `TBD` |
| CL-REQ-0004 | ControlEvent ledger is authoritative; OTel is export projection | `doc/graph/dome_task_spec_closed_loop_requirements_companion_v5.md` §9, §14 | `integration` | `TBD` |
| CL-REQ-0005 | Deterministic IDs and replay checks must pass | `doc/graph/dome_task_spec_closed_loop_requirements_companion_v5.md` §12 | `ci-gate` | `TBD` |

## 14. Evidence Authority and Retention Policy

### Functional Requirements
- The ControlEvent ledger is authoritative for execution decisions.
- Control evidence used for gate/promotion decisions must be retained for replay and audit windows.

### Technical Requirements
- OTel exports must be derived from authoritative ControlEvent ledger records.
- OTel export must preserve correlation IDs and decision references.
- Retention and immutability guarantees for the authoritative ledger must be documented and enforced.

## 15. Schema Evolution and Compatibility

### Functional Requirements
- Breaking schema changes must include migration notes and compatibility guidance.
- Runtime must support at least `N-1` schema compatibility for persisted artifacts.

### Technical Requirements
- Every schema must define:
  - semantic versioning strategy
  - compatibility mode (`strict`, `compat`, `migrate`)
  - deprecation windows
- Converters/adapters must be tested for forward/backward transform correctness.

## 16. Error Taxonomy and Failure Classes

### Functional Requirements
- The system must classify failures into standard error classes for policy, schema, tool, transport, and timeout/retry domains.
- Gate and promotion decisions must reference standardized reason codes, not free-form strings.

### Technical Requirements
- A canonical error catalog must define:
  - error code
  - class
  - retryability
  - recommended remediation
- Worker/tool/coordinator APIs must return structured errors with stable codes.
- Error-class coverage must be included in conformance tests.
