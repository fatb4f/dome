# Contract-based orchestration with torrent-like waves and stacked patch integration (living doc)

## Purpose

Define an execution model for **ephemeral, schema-bound workers** spawned from a coordinator/planner in **waves**, using **least-privilege ToolProfiles** and **BitTorrent-like scheduling**. Workers propose **patch layers**; a coordinator composes them on a single **integration worktree canvas** under **admin-only** capabilities.

---

## 1) Definitions

### Standard envelope (required for all artifacts and events)

All system objects (ToolProfiles, TaskSpec slices, PatchProposals, StackPlans, ApplyResults, validation reports, promotion decisions, ledger events) MUST be wrapped in a consistent envelope to make audit/replay deterministic.

#### Preferred (vendored) standard: `ssot/schemas/event.envelope`

When available, use the vendored SSOT schema as the canonical envelope (mocked here as if present in-repo):

- `event.envelope` provides: `schema_version`, `sequence`, `event_id`, `ts`, `topic`, `run_id`, `payload`.
- System artifacts may either:
  1. be embedded as the `payload` of an `event.envelope` event, or
  2. be stored as standalone JSON artifacts that are also emitted as envelope events.

#### Artifact header fields (minimum; carry in either the artifact body or in the envelope payload)

- `artifact_kind` (e.g., `dome.tool_profile/v0.1`, `dome.patch_proposal/v0.1`)
- `version`
- `object_id` (content-addressed or UUID; unique within run)
- `run_id`, `wave_id`, `task_id/node_id` (as applicable)
- `base_ref` (commit SHA) and optional `base_tree_hash`
- timestamps: `created_at` (and for credentials: `issued_at`, `expires_at`)
- provenance: `producer`/`issuer`, optional `subject`
- determinism: `determinism_seed`, `inputs_hash` (recommended)
- integrity: `payload_digest` + `canonicalization` identifier
- signature material where needed: `kid`, `signature`

**Canonicalization:** every digest/signature MUST specify the canonicalization algorithm/version.

---

### High-level SSOT constructs (vendored; treated as present)

The following SSOT schemas are treated as authoritative interface points for orchestration state and promotion workflows:

- **Run manifest:** `dome.run.manifest/*` — pinned refs and environment facts for reproducibility.
- **Work queue:** `dome.work.queue/*` — the coordinator’s executable plan (tasks, caps, budgets).
- **Task result:** `dome.task.result/*` — per-task completion + emitted artifact refs.
- **Gate decision:** `dome.gate.decision/*` — pass/fail against gates with reason codes + telemetry refs.
- **Promotion decision:** `dome.promotion.decision/*` — promotion approvals tied to evidence.
- **Evidence capsule/bundle:** `dome.evidence.capsule/*`, `dome.evidence.bundle/*` — immutable evidence objects.

These map to the living-doc artifacts as follows:

- **TaskSpec node** ↔ `work.queue.tasks[*]` entry (capabilities + required outputs)
- **PatchProposal / StackPlan / ApplyResult / ValidationReport** ↔ referenced from `task.result` and emitted as `event.envelope.payload`
- **PromotionDecision** ↔ `promotion.decision` (must reference: stack/apply/validation evidence chain)

---

### Repo layout for artifacts (monorepo-friendly; mocked vendored)

Use a stable on-disk layout for generated artifacts that mirrors SSOT examples:

```text
ops/
  runs/<run_id>/
    work.queue.json
    events/
      event.<sequence>.json
    tasks/
      <task_id>/
        task.result.json
        outputs/
          ... (PatchProposals, evidence, logs)
    gate/
      gate.decision.json
    promotion/
      promotion.decision.json
```

This is compatible with “stacked patch integration canvas” because the coordinator can:

- read `work.queue.json`
- materialize tasks as waves
- persist `task.result` + PatchProposals
- emit gate + promotion decisions with evidence bindings

### SkillContract

A **typed API contract** (versioned schemas + semantics + error taxonomy).

- **Contract ID + version**: `contract_id@semver`
- **Methods**: typed request/response schemas
- **Semantics**: invariants, idempotency rules, side-effects
- **Error taxonomy**: structured error codes, retryability

