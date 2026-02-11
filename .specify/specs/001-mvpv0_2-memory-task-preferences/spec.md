# Spec: MVP v0.2 — Memory + Task Preferences

## Summary
Build the minimal core of a spec-driven agentic system where the only durable identity is:
- memory (proven observations with provenance)
- task preferences (deterministic ranking/routing choices)

The operating loop is **PLAN → EXECUTE → GATE**.

## Goals
- Provide SSOT artifacts: `plant.spec`, `control.strategies`, `state.space`.
- Provide a work item lifecycle and deterministic `next(S)`.
- Provide telemetry-derived evidence bundles (rich signals captured into OTEL spans/events/attributes).
- Provide gating logic that updates state only from gathered telemetry.

## Non-goals (v0.2)
- Long-term learning/RL
- Multi-agent distribution beyond a single-runner stub
- Non-deterministic exploration as default behavior

## Functional requirements
- FR1: Represent work as DAG nodes `{reqs,deps,provs,assert}`.
- FR2: Execute tasks using tools and capture exit code, stdout, stderr, logs, artifacts and hashes; **emit all decision-relevant signals into telemetry**.
- FR3: Gate transitions deterministically; DONE only when **telemetry evidence** obligations are satisfied.
- FR4: Persist durable memory and task preferences to `state.space` only with a telemetry provenance pointer (trace_id/span_id).

## Evidence / acceptance
- A demo run over a single node produces a telemetry bundle (trace_id/span_id + signals) and references any artifacts by (path + sha256).
- A replay run with same inputs produces identical gate outputs.
- A minimal `state.space` snapshot shows updated memory/preferences and work lifecycle states.

## Open questions
- Predicate meta-language: JSON schema + references vs DSL vs code-only?
- Preferred storage format for state snapshots: JSON vs SQLite?
- Canonical span schema: OpenTelemetry GenAI semantic conventions vs a project-specific minimal convention.
