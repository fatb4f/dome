# Plan: MVP v0.2 — Memory + Task Preferences

## Architecture overview
- `plant.spec` (JSON/YAML): declares actions, constraints, obligations, budgets.
- `control.strategies` (JSON/YAML): declares deterministic ranking/tie-breaks and tool preference weights.
- `state.space` (JSON): stores durable memory + task preferences + work lifecycle.

## Deterministic selection (`next(S)`)
Inputs:
- work status (`QUEUED` only)
- deps satisfied
- priority score (from preferences)
Tie-break:
- `priority_score` desc
- `created_at` asc
- `work_id` asc

## Evidence bundle (EXECUTE)
For each executed action, capture rich signals and emit them into telemetry.

Telemetry bundle shape:
- `otel.trace_id_hex`, `otel.span_id_hex`
- `signals{}` (decision-relevant key/values)
- `artifacts[]` referenced by (path + sha256)

## Gate predicates (GATE)
- Implement predicates as pure functions over `(state_snapshot, telemetry_bundle, node)`.
- Gate output: `{ALLOW|DENY|STOP, reason_code?, notes?}`.

## Minimal storage choice
- Use JSON for v0.2 snapshots.
- Add an append-only `event.log` only if replay debugging is needed beyond snapshot diffs.

## Observability plumbing (Option A + Langfuse)
- Instrument apps with OpenLLMetry (Traceloop SDK).
- Export OTLP to a local OpenTelemetry Collector.
- Collector forwards traces to Langfuse OTLP/HTTP trace endpoint.