### Tool

A method within a SkillContract.

### ToolProfile

A scoped, least-privilege slice of a SkillContract (subset of methods + constraints + limits) issued per worker spawn.

- `Tool ⊂ SkillContract`
- Worker receives: `ToolProfile ⊂ SkillContract`

### Capability classes

Treat these as **enforced capability classes**, not labels:

- **read**: observation-only (no mutation)
- **write**: bounded mutation (artifact creation / patch proposal / atomic write), **no repo history mutation**
- **admin**: privileged orchestration (gate/promo, repo mutation, policy overrides)

---

## 2) Enforcement rules

### Anti-replay requirement (ToolProfiles)

ToolProfiles are treated as **capability-bearing credentials** and must be non-replayable in practice.

Required properties:

- short-lived TTL (`issued_at`/`expires_at`)
- unique nonce (`jti`) with server-side replay detection
- binding to `run_id`/`wave_id` and intended `audience`
- signature over a canonical form of the whole profile

### Least privilege

- Worker ToolProfiles may include only **read/write** tools.
- **admin tools are coordinator-only**.
- “Planner-in-hat” mode must not grant itself admin tools unless it is explicitly acting as coordinator.

### A2A-style interoperability (Cards → ToolProfiles)

- **Agent Card**: supply-side capability advertisement (max capabilities)
- **ToolProfile**: demand-side scoped grant for a specific spawn/run

`ToolProfile = policy ∩ required_capabilities(node) ∩ Card`

---

## 3) Execution model: graph → on-demand ephemeral runtime + ToolProfile

### Determinism requirement

Planner/scheduler decisions must be replayable from:

- TaskSpec graph
- policy
- ledger event log
- `determinism_seed`

Coordinator must persist the seed and decision artifacts (e.g., StackPlan, scheduling decisions) as enveloped, signed objects.

### TaskSpec graph

Planner emits a **TaskSpec graph** where nodes declare:

- `containers[]` (runtime/container requirements)
- `required_capabilities[]` (read/write/admin classes)
- `required_outputs/evidence[]` (typed artifacts)

**Nodes do not declare methods.** They declare capability needs and required outputs.

### Resolver rules

Capability→method mapping lives in the **ToolContract/ToolProfile resolver**, not in TaskSpec.

### Core loop

For each node (or batch/wave):

1. `required_capabilities = required_capabilities(node)`
2. `tool_profile = policy ∩ tool_contract ∩ required_capabilities`
3. Spawn ephemeral worker with:
   - `task_spec_slice/ref`
   - `tool_profile`
   - `action_spec` (intent-level)
4. Worker compiles intent → concrete tool calls using ToolProfile

**Key property:** runtime + ToolProfile are regenerable on demand from graph + policy → scalable audit + reproducibility.

### SpawnSpec (required boundary contract)

Every worker invocation MUST be dispatched with a typed `SpawnSpec`. Coordinator MUST validate the schema before dispatch and fail closed on unknown or invalid fields.

Required fields:

- `run_id`
- `wave_id`
- `node_id`
- `node_execution_id`
- `task_spec_ref` (pinned ref/hash)
- `tool_profile_ref` (pinned ref/hash)
- `container_ref` (image digest)
- `action_spec` (intent-level action only)
- `determinism_seed`
- `inputs_hash`

Required validation contract:

- Unknown fields at the SpawnSpec boundary are rejected.
- Missing required fields are rejected.
- `task_spec_ref` and `tool_profile_ref` must resolve to immutable refs.
- Dispatch is denied unless coordinator-side validation passes.

---

## 4) Why this scales to “BitTorrent waves”

### Idempotency and endgame safety (required)

Endgame duplication is safe **only** if all write-capable methods are idempotent under a required idempotency key, and the system enforces dedupe.

Required:

- Every write tool call includes `idempotency_key`.
- Tool contracts declare a side-effect class and idempotency semantics.
- Coordinator records and rejects/replays safely on duplicate `(method, idempotency_key, run_id)`.

### BitTorrent properties

