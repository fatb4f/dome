# Concept overview (read this first)

This section sits *above* the checklists/matrices so they’re interpretable. It defines the problem, objectives, operating model, and the meaning of the core constructs.

---

## 1) Problem framing

**Weak seam:** post-ingest.

- **OTel → Logfire aggregation** is assumed “good enough”.
- The unstable/low-signal part is everything **after the aggregator**:
  - extracting patterns
  - deciding what is “high-signal”
  - writing durable, queryable memory artifacts

**Design response:** move “what matters” upstream (planner wrappers) and make all downstream steps deterministic and replayable.

---

## 2) Core objective

Build **deterministic, replayable, bounded contextual memory** that improves planner decisions.

“Contextual memory” here means:
- retrieved *before* action selection,
- keyed on the same primitives used to define tasks,
- prescriptive enough to shape tool execution,
- verifiable (gates/guards/tests), and
- grounded in evidence bundles (traceability).

This is explicitly **not** just “telemetry storage” or “analytics”.

---

## 3) Operating model (control flow)

### 3.1 Planner → high-signal wrapper emission (curation)
Planner emits wrapper context for:
- promoted evidence (high-signal),
- every gate failure (also high-signal),
and includes TaskSpec primitives (target/action/scope/failure_reason_code).

Wrappers are the *selector* that prevents the daemon from guessing.

### 3.2 Daemon → facts first, derived second (materialize → derive)
Daemon responsibilities:
1) **Materialize facts** into DuckDB (append-friendly, replayable)
2) **Derive artifacts** (patterns, rollups, capsules) from a DB snapshot
3) **Upsert capsules** so they can be retrieved via the Memory API

### 3.3 Planner → bounded retrieval loop (priors before actions)
At planning time:
1) planner forms a TaskSpec using the same standardized primitives,
2) planner calls `memory.query_priors(...)` (bounded, ordered),
3) planner ranks results by TaskSpec match + policy/compatibility,
4) planner chooses actions and verification gates accordingly.

---

## 4) Safety model: Guardrails as the control plane

### 4.1 GuardrailsBundle (contract)
Guardrails are **control-plane** decisions about whether a transition is allowed. Treat GuardrailsBundle as an **upstream policy input** (configured, not derived from ingest/wrappers).

GuardrailsBundle provides:
- explicit guard specs,
- guard evaluation records (PASS/FAIL/SKIP),
- required evidence constraints,
- and strict handling of unknowns (default: **DENY**, `max_unknowns = 0`).

### 4.2 Why guardrails matter for memory
A “prescriptive prior” is only valid if it is:
- **policy-compatible** (side-effects + guard constraints),
- and produces the **expected guard outcomes**.

Guard denials must be represented explicitly so they don’t silently pollute “failure semantics”.

---

## 5) Learning model: spec-as-test, replay, fuzz (learning plane)

Learning-plane mechanisms generate evidence and update taxonomy/strategies:

- **Spec-as-test:** encode the expected behavior/constraints as executable checks.
- **Replay:** re-run a packet using archived evidence to validate determinism and regressions.
- **Fuzz:** mutate schema-defined inputs/config to discover edge cases; failures become new high-signal evidence groups.
- **Hypothesis:** property-based testing to generalize invariants beyond golden fixtures.

These feed the inference layer and concept maintenance (support/decay/conflict).

**Spec-as-test has both learning-plane and control-plane effects:**
- As learning-plane: it generates evidence and keeps taxonomy/strategies honest.
- As control-plane: failures are emitted as high-signal wrapper events and should block promotion until resolved.


---

## 6) Key conceptual tension (state explicitly)

**unknowns = DENY** is correct for *promotion safety*, but must not prevent learning.

Resolution:
- Deny unsafe transitions in control-plane (promotion/unsafe execution),
- while still capturing:
  - evidence bundles,
  - `guard_eval`,
  - `failure_reason_code` candidates,
  - and a learning workflow that classifies novel failures and proposes strategies.

In other words: **deny execution, not observation**.

---

## 7) Vocabulary contract (define once)

To avoid polluted priors, distinguish:

