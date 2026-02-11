# Constitution (SSOT) — MVP v0.2

## Purpose
Build a spec-driven agentic entity whose **durable identity** is:
- **Memory:** what was observed and proven (with provenance)
- **Task preferences:** how it ranks/chooses work and tools under constraints

Everything else is derived, transient, or auditable.

## Root SSOT artifacts
This system is defined by three artifacts:

- **plant.spec**: constraints + allowed actions + obligations (**Φ + A**)
- **control.strategies**: deterministic selection/routing/evaluation (defines `next(S)`)
- **state.space**: observable truth (snapshot/ledger) + gates + provenance (**Ω(S)**)

`work_queue` is a derived frontier view: the smallest slice needed to pick the next admissible action.

## Operating loop (non-negotiable)

### PLAN
- Output must be a **work DAG** of nodes: `{reqs, deps, provs, assert}`.
- Every node declares **required evidence** (signals/artifacts) for completion.
- Planning may not mark anything DONE.

### EXECUTE
Use tools. Capture rich signals.

Telemetry is the **SSOT for confirmation**: all signals that may influence gating or memory/ledger writes MUST be emitted into the execution trace (OpenTelemetry spans/events/attributes). External artifacts are allowed, but must be referenced by telemetry (path + hash).

Required signals (whenever applicable):
- exit code
- stdout and stderr (separated)
- structured logs (prefer JSON when possible)
- artifact paths + sha256
- diffs / diffstats
- **otel_trace_id** and **otel_span_id** (provenance pointer)

Preferred techniques:
- **flags:** `--json`, `--verbose`, `--debug`, `--trace` (or tool equivalents)
- **env vars:** `LOG_LEVEL`, `TRACE`, `CI` (or tool equivalents)
- **redirection:** write machine logs to files; keep stdout/stderr separate

### GATE
- State updates MUST be derived **only** from gathered telemetry (trace data). If a fact is not in telemetry (or referenced by telemetry), it must not influence decisions.
- DONE is permitted only when:
  - outputs validate (schemas if applicable)
  - telemetry evidence obligations are satisfied
  - otel trace reference is recorded (trace_id/span_id)
- Otherwise: BLOCKED with a typed reason code.

## Determinism
`control.strategies.next(S)` must be deterministic:
- explicit tie-break rules
- stable ordering inputs
- same snapshot + same telemetry → same decision

## Safety and scope control
- Prefer smallest change that satisfies the spec.
- Budgets must exist for loops/retries; no unbounded iteration.
- Templates under `.specify/templates/` are modified only by explicit template upgrade steps.