- pieces are independent-ish
- rarity/constraint awareness guides scheduling
- duplication near the end is safe

### System analog

- **pieces** = tasks (graph nodes) and/or patch layers (see §6)
- **ledger** = have/need state (evidence + completion acks)
- **rarity** = scarce ToolProfiles / scarce resources / high-blocker tasks
- **endgame** = duplicate execution of last blockers (safe via idempotency + scoped ToolProfiles)

### Deterministic scheduler priorities

- **most-blocking-first**: maximize unlocks (critical path / fan-out)
- **rarest-first**: scarce profiles/resources first
- **endgame redundancy**: bounded duplication for final blockers

---

## 5) Minimal artifacts (formal schemas)

### Enforcement hooks (required, not just conceptual)

The system must define *where* and *how* ToolProfile constraints are enforced.

Required enforcement points:

- **Credential verification:** signature, TTL, jti replay check, run/wave/audience binding (before any tool call).
- **Sandboxing:** OS/container enforcement for file paths, network, and exec.
  - Examples: container runtime policy (mounts/readonly), seccomp/AppArmor, network namespace deny-by-default.
- **Budget accounting:** deterministic counters for calls/time/retries.
  - Define what counts as a “call” (tool invocation boundary), and how time is measured (wall vs CPU).
  - Retries must be coordinator-governed and charged against budgets.
- **Revocation semantics:** coordinator can revoke grants prior to `expires_at`.
  - Minimum: maintain a revocation list keyed by `jti` or `profile_id`.

### A) ToolProfile schema (grant issued to a worker)

Fields:

- `profile_id`
- `contract_id@version`
- **Grant binding (anti-replay):**
  - `issued_at` (RFC3339)
  - `expires_at` (RFC3339; short TTL)
  - `jti` (nonce / unique token id)
  - `audience` (e.g., `worker_runtime`, `container_id`, or `cluster`)
  - `run_id` and `wave_id` (bind grant to a specific execution)
  - `worker_id` (optional; bind to spawn identity)
  - `single_use` (bool; recommended true for write-enabled profiles)
- `allowed_methods[]` **or** `allowed_capabilities[]` (+ resolver mapping)
- `constraints`: roots/network/exec limits, allowed paths, env
- `budgets`: max calls, max seconds, max tokens, cost caps
- `issuer`: coordinator identity
- **Signature:**
  - `kid` (signing key id)
  - `signature` over the canonicalized ToolProfile payload (including all bindings)

**Verification rules (required):**

- Reject expired grants; reject unknown `kid`.
- Reject reused `jti` (store a spent-token set per issuer + TTL window).
- Reject mismatched `audience`, `run_id`, `wave_id` (and `worker_id` if bound).
- For `single_use=true`: mark spent on first successful write call.

### B) TaskSpec node requirements (planner declaration)

Fields:

- `node_id`
- `containers[]`
- `required_capabilities[]`
- `required_outputs/evidence[]` (typed)
- `dependencies[]` (edges)
- **node\_execution\_id schema:**
  - `node_execution_id` is minted by the coordinator for each attempt and is the root for idempotency.
  - All worker write calls and artifact submissions for that attempt must include `node_execution_id`.

**Graph integrity rules (required):**

- Reject duplicate `node_id`.
- Reject unknown dependency IDs.
- Reject self-dependencies.
- Cycles:
  - either reject by default, or require explicit cycle annotation + bounded iteration policy.

### C) Resolver rules (capability→method)

- encoded in ToolContract/ToolProfile, not TaskSpec

---

## 6) Patch-first composition on an integration worktree (preferred workflow)

### Objective

Ephemeral workers propose **patch layers**. A coordinator stacks patches on a single **integration worktree canvas** until constraints are met.

### Roles

- **Workers (read/write only):** may observe and submit patch artifacts; must not mutate repo history.
- **Coordinator (admin):** owns integration worktree, applies patches, checkpoints commits, runs privileged validations, promotes results.

### Recommended skills

#### RepoReadSkill\@vX (read)

Examples:

- `read_file`, `list_tree`, `grep`, `get_base_ref`, `get_diff_stats`

