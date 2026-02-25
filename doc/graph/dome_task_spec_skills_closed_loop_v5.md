# Dome TaskSpec Closed-Loop Pipeline - Single-Structure Spec

Source baseline PDF: `/home/src404/Downloads/dome_task_spec_skills_closed_loop_v2.pdf`
Version: `v5`
Generated: `2026-02-16 15:12 UTC`
Canonical status: this is the active Mode A spec copy for implementation. Superseded revisions are archived under `doc/archive/reviews/` and are non-normative.
## 1. Purpose
Define a deterministic, idempotent, telemetry-first execution pipeline where TaskSpec is authoritative at the intent layer, workers are ephemeral (`codex-cli`), execution is routed through a unified `tool.api`, and promotion/next-wave decisions are computed from committed control evidence in a closed loop.

## 2. Roles and Ownership
Note: the original PDF table wraps aggressively. Content below is normalized from extracted text.

Starter operating mode:
- `codex-cli` assumes both planner and coordinator roles.
- AISDK is used for planning decisions and for generating worker instructions.
- In starter mode, `codex-cli` hosts both logical roles (Planner + Coordinator) in one process; ownership boundaries remain logical.

### Planner
- Type: persistent controller (max-stats)
- Owns: TaskSpec graph, wave snapshots, plan refinement state
- Does not own: run ledger tracking, gating/promotion execution

### Coordinator (loop daemon)
- Type: persistent state (min-stats)
- Owns: run ledger from authoritative ControlEvent records, TaskSpec staleness/hydration tracking, wave tracking, gating/promotion execution path
- Does not own: TaskSpec authoring or wave mutation

### Workers
- Type: ephemeral `codex-cli` subprocesses
- Owns: execution of TaskActions and evidence emission
- Does not own: planning, commit repo history, gating/promotion decisions

### `tool.api` (xtrlv2 skill)
- Type: service/API
- Owns: idempotent tool methods and per-container allowlist enforcement
- Does not own: git/history operations

### Git skill
- Type: service/API
- Owns: apply patch proposals, commit, promote
- Does not own: worker-side operations/access

## 3. Skills (API surfaces)

### Skill A - TaskSpec craft
- API: `dome.api.taskspec.craft`
- Input: Packet (RunToken) + policy refs + repo baseline refs
- Output: TaskSpec graph + primitive/atomic-set decomposition + WaveSpecs

### Skill B - Iteration pipeline
- APIs:
  - `dome.api.loop.init`
  - `dome.api.loop.dispatch_wave`
  - `dome.api.loop.status`
  - `dome.api.loop.compute_gate`
  - `dome.api.loop.compute_promotion`
- Implements closed loop: dispatch -> ingest committed ControlEvents (exportable to OTel) -> compute wave outcome -> gate/promo -> next wave request.

### Skill C - `tool.api` (xtrlv2)
- API: `dome.api.tool.xtrlv2.*`
- Unified idempotent tool surface (FS/exec/diff/evidence)
- Enforces per-container allowlists and idempotency keys
- No git operations

### Skill D - Git
- API: `dome.api.repo.git.*`
- Coordinator-only repo authority: apply patch proposals, commit, promote
- Never exposed to workers

## 3.1 Core Definitions

### `task_spec` = intent
What the worker must accomplish, expressed in domain terms:
- goal and acceptance criteria
- inputs and constraints
- non-goals
- required evidence/artifacts to return

Property:
- mostly tool-agnostic; it may name required capabilities but must not encode exact method calls.

### `tool_contract` = resolution surface
What the worker is allowed/able to do to resolve the intent:
- available tools and methods
- typed request/response schemas
- constraints (allowlists, rate limits, sandbox rules, IO limits)
- error taxonomy
- version and compatibility information

Property:
- environment-specific; binds execution to concrete interfaces.
- Authority split: `task_spec` is authoritative over intent-level actions, containers, and capability requirements; `tool_contract` is authoritative over method-level bindings and invocation semantics.

## 3.2 Consolidated Concept Flow: Pipeline -> Skills -> Tool Usage

This section consolidates the operating model from intent ingress to promotion:

1. Pipeline stage: Ingest and shape
- Input enters as Packet/RunToken.
- `codex-cli` (planner role) uses AISDK and `dome.api.taskspec.craft`.
- Output: immutable planning artifacts (`TaskSpec`, `WaveSpec`).

2. Pipeline stage: Wave dispatch and orchestration
- `codex-cli` (coordinator role) dispatches wave tasks and tracks run ledger state via `dome.api.loop.*` (`init`, `dispatch_wave`, `status`).
- Output: execution state transitions and control events.

3. Pipeline stage: Worker execution
- `codex-cli` spawns ephemeral workers using typed `SpawnSpec` containing:
  - `loop_token` (platform/coordinator-authored, injected at spawn time, immutable for the worker)
  - `task_spec` slice or reference
  - ToolSDK capability/allowlist for that spawn
  - initial `action_spec` ("what to do next")
- Workers execute TaskActions only via `tool.api` / ToolSDK calls permitted by `tool_contract`.
- Tool usage boundary:
  - container-level capability allowlists (intent-level)
  - method-level allowlists enforced by `tool.api`, resolved from `tool_contract`
  - idempotency-keyed requests/responses
  - no git-history operations

4. Pipeline stage: Gate and promotion computation
- Coordinator computes deterministic `GateResult` and `PromotionResult`.
- Skill used: `dome.api.loop.compute_gate`, `dome.api.loop.compute_promotion`.
- Output: decision artifacts tied to evidence references.

5. Pipeline stage: Repository mutation
- `codex-cli` applies worker PatchProposals and performs commit/promotion.
- Skill used: `dome.api.repo.git.*`.
- Tool usage boundary:
  - coordinator authority (inside `codex-cli`)
  - auditable commit/promotion trail

Consolidation principle:
- Pipeline defines lifecycle order.
- Skills define authority boundaries.
- Tool usage defines allowable side effects and enforcement.

## 3.3 Type Boundaries: AISDK vs ToolSDK

AISDK types:
- `TaskSpec`
- `WorkerInput`
- `WorkerOutput`
- `Artifact`
- `Decision` / `Step`
- `ErrorSummary`

ToolSDK types:
- `ToolContract`
- `ToolCall`
- `ToolResult`
- `ToolError`

Boundary rule:
- Worker can reason in AISDK space.
- Worker can only act via ToolSDK calls permitted by `ToolContract`.
- Tool contract violations must be returned as typed `ToolError` and surfaced as `ErrorSummary`.

## 3.4 Typed `SpawnSpec` (illustrative schema)

`SpawnSpec` is the bounded execution handoff created by `codex-cli` at worker spawn.

```json
{
  "spawn_spec_version": "dome.spawn_spec.v1",
  "run_id": "run-...",
  "spawn_id": "spawn-...",
  "loop_token": "ltok-...",
  "task_ref": {
    "task_id": "ts-...",
    "task_spec_ref": "taskspec://run-.../ts-..."
  },
  "tool_contract_ref": "toolcontract://xtrlv2/v1",
  "capability_scope": {
    "containers": ["read", "update", "test"],
    "capabilities": ["fs.read", "fs.write_atomic", "exec.run", "evidence.emit"]
  },
  "action_spec": {
    "action_id": "act-...",
    "capability_id": "fs.write_atomic",
    "intent_args_ref": "artifact://run-.../intent-args/act-....json"
  },
  "limits": {
    "max_tool_calls": 50,
    "max_seconds": 600
  },
  "versions": {
    "task_spec_version": "dome.taskspec.v1",
    "tool_contract_version": "dome.tool_contract.v1"
  }
}
```

`SpawnSpec` authority rules:
- `loop_token` is platform/coordinator-authored and immutable for workers.
- workers must not widen `capability_scope` or mutate `task_ref`.
- all ToolSDK calls must be validated against `tool_contract_ref` and `capability_scope`.

## 4. Packet as RunToken (handoff token)
Packet is the pipeline init token. It is ingress-only and discardable after TaskSpec derivation. It must not contain sandbox/perms; those belong to TaskSpec and/or Codex runtime state.

