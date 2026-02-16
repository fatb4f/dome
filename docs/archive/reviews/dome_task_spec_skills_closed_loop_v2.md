# Dome TaskSpec Closed-Loop Pipeline - Single-Structure Spec

Source PDF: `/home/src404/Downloads/dome_task_spec_skills_closed_loop_v2.pdf`
Version: `v2`
Generated: `2026-02-16 02:30 UTC`

## 1. Purpose
Define a deterministic, idempotent, telemetry-first execution pipeline where TaskSpec is authoritative, workers are ephemeral (`codex-cli`), execution is routed through a unified `tool.api`, and promotion/next-wave decisions are computed from committed OTel evidence in a closed loop.

## 2. Roles and Ownership
Note: the original PDF table wraps aggressively. Content below is normalized from extracted text.

### Planner
- Type: persistent controller (max-stats)
- Owns: TaskSpec graph, wave snapshots, plan refinement state
- Does not own: run ledger tracking, gating/promotion execution

### Coordinator (loop daemon)
- Type: persistent state (min-stats)
- Owns: run ledger from OTel control evidence, TaskSpec staleness/hydration tracking, wave tracking, gating/promotion execution path
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
- Implements closed loop: dispatch -> ingest OTel control evidence -> compute wave outcome -> gate/promo -> next wave request.

### Skill C - `tool.api` (xtrlv2)
- API: `dome.api.tool.xtrlv2.*`
- Unified idempotent tool surface (FS/exec/diff/evidence)
- Enforces per-container allowlists and idempotency keys
- No git operations

### Skill D - Git
- API: `dome.api.repo.git.*`
- Coordinator-only repo authority: apply patch proposals, commit, promote
- Never exposed to workers

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
- Atomic action: one TaskAction bound to one container and one `tool.api` method

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
TaskSpec is authoritative and must declare deterministic containers, per-container tool allowlists, and TaskActions mapping 1:1 to `tool.api` calls.

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
`tool.api` is the only worker-visible side-effect boundary. It enforces per-container method allowlists and implements idempotency via an internal ledger.

ToolRequest envelope (illustrative):

```json
{
  "tool_request_version": "dome.tool.request.v1",
  "run_id": "run-...",
  "task_id": "ts-...",
  "action_id": "ta-...",
  "container": "update",
  "method": "tool.fs.write_atomic",
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
- `action_id = H(task_id + container + method + args)`
- `idempotency_key = H(run_id + action_id + tool_version + constraints)`
- `tool.api` returns cached responses for repeated keys

## 9. Closed loop: OTel control evidence as ledger
Coordinator ingests control-plane OTel evidence and uses it as the ledger for wave completion, gating, promotion, and next-wave computation. Workers must sync OTel before exit.

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