#### PatchProposalSkill\@vX (write)

Examples:

- `submit_patch(PatchProposal, idempotency_key)`
- `submit_metadata(proposal_id, meta, idempotency_key)`

Write-method requirements:

- **Idempotency key required** for every write method call.
- Methods must declare **side-effect class**:
  - `none` (pure)
  - `artifact_put` (content-addressed write)
  - `proposal_register` (register proposal metadata)
- Coordinator enforces deduplication by `(method, idempotency_key, run_id)`.

**No:** `git apply`, `commit`, `merge`, `promote`.

#### RepoIntegrationAdminSkill\@vX (admin, coordinator-only)

Examples:

- `create_integration_worktree(base_ref)`
- `apply_patch(proposal_id, mode=index|three_way)`
- `checkpoint(label)`
- `run_validation(profile)`
- `rollback(checkpoint_id)`
- `promote(integration_head)`

---

## 7) PatchProposal and stacking artifacts

### Patch overlap / conflict model (required)

To make stacking reliable, the coordinator must define what constitutes overlap and how it is detected.

**Overlap levels (supported):**

- **file-level:** same path touched (coarse)
- **hunk-level (recommended default):** overlapping line ranges within a file
- **AST-level (optional):** normalized semantic regions (language-specific)

**Stable fingerprint scheme (hunk-level):** Each hunk fingerprint must declare:

- `path`
- `base_ref`
- `base_context_digest` (hash of normalized preimage context)
- `edit_digest` (hash of normalized inserted/removed lines)
- `range_hint` (optional; start/end line numbers on base)
- `fingerprint_version`

Normalization rules must be specified (e.g., line ending normalization, whitespace policy) and included in `fingerprint_version`.

**Coordinator overlap decision rules:**

- Two proposals overlap if any fingerprints share the same `path` and intersect by `range_hint`, OR if `base_context_digest` collisions occur with incompatible `edit_digest`.

**Patch splitting protocol (required when split is used):**

- Coordinator issues a `SplitRequest` artifact referencing `proposal_id` and requested partitioning policy:
  - `by_file`, `by_hunk`, or `by_region`
- Worker returns `SplitResult` with `proposal_id_A`, `proposal_id_B`, each with their own digests and bindings.
- Splits must preserve provenance links to the original proposal.

### PatchProposal (worker output artifact)

Minimum fields:

- `proposal_id`
- `base_ref` (**must** be an immutable commit SHA; must match wave base)
- **Parent binding (integrity / TOCTOU defense):**
  - `base_tree_hash` (tree hash for `base_ref`)
  - `diff_canonicalization` (algorithm/version)
  - `diff_digest` (e.g., sha256 of canonicalized diff payload)
  - `diff_ref` (content-addressed blob ref) and/or `diff_unified`
- `touched_files[]`
- `intent_tags[]` (tests/docs/refactor/bugfix)
- `risk` (surface area, deps touched, migration flags)
- optional: `hunk_fingerprints[]` (for overlap detection)
- `declared_constraints` (e.g., no deps, no API change)
- `worker_run_meta` (tool\_profile\_id, run\_id, wave\_id, budgets used)

**Coordinator verification rules (required):**

- Resolve `base_ref` → tree; reject if computed tree hash ≠ `base_tree_hash`.
- Canonicalize diff using `diff_canonicalization`; reject if digest ≠ `diff_digest`.
- Apply-check must be evaluated against the exact `base_ref` (not a branch name).

### StackPlan (coordinator artifact)

- `stack_plan_id`
- `base_ref`
- `ordered_proposals[]`
- `rejected[]` with reasons (policy/conflict/redundant)
- `checkpoint_strategy` (per-layer vs per-batch)
- `expected_validations[]`
- **decision determinism:**
  - `determinism_seed`
  - `selection_scores[]` (optional but recommended for audit)

### Decision artifacts (recommended)

To avoid ad hoc audits, persist coordinator decisions as enveloped artifacts:

- `SchedulingDecision` (which nodes spawned, why)
- `SelectionDecision` (why proposals were accepted/rejected)
- `ConflictDecision` (reorder/split/resolver/human)