Packet minimal shape (illustrative):

```json
{
  "packet_version": "dome.packet.v1",
  "run_id": "run-...",
  "packet_fingerprint": "sha256:...",
  "intent": {
    "kind": "issue|prompt|job",
    "id": "...",
    "text": "..."
  },
  "inputs": {
    "repo_ref": {
      "repo": "dome",
      "base_ref": "sha|tag"
    }
  },
  "targets": [
    {
      "kind": "path|component",
      "id": "tools/orchestrator"
    }
  ],
  "policy_refs": {
    "reason_codes": "vX",
    "gate_rules": "vY"
  },
  "budgets": {
    "max_seconds": 3600,
    "max_tool_calls": 1000
  }
}
```

## 5. Planner decomposition: layered primitives -> atomic sets -> TaskSpecs
- Primitive: logical unit of work (diagnose, transform, verify, etc.)
- Atomic set: minimum set of atomic actions required to resolve a primitive
- Atomic action: one TaskAction bound to one container and one capability requirement

Layer model (planner-owned):
- `L0 Observe -> L1 Diagnose -> L2 Transform -> L3 Verify -> L4 Gate Inputs`
- Coordinator never edits these layers; it executes and records outcomes.

Primitive resolution rule:
- Each TaskSpec must bind to exactly one `primitive_id` (or explicitly declared atomic cluster).
- Completion produces observable artifacts and/or invariant truth values, recorded as evidence bundles.

## 6. Wave organization: bottom-up torrent-style scheduling
Waves are built bottom-up from resolved atomic sets, analogous to torrent piece scheduling:
- pieces = primitives/atomic sets
- ledger = have/need map
- prioritization = starvation prevention

Wave scheduling heuristics (planner output):
- most-blocking-first (max downstream unlock)
- rarest-first (most constrained primitives)
- optional shortest-first for faster feedback
- optional endgame redundancy for final blockers (safe due to idempotency keys)

WaveSpec immutability per wave:
- Planner publishes a WaveSpec snapshot (`taskspec refs + plan_hash`)
- Coordinator executes it immutably
- Any planner revision creates a new `wave_id`

## 7. TaskSpec execution contract
TaskSpec is authoritative and must declare deterministic containers, capability requirements, and TaskActions mapped to intent-level actions (not concrete tool methods).

Containers:
- `read`: observe-only
- `write`: create new artifacts atomically
- `update`: modify existing artifacts via atomic replace/patch proposal
- `test`: run deterministic checks; capture evidence

Git definition (skill boundary):
- Git is a separate skill.
- Workers and `tool.api` must not perform git-history operations.
- Workers produce PatchProposal artifacts.
- Coordinator applies/commits via Git skill after gating.

## 8. `tool.api` (xtrlv2) contract
`tool.api` is the only worker-visible side-effect boundary. It enforces per-container method allowlists resolved from `tool_contract` and implements idempotency via an internal ledger.

ToolRequest envelope (illustrative):

```json
{
  "tool_request_version": "dome.tool.request.v1",
  "run_id": "run-...",
  "task_id": "ts-...",
  "action_id": "ta-...",
  "container": "update",
  "method": "dome.api.tool.xtrlv2.fs.write_atomic",
  "args": {
    "path": "...",
    "content_ref": "..."
  },
  "constraints": {
    "allowed_roots": ["./"],
    "network": false
  },
  "idempotency_key": "idem-...",
  "tool_version": "xtrlv2@..."
}
```

Idempotency chain:
- `task_id = H(TaskSpec)`
- `action_id = H(task_id + container + capability_id + canonical(intent_args))`
- `tool_call_id = H(run_id + action_id + tool_id + tool_version + canonical(bound_args) + canonical(constraints))`
- `idempotency_key = H(run_id + tool_call_id + tool_version + canonical(constraints))`
- `tool.api` returns cached responses for repeated keys

## 9. Closed loop: ControlEvent ledger and OTel export
Coordinator uses an authoritative ControlEvent ledger for wave completion, gating, promotion, and next-wave computation. OTel MAY be used as an export/observability channel for the same control events. Worker must emit `task.completed` and block until coordinator `task.ack` (or deterministic timeout path) before exit.