- **Failure semantics (`failure_reason_code`)**
  - “what went wrong in the domain/tool/task”
  - used for retrieval keys and strategy mapping

- **Policy denials (guard/control reason)**
  - “what was disallowed by guardrails”
  - used for safety audit, not as a replacement for domain failure semantics

Both can coexist on an event, but they should remain separable fields/columns.

---


**Fielding rule (to keep priors clean):**
- Use `task.reason_code` (canonical **failure_reason_code** field) for failure semantics only.
- Store guard denials separately (e.g., `policy_reason_code` / `guard_reason_code`), and allow both to exist on the same task/event.

## 8) What “done” means conceptually

A concept prior is *prescriptive* only if all are true:

1) **Deterministic:** same canonical input/config → same canonical output
2) **Policy-compatible:** side-effects and guards match the environment/mode
3) **Verifiable:** expected gates/guards/tests pass
4) **Traceable:** grounded in evidence bundle pointers + packet provenance
5) **Bounded:** retrievable via bounded API (limit/order) and stable keys

If any of these fail, it’s advisory (or unsafe), not prescriptive.

---

## 9) Concept definitions (the three main blocks)

### 9.1 `python_standard` (tool-shaping gate)

**Fast/slow verification split:**
- Run schema + determinism + Hypothesis properties in fast CI.
- Run replay/fuzz as slower, scheduled gates (nightly/weekly) while still writing their outcomes into the same fact/capsule pipeline.

**What it is:** a composite gate that turns “a tool” into a predictable, contract-driven component.

**What it enforces (in layers):**
- Contract shaping: Pydantic models + canonical serialization
- Determinism: golden fixtures + Hypothesis determinism properties
- Side-effects: schema/manifest policy + adapter enforcement + tests
- Observability: required telemetry and evidence linkage
- Verification: spec-as-test + (optionally) replay/fuzz gates

**Why it exists:** prescriptive concept capsules only work if the referenced tools behave predictably and emit comparable evidence.

### 9.2 Dual-layer memory substrate (facts → capsules)
**What it is:** two memory tiers in DuckDB:

- **Tier 1: operational facts**
  - run/task facts, gate facts, wrappers, evidence pointers, guard evals
  - optimized for replayability, auditing, rollups, and bounded retrieval

- **Tier 2: prescriptive capsules**
  - operational capsules: “what happened + what to do next time for this exact TaskSpec key”
  - conceptual capsules: generalized “recipes” with applicability envelope + verification requirements

**Why it exists:** analytics alone don’t create contextual memory; capsules do, because they encode “actionable priors” keyed to TaskSpec.

### 9.3 Inference layer (facts → recommendations → capsule maintenance)
**What it is:** deterministic derivation over a DB snapshot to produce:
- normalized fingerprints,
- policy matches (reason_code → strategy),
- action recommendations (target/action primitives),
- confidence/support/decay,
- and conceptual capsule refresh.

**Why it exists:** to move from raw facts to stable, reusable, prescriptive concepts and keep them correct over time.

---

---

# python_standard + revised memory substrate
## Checklists and dependency matrices (including GuardrailsBundle)

This document consolidates:

1. `python_standard` checklist + dependency matrix  
2. Revised memory substrate checklist + dependency matrix  
3. GuardrailsBundle integration deltas used by both

---

## Shared component: GuardrailsBundle

- **GR-01 GuardrailsBundle (spec + eval)**  
  - Validate active bundle against `guardrails_bundle.schema.json`  
  - Evaluate guards and emit `guard_eval` facts  
  - Enforce `unknowns = DENY` and `max_unknowns = 0`  
  - Support `required_evidence` constraints (e.g., `["evidence_capsule"]`)  

---

## TaskSpec backbone dependency matrix

**Legend:** `1` means row depends on column.

| Row \ Col | TS-01 Primitives | TS-02 SideEffects | TS-03 Versions | TS-04 TransitionCtx | TS-05 SemanticsSplit |
|---|---:|---:|---:|---:|---:|
| **TS-01 Primitives** | 0 | 0 | 0 | 0 | 0 |
| **TS-02 SideEffects** | 1 | 0 | 0 | 0 | 0 |
| **TS-03 Versions** | 1 | 0 | 0 | 0 | 0 |
| **TS-04 TransitionCtx** | 1 | 0 | 0 | 0 | 0 |
| **TS-05 SemanticsSplit** | 1 | 0 | 0 | 1 | 0 |