### ApplyResult (coordinator artifact)

Per proposal:

- `applied`: boolean
- `conflict_summary`: files/hunks
- `checkpoint_id` / resulting `head_ref`

---

## 8) Integration canvas workflow (stacked patches)

### Evidence binding (required)

Every applied patch and checkpoint must be tied to the evidence that justified it.

Required bindings:

- Each apply produces an `ApplyResult` containing:
  - `proposal_id`, `diff_digest`, `base_ref`, resulting `head_ref`, `checkpoint_id` (if any)
- Each validation produces a `ValidationReport` bound to:
  - `head_ref` (or `checkpoint_id`)
  - the set of `proposal_id`s included in that head
  - toolchain/environment identifiers (container image digests)

These artifacts are necessary inputs to promotion.

### 0) Initialize

- Coordinator creates integration worktree at `BASE=base_ref`.
- Canvas state changes only via coordinator admin tools.

### 1) Propose (parallel, wave)

- Spawn N ephemeral workers with least-privilege ToolProfiles.
- Each worker submits PatchProposal artifacts.

### 2) Pre-filter (cheap gates)

- schema validation
- policy checks (forbidden paths, size limits)
- apply-check simulation on clean base (coordinator side)

### 3) Index + plan

- compute overlap (files; optional hunks)
- choose ordering:
  - low-risk/non-overlapping early
  - deps/lockfiles gated/late
  - critical-path pieces early

### 4) Apply (admin-only)

- Apply each patch onto the integration worktree:
  - prefer `--index` + 3-way apply semantics (implementation detail)
- After each accepted patch (recommended): checkpoint commit

### 5) Validate constraints

- run fast checks early; full suite near acceptance

### 6) Conflict policy

If apply fails:

1. retry later (reorder)
2. **split (guarded):** apply non-conflicting hunks **only if policy allows** and proposal declares an `atomicity` policy of `hunk_ok`.
   - if split is used, escalate validation scope (at least targeted tests for touched areas)
   - record a derived proposal id and provenance linking to the parent proposal
3. spawn resolver worker targeting current head
4. drop if low value

**Atomicity policy (recommended):**

- default: `atomic_proposal` (all-or-nothing apply)
- allowed by policy: `atomic_file` (file-by-file)
- rarely: `hunk_ok` (hunk-split), only with validation escalation

### 7) Advance wave baseline

When the canvas has moved substantially:

- start a new wave with `BASE := current integration head`
- spawn workers from that new baseline

### Termination

Stop when:

- constraints satisfied
- budgets exhausted
- human gate required

### Promotion / gating (first-class)

Promotion is permitted only when the coordinator can present a complete, signed chain of evidence:

**Necessary and sufficient artifacts (minimum):**

- `StackPlan` (selected proposals + determinism seed)
- `ApplyResult[]` for every applied proposal (with digests)
- `ValidationReport[]` meeting policy thresholds (e.g., required suites)
- `PromotionDecision` stating:
  - `from_head_ref` → `to_ref` (target branch/ref)
  - policy version
  - evidence references (IDs/digests)

**Policy must define:**

- which validation suites are required for which risk classes
- whether per-layer validations suffice or only final-head validations count
- whether any human approval is required by risk class

---

## 9) “Can the same file be tracked twice?” (operational answer)

- In a **single worktree/index**: a path has one staged/working state at a time.
- In this architecture: multiple workers can propose different states for the same file via **distinct PatchProposals**.
- The coordinator composes/chooses/merges at stacking time; alternatives can be kept as separate proposals or separate candidate stacks.

---

## 10) Scheduler design (torrent-like)

### ControlEvent authority and OTel derivation (required)

`ControlEvent` is the authoritative control-plane event type for execution decisions. OTel is derived telemetry export and must never be used as control truth.

Required ControlEvent contract:

- Topic taxonomy includes, at minimum: `task.dispatched`, `task.progress`, `task.completed`, `task.ack`, `task.timeout`, `gate.computed`, `promotion.computed`.
- Ordering keys include:
  - `sequence` (monotonic per run) as primary
  - `event_ts`, then `event_id` as deterministic tie-breakers