Commit barrier:
- A task is complete only when coordinator has ingested the worker `task.completed` control event and acknowledged it.
- Worker blocks exit until ack (or times out, triggering staleness).

## 10. Hard gate confirmation (explicit control point)
Gate is computed deterministically from:
- TaskSpec
- `schema_guardrails`
- boolean invariants
- `post_task` overlay
- evidence bundles

Hard confirmation (human or privileged signer) is recorded when required and blocks promotion.

Gate inputs and overlays:
- `post_task` overlay is coordinator-derived and records observations only (artifacts, hashes, test results, tool call outcomes)
- Overlay must not widen TaskSpec authority (no new actions, no expanded capabilities)

## 11. What is removed from packets and `tool.api`
Packets and `tool.api` do not carry sandbox/permission mechanics. Sandbox/perms are Codex runtime state and/or TaskSpec constraints. `tool.api` contains no git functions; git is a separate skill invoked only by coordinator.


## 12. Implementation patterns (schema-aware runtime)

After ingress, all execution must be type-interface-bound:

- **Worker runtime is ai-sdk typed** and must parse/validate `task_spec` and the associated `tool_contract` (provided in `WorkerInput`).
- **Strong typing + runtime validation**: compile-time types (TS/Rust/Go/Python) **plus** runtime validators (JSON Schema / Zod / Pydantic).
- **Validation gates**:
  - validate WorkerInput (`task_spec`, `tool_contract`) before any work
  - validate each ToolCall against `tool_contract` before dispatch
  - validate ToolResult decoding and final WorkerOutput artifacts
- **Codegen (optional but recommended)**: generate tool stubs and validators from `tool_contract` schemas to keep the worker thin and prevent drift.



---

## 13. Canonical Schemas (normative)
The pipeline MUST publish versioned machine-readable schemas for all protocol surfaces:

- Packet / RunToken: `Packet`
- Plan/Execution surfaces: `TaskSpec`, `WaveSpec`
- Tool boundary: `ToolRequest`, `ToolResult`
- Control ledger events: `ControlEvent`

Control events MUST include, at minimum:
- `task.completed`
- `task.ack`
- `task.timeout`
- `task.retry`
- `gate.computed`
- `promotion.computed`

## 14. Outcome Artifact Contracts (normative)
The system MUST emit exact, schema-validated artifact payloads for:

- `WaveStatus`
- `GateResult`
- `PromotionResult`

Each outcome payload MUST include:
- identity: `run_id`, `wave_id` (where applicable)
- versioning: schema version + policy version
- decision fields: status enum + reason fields
- references: evidence bundle links/hashes used in decision computation

## 15. Ack/Timeout State Machine (normative)
Task completion MUST follow an explicit coordinator state machine.

Required states:
- `DISPATCHED`
- `COMPLETED_UNACKED`
- `ACKED`
- `TIMED_OUT`
- `RETRY_SCHEDULED`
- `FAILED_TERMINAL`

Required rules:
- Duplicate `task.completed` events MUST be idempotently folded by `(run_id, task_id, event_id)`.
- Late events after `TIMED_OUT` MUST be reconciled deterministically via a documented precedence rule.
- Retries MUST preserve parent-child linkage and bounded retry policy.

## 16. Capability Discovery (normative)
The runtime MUST expose a capability discovery endpoint (or equivalent handshake) returning:

- tool catalog and method names
- schema and runtime versions (`tool_request_version`, `tool_version`)
- per-container constraints and allowlists

For large catalogs, progressive discovery MAY be supported:
- names only
- names + summaries
- full schemas

## 17. Conformance and Evolution Policy (normative)
The project MUST maintain a conformance suite in CI that proves:

- replay determinism (`same inputs -> same outputs`)
- boundary enforcement (deny-by-default for out-of-contract actions)
- schema validation for emitted events/artifacts

Compatibility policy MUST define:
- support window (minimum `N-1` schema compatibility)
- deprecation windows and migration guidance
- conversion behavior for older artifacts