---

# 1) python_standard

## Checklist

### A. Shape constraints (what every shaped tool must declare)
- [ ] Tool manifest exists (name, version, target/action keys, schema version).
- [ ] Side-effects policy declared in manifest/schema (mode + allowlists).
- [ ] Pydantic models: `InputModel`, `OutputModel`, `ConfigModel`.
- [ ] Canonical serialization implemented for all models (stable dumps).

### B. Contract & serialization checks
- [ ] All fixtures validate against `InputModel` / `ConfigModel`.
- [ ] Output validates against `OutputModel`.
- [ ] Canonical round-trip holds: `dump(load(dump(x))) == dump(x)` for input/config/output.

### C. Determinism checks
- [ ] Golden fixture determinism: same canonical input+config ⇒ same canonical output.
- [ ] Ordering determinism: no unstable ordering in outputs (canonical dump enforces).
- [ ] Hypothesis: determinism property holds across generated cases (bounded runtime).

### D. Side-effects enforcement checks
- [ ] Tool routes side effects through adapters (FS/Network/Process) rather than direct calls.
- [ ] Runtime tests prove forbidden operations fail fast under declared policy.
- [ ] Allowlist boundaries tested (paths/domains/commands).

### E. Observability & verification checks
- [ ] Tool emits required telemetry fields:  
  `run.id`, `task.id`, `task.status`, `task.attempts`, `task.reason_code` (canonical `failure_reason_code`), `task.worker_model`, `task.duration_ms`.
  - When a guard denial occurs, also emit `policy_reason_code`/`guard_reason_code` (separate from `task.reason_code`).
- [ ] Spec-as-test: executable assertions generated from spec and run in CI.
- [ ] Replay harness exists for packet-level reproduction (uses `summary.json → evidence_bundle_path` + event envelope).
- [ ] Fuzz harness exists (schema-driven mutations; failures produce minimal repro bundles).

### F. Guardrails shaping (new)
- [ ] Load active guardrails bundle and validate against schema.
- [ ] Enforce unknowns=DENY (`max_unknowns: 0`) for tool lifecycle/state transitions.
- [ ] Enforce `required_evidence` on guarded transitions (e.g., `evidence_capsule`).
- [ ] Emit `guard_eval` with decision + reason codes + evidence refs.
- [ ] Map guard denials to a separate `policy_reason_code`/`guard_reason_code` field and ensure telemetry emits it (do **not** overload `task.reason_code`).

---

## python_standard dependency matrix

**Legend:** `1` means row depends on column.

| Row \ Col | PS-01 Contract | PS-02 CanonSer | PS-03 Determinism | PS-04 SideEffectsEnforce | PS-05 Observability | PS-06 SpecAsTest | PS-07 Replay/Fuzz/Hypothesis |
|---|---:|---:|---:|---:|---:|---:|---:|
| **PS-01 Contract** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **PS-02 CanonSer** | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **PS-03 Determinism** | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| **PS-04 SideEffectsEnforce** | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| **PS-05 Observability** | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **PS-06 SpecAsTest** | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| **PS-07 Replay/Fuzz/Hypothesis** | 1 | 1 | 1 | 1 | 1 | 1 | 0 |


---

# 2) Revised memory substrate

## Checklist

### A. Ingest & correlation (Logfire → DuckDB)
- [ ] Required telemetry fields are present on all tasks.
- [ ] Correlation path is persisted: `summary.json → evidence_bundle_path → hashes` plus `(event_id, sequence, run_id)` for replay.
- [ ] Daemon has a checkpointed ingest loop (restart-safe).

### B. Planner wrapper context (high-signal selection)

### B.1 Wrapper fallback policy (required)
- [ ] Define fallback behavior when wrappers are missing/partial:
  - **Strict:** no wrapper ⇒ no patterning/capsule minting (facts-only)
  - **Hybrid (recommended):** no wrapper ⇒ derive only from failures/denials/anomalies
  - **Lenient:** no wrapper ⇒ run heuristics over all ingested facts