- Correlation keys include `run_id`, `wave_id`, `node_id`, `node_execution_id`, `task_id`.

Required OTel mapping contract:

- OTel spans/logs are projections of ControlEvent records.
- Export must preserve stable correlation IDs and decision references.
- If OTel and ledger disagree, ControlEvent ledger wins.

### Ledger consistency model (required)

The have/need ledger must define a concurrency contract.

Recommended default:

- **Single-writer coordinator** maintains the authoritative ledger state.
- All worker results are submitted as append-only events.
- Coordinator applies events in a deterministic order to derive ledger state.

If multi-writer is required:

- Use an append-only event log with optimistic concurrency:
  - every update includes `expected_ledger_version`
  - conflicting updates are retried by the coordinator

### Ledger (have/need)

- have: validated PatchProposals, passing checkpoints, satisfied node evidence
- need: unmet outputs, failing validations, unresolved conflicts

### Priority scoring (conceptual)

Combine:

- **blocking score** (unlocks downstream nodes)
- **rarity score** (scarce ToolProfiles/resources)
- **confidence score** (prior success signals; low overlap)
- **risk penalty** (broad changes, lockfiles, critical paths)

### Deterministic tie-break contracts (required)

When primary scores are equal, the system MUST apply deterministic tie-breakers.

Required tie-break order:

- Scheduling order (`SchedulingDecision`): `node_priority_group`, then `node_id`, then `task_spec_digest`.
- Proposal selection (`SelectionDecision`): `proposal_id`, then `created_at`, then `diff_digest`.
- Conflict arbitration (`ConflictDecision`): `policy_precedence`, then `proposal_id`, then `conflict_fingerprint`.

These tie-break fields must be persisted in decision artifacts for replay audit.

### Endgame mode

When remaining blockers are few:

- duplicate execution of last blockers with bounded parallelism
- accept the best passing layer(s)

---

## 11) Tight model statement

TaskSpec declares **capability needs** and required **patch/evidence outputs**. ToolProfiles grant **method access**. The scheduler derives ToolProfiles from **graph + policy** to spawn least-privilege ephemeral workers in torrent-like waves. The coordinator, holding admin tools, stacks PatchProposals on an integration canvas until constraints are met.

---

## 12) Deterministic client generation from specs + profiles (git-backed tool registry)

### Goal

A client (OpenAI SDK, Tool SDK, or A2A runtime client) MUST be deterministically generated from a spec given a profile (capabilities + policy), and be reproducible across ephemeral runtimes/workers.

This implies three inputs are versioned in git and pinned by ref:

1. **Specs** (OpenAPI / JSON Schema / A2A card/profile schemas)
2. **Generator toolchain** (exact generator version + config + normalization)
3. **Profiles** (policy + capability mapping + constraints)

Ephemeral runtimes/workers MUST NOT “discover latest”. They resolve pinned references and run hermetically.

---

## 13) Git as the tool registry backend

### Repository layout (single repo or monorepo-friendly)

```text
registry/
  tools/
    <tool_id>/
      spec/
        openapi.yaml
        schemas/
          *.json
      profiles/
        default.profile.json
        readonly.profile.json
        highrisk.profile.json
      generators/
        openapi-generator.lock
        config/
          python.yaml
          typescript.yaml
      contract-tests/
        cases/
          *.json
        runner/
          ...
      CHANGELOG.md
      OWNERS
  a2a/
    cards/
      runtime/<runtime_id>.card.json
      tool/<tool_id>.card.json
    profiles/
      <profile_id>.profile.json
  policy/
    resolver_spec.json
    policy_spec.json
```

### Resolution model (what ephemeral components consume)

Pinned references:

- Tool reference: `tool_id@<git_ref>`
- Profile reference: `profile_id@<git_ref>`
- Generator reference: `generator_bundle@<git_ref>`

Ephemeral runtime boot resolves:

- `tool_spec_ref` + `profile_ref` + `generator_bundle_ref`
- executes in a hermetic environment (locked deps, locked formatters)

