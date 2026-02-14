# SSOT Living Doc — Telemetry-Gated Agent Identity (MVP v0.2)

## Objective
Build a spec-driven “agentic entity” whose durable identity is:
- **Memory:** claims that are *proven* (with provenance)
- **Task preferences:** deterministic choices (ranking/routing/tie-breaks)

Everything else is transient, derived, or auditable.

## Root SSOT artifacts
### `plant.spec`
Constraints + allowed actions + obligations (what *may* happen, what *must* happen).

### `state.space`
Observable truth (snapshot/ledger):
- durable memory entries
- durable task preferences
- work lifecycle state
- **telemetry provenance pointers** for any transition that writes durable state

### `control.strategies`
Deterministic transition logic:
- `next(S)` selection (routing + tie-breaks)
- gating predicate selection

## Telemetry-first confirmation model
**Telemetry (OpenTelemetry trace data) is the SSOT for confirmation**:
- Any signal that can influence gating or durable writes **must be present in telemetry** (span attributes / events).
- External artifacts are allowed (files, diffs, reports), but must be **referenced by telemetry** (path + hash).
- If a fact is not in telemetry (or referenced by telemetry), it must not influence decisions.

---

## Eval loop = constraint satisfaction over evidence bundles
The gate/eval loop treats each work node’s `{assert}` as an **algebraic constraint expression** with multiple clauses.

### Constraint expression (minimal algebra)
A node assertion is a conjunction of clauses:

- **Expression:** `ASSERT := AND(clause_1, clause_2, ..., clause_n)`
- **Clause kinds (common):**
  - `provides(X)` — required evidence/value exists (e.g., tests report)
  - `ensures(P)` — predicate must hold (e.g., exit_code == 0)
  - `preserves(Y)` — forbidden side effect did not occur (e.g., no changes in forbidden paths)
  - `limits(B)` — budget/threshold respected (e.g., runtime <= max)

Each clause is evaluated deterministically from telemetry:
- input: `(state_snapshot, evidence_bundle, node)`
- output: `PASS | FAIL(reason_code) | STOP(reason_code)`

### Evidence bundle (gate input)
Minimal, deterministic gate input:
- `otel.trace_id_hex`, `otel.span_id_hex`
- `signals{}`: telemetry-derived key/values used by the gate
- `artifacts[]`: `(path, sha256, bytes)` referenced by telemetry

### Eval result
The evaluator computes:
- `solved: bool` (true iff all clauses PASS)
- `failed_clauses[]` (with reason codes)
- `residual` (optional: remaining obligations if partial progress is allowed)

### State-space computation and assertion
`state.space` is updated **only** by applying the eval result:

- If `solved=true`:
  - transition `GATED -> DONE`
  - write durable memory/ledger entries referencing `(trace_id, span_id)`
- If any clause FAIL:
  - transition `GATED -> BLOCKED`
  - record the failed clause(s) and `reason_code` as the blocker
- If any clause STOP:
  - transition to `BLOCKED` (or terminal stop state if modeled)
  - no durable writes beyond the stop record

This ensures: **DONE ⇔ assertion solved against telemetry-backed evidence**.

---

### Telemetry evidence bundle
Minimal, deterministic gate input:
- `otel.trace_id_hex`, `otel.span_id_hex`
- `signals{}`: telemetry-derived key/values used by the gate
- `artifacts[]`: `(path, sha256, bytes)` referenced by telemetry

## Operating loop
### PLAN
Emit a bounded work DAG of nodes:
`node = { reqs, deps, provs, assert }`
- `provs` and `assert` declare required telemetry evidence.
- Planning cannot mark work DONE.

### EXECUTE
Run tools; capture rich signals.
- Emit all decision-relevant signals into telemetry.
- Reference artifacts by (path + sha256) in telemetry.

### GATE
Deterministic gate over telemetry bundle only.
- `DONE` only when obligations are satisfied and trace pointer recorded.
- Otherwise `BLOCKED` with typed `reason_code`.

## Minimal observability stack (Option A + Langfuse)
- **Instrumentation:** OpenLLMetry (Traceloop SDK)
- **Transport:** OTLP to local **OpenTelemetry Collector**
- **Backend:** Langfuse (OTLP/HTTP trace ingestion)
- Optional: **OpenInference** processors if multiple instrumentors need schema unification

## MVP v0.2 scope decisions
- Keep the system single-runner and deterministic.
- Defer higher-order planners (e.g., Graph-of-Thoughts) and self-evaluation until the telemetry-first loop proves sufficient.
- Prefer expanding **telemetry obligations** over adding reasoning complexity.

## Repo wiring (reference)
- `ops/observability/`: OTEL collector → Langfuse forwarding
- `apps/python-demo/`: runnable Plan→Execute→Gate demo (telemetry-only gating)
- `ssot/schemas/`: JSON Schemas, including telemetry evidence bundle

## Promotion criteria to “project status”
Promote once:
- A minimal end-to-end loop reliably writes state only on telemetry-confirmed gates.
- Trace provenance is stable and queryable (trace_id/span_id → gate → state write).
- Determinism holds under replay (same snapshot + same telemetry → same decisions).