- [ ] Persist the chosen policy per run/packet (`wrapper_policy`) so behavior is auditable and replayable.

- [ ] Planner emits wrappers for promoted evidence groups.
- [ ] Planner emits wrappers for every failed gate.
- [ ] Wrappers carry TaskSpec keys (scope + target/action primitives + failure_reason_code).
- [ ] Wrapper membership points to evidence bundles (paths/hashes).

### C. Fact tables (facts first)
- [ ] `run_fact` and `task_fact` exist (spine for run summaries and priors).
- [ ] `gate_fact` exists (gate outcome + reason).
- [ ] `evidence_group_fact` + `evidence_group_member` exist (wrapper materialization).
- [ ] TaskSpec key columns are stored with `task_fact` (for consistent indexing).

### D. Derived tables (indexed queries)
- [ ] `run_gate_status` rollup exists (promotion blockers, fail ratios, retries).
- [ ] `gate_fail_rollup` exists (by gate, failure_reason_code, worker_model, time bucket).

### E. Capsules (operational + conceptual)
- [ ] Operational capsules minted per wrapper group via `memory.upsert_capsule` and validated against SSOT schema.
- [ ] Concept capsules minted post-success packet (generalized recipe with applicability + verification).
- [ ] Capsule ordering/retrieval is deterministic and bounded.

### F. Retrieval loop (planner uses memory)
- [ ] Planner calls `memory.query_priors(scope, filters, limit<=200)` before task execution.
- [ ] Planner matches/ranks priors by TaskSpec primitives (target/action/**failure_reason_code**/etc.).
- [ ] Single-shot promo only when priors are high-confidence and version/policy compatible.

### G. Inference layer (normalization → recommendations)
- [ ] Failure fingerprints derived from facts (gate sets, failure_reason_code, tool/config signatures).
- [ ] Policy-driven classification (strategy selection) and confidence tracking, keyed primarily on **failure_reason_code** (not policy denials).
- [ ] Spec-as-test drift detection feeds the same pipeline (new failures mint new capsules).

### H. Replay/fuzz + ops gates
- [ ] Replay uses packet IDs + evidence roots to re-run deterministically.
- [ ] Fuzz mutates schema-defined inputs/configs; failures auto-generate evidence groups.
- [ ] Alert gates wired: promotion block on `REJECT`/`NEEDS_HUMAN`, retry-storm and error budget thresholds.

### I. Guardrails facts + retrieval (new)
- [ ] Ingest and persist `guard_spec` + `guard_eval` as first-class facts (parallel to `gate_fact`).
- [ ] Any `DENY/STOP` emits a high-signal wrapper group (failed-gate equivalent).
- [ ] Guard denials map to standardized `policy_reason_code` (kept distinct from `failure_reason_code`).
- [ ] Concept capsules include `verify.expected_guards` (e.g., `repo.clean: PASS`) where applicable.
- [ ] `unknowns=DENY` violations create an explicit `unknowns` evidence entry and block promotion.

---

## Revised memory substrate dependency matrix

> Note: **MS-05 Derivations** currently groups rollups and inference for simplicity. If you later need separate SLOs/runtime (e.g., rollups continuous vs inference batch), split it into two columns without changing the upstream dependencies.


**Legend:** `1` means row depends on column.

| Row \ Col | MS-01 GuardrailsBundle | MS-02 Ingest (OTel+Logfire) | MS-03 Planner Wrappers | MS-04 Fact Tables | MS-05 Derivations (rollups+inference) | MS-06 Capsule Minting | MS-07 Replay/Fuzz | MS-08 Ops Gates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **MS-01 GuardrailsBundle** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **MS-02 Ingest (OTel+Logfire)** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **MS-03 Planner Wrappers** | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **MS-04 Fact Tables** | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| **MS-05 Derivations (rollups+inference)** | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| **MS-06 Capsule Minting** | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 0 |
| **MS-07 Replay/Fuzz** | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| **MS-08 Ops Gates** | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 0 |