### Promotion model

- `main` contains “candidate” registry state
- `tags/registry/<tool_id>/vX.Y.Z` are “promoted” tool/profile/spec releases
- Ephemeral environments use tags by default; raw SHAs for debugging

---

## 14) Deterministic codegen pipeline (OpenAPI / JSON Schema)

### Determinism requirements (non-negotiable)

To make “same spec + profile ⇒ same client” true across SDKs:

1. **Canonical spec normalization**

   - Canonicalize ordering (paths, components, schemas)
   - Resolve `$refs` consistently
   - Remove/normalize non-semantic noise if generator is sensitive

2. **Pinned generator + pinned templates**

   - Generator version locked (e.g., openapi-generator-cli, oapi-codegen, datamodel-codegen)
   - Templates/config checked into git and referenced by ref

3. **Pinned formatter/toolchain**

   - Prettier/Black/Ruff/GoFmt versions locked
   - Line ending normalization

4. **Stable naming rules**

   - Explicit `operationId`s
   - Explicit schema titles
   - Avoid generator heuristics where possible

### Profile-driven generation (key idea)

A profile is a **filter + policy overlay** that deterministically derives a “view” of the spec and generator config.

Profile controls (typical):

- Allowed endpoints (tag/operationId/path/method)
- Allowed schemas (subset or denylist)
- Auth modes (none/apiKey/oauth/mtls)
- Network metadata (allowlist hosts/ports)
- Rate/budget metadata (max calls, timeouts)
- Client surface (sync/async, streaming, retries)

### Build pipeline (deterministic)

Inputs:

- `openapi.yaml` + `profile.json`

Steps:

1. `spec_filter(profile) → filtered.openapi.json` (canonicalized)
2. `generator(profile, language) → client code`
3. format + lint (locked versions)
4. contract-tests run against:
   - golden I/O cases
   - mock server (optional)

Outputs:

- `client/<lang>/<tool_id>/<profile_id>/...`
- `manifest.json` (hashes of all inputs + generated outputs)

---

## 15) Multi-agent collaboration patterns for registry evolution (stacked patches)

### Roles

- **Workers (ephemeral):** read repo + produce PatchProposal + evidence
- **Coordinator (admin):** stacks/applies patches, tags releases, promotes profiles/specs

### PR pattern

- **Spec PR (worker):** modifies `spec/` + `profiles/` + adds/updates golden cases
- **Generated PR (coordinator or CI bot):** updates generated clients for affected languages
- **Promotion PR (coordinator):** tags + updates registry index

### Stacked PRs (recommended)

- `spec:` change OpenAPI/JSON schema + contract tests
- `gen:` update generated clients
- `runtime:` update ephemeral runtime bundles if needed
- `promote:` tag + publish index

---

## 16) Targets

### 16.1 OpenAI SDK for ephemeral runtimes

Treat the OpenAI SDK as a consumer that MUST be pinned and configured from git.

Runtime bundle includes:

- SDK version (pinned)
- transport config (timeouts/retries)
- auth method selector (from profile)
- model allowlist (from profile)
- deterministic defaults (explicit params; seed where applicable)

Git artifacts:

- `a2a/cards/runtime/<runtime_id>.card.json`
- `a2a/profiles/<profile_id>.profile.json`
- `policy/resolver_spec.json` mapping capability → OpenAI SDK operation families (e.g., `responses.create`, `files.create`, ...)

Why this matters:

- Ephemeral runtime bootstraps from `runtime_card@ref`
- It installs the pinned SDK and exposes only profile-allowed operations

### 16.2 Tool-SDK for ephemeral workers

Tool-SDK is where you enforce: **workers can only emit PatchProposals + evidence**.

Responsibilities:

- Load ToolProfiles (grants) and enforce:
  - IO roots, deny globs
  - network allowlist
  - per-method budgets
- Provide typed clients generated from specs:
  - `tool_client = ToolClient.from_spec(tool_id@ref, profile_id@ref)`

Git artifacts:

- `tools/<tool_id>/profiles/*.profile.json`
- `tools/<tool_id>/generators/*` (locked)
- `tools/<tool_id>/contract-tests/cases/*`

### 16.3 A2A cards and profiles

Treat A2A cards/profiles as first-class registry entries with deterministic parsing and stable IDs.

A2A card (advertises max capabilities):

- identity + version
- supported capabilities
- required/optional auth
- spec refs (tool spec, runtime spec)
- endpoints/transport options

A2A profile (granted for a run):

- capability grant
- constraints (IO/net/budgets)
- allowed spec view (tags/ops)
- determinism seed + inputs hash

These should be referenced by SHA/tag in run manifests.

---

## 17) Deterministic client contract (spec + profile ⇒ client)

### Inputs (MUST be hashed)

- `spec_ref` (git SHA)
- `profile_ref` (git SHA)
- `generator_bundle_ref` (git SHA)
- `language_target` + `sdk_flavor` (e.g., `python-openai`, `ts-openai`, `go-tool`)
- `normalization_rules_version`

### Output

- `client_artifact_hash`
- `manifest.json` including:
  - input refs/hashes
  - generated file hashes
  - toolchain versions (generator + formatters)

### Cross-SDK equivalence

Byte-identical output across SDKs is not required. Required equivalence is **behavioral**:

- same endpoint set
- same request/response typing
- same auth requirements
- same normalized error taxonomy mapping
- same contract test suite passing

---

## 18) Minimal schemas to add (MVP)

### ProfileSpec (used for runtime and tool generation)

- `allow.operations[]` (operationIds or tags)
- `deny.operations[]`
- `auth.mode`
- `net.allow_hosts[]`
- `io.read_roots[]`, `io.write_roots[]`, `io.deny_globs[]`
- `budgets.max_calls_by_family`, `budgets.max_wall_seconds`
- `determinism.seed`, `determinism.inputs_hash`

### ResolverSpec

Maps capability → `{operationIds[] or families[], constraints_template}`. Used by both planner and enforcer.

### GenerationManifest

- input refs/hashes + output hashes
- toolchain locks

---

## 19) Recommended implementation order

1. Add **ProfileSpec** + **ResolverSpec** as versioned schemas in repo.
2. Implement `spec_filter(profile)` producing canonical `filtered.openapi.json`.
3. Lock generator bundles per language (store locks/config/templates in git).
4. Add contract-tests as golden cases keyed by `operationId`.
5. Wire Tool-SDK + OpenAI-SDK runtimes to only instantiate clients from `spec_ref + profile_ref`.

---

## 20) Open questions / knobs (intentionally left configurable)

- Patch granularity policy (per-file, per-feature, per-hunk)
- Checkpoint strategy (per-layer vs per-batch)
- Validation tiers (fast vs full)
- Alternative exploration: single canvas only vs occasional parallel candidate canvases
- Conflict resolution: automatic split vs resolver workers vs human gates

### Defaults / clarifications (current)

1. **ToolProfiles are single-use for write:** `single_use=true` is recommended for any ToolProfile that permits write tools; replay is prevented via `jti` + TTL + run/wave binding.
2. **`base_ref` is immutable:** require commit SHA (not a branch name). Reject non-SHA refs at ingestion.
3. **Apply mode is policy-driven:** coordinator selects `atomic_proposal` (default) vs `atomic_file` vs `hunk_split` based on policy and proposal metadata.
4. **Event log is source of truth:** recommended append-only event log; ledger is a materialized view maintained by the coordinator.

---

## 21) Traceability and CI conformance (required)

Requirement traceability is executable, not narrative.

Required mapping:

- Every `CL-REQ-XXXX` MUST map to one or more of:
  - schema validation gate
  - conformance test
  - replay/determinism test
- Mappings MUST be recorded in `doc/graph/reviewpack_requirements.json` and referenced by CI outputs.

Required CI evidence:

- CI artifacts must include requirement IDs covered in the run.
- CI must fail if any required requirement ID lacks a mapped check.
- CI must fail if deprecated path references (e.g., `<deprecated_review_pack_path>`) are introduced in active docs.
