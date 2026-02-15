# Tasks: MVP v0.2 — Memory + Task Preferences

## Phase 0 — Repo + artifacts
- [x] T001 Create schemas for plant.spec, control.strategies, state.space
  - Evidence: schema validation passes on example docs

## Phase 1 — Work model
- [x] T010 Define work node schema `{reqs,deps,provs,assert}` and lifecycle states
  - Evidence: example node validates and can be scheduled

## Phase 2 — Execute (tool signals)
- [x] T020 Implement evidence capture harness (exit code, stdout/stderr, logs, artifacts, hashes)
  - Evidence: sample command run writes evidence artifacts to disk (optional)

- [x] T021 Instrument EXECUTE with OpenTelemetry (Option A: OpenLLMetry) and emit all decision-relevant signals into spans/events/attributes
  - Evidence: demo run prints/records `trace_id` and `span_id`

- [x] T022 Add OTEL collector forwarding to Langfuse (self-host or cloud) with env-based credentials
  - Evidence: collector starts; traces arrive in Langfuse UI

## Phase 3 — Gate (deterministic)
- [x] T030 Implement deterministic gating predicates and reason codes
  - Evidence: replay test produces identical gate output

- [x] T031 Gate uses telemetry bundle as the sole decision driver (no hidden signals)
  - Evidence: gate input is `{trace_id, span_id, signals}`; changing non-telemetry evidence does not affect outcome

## Phase 4 — Minimal loop
- [x] T040 Implement loop: PLAN (select node) → EXECUTE → GATE → update state.space
  - Evidence: state snapshot updated; DONE set only with telemetry-derived evidence

- [x] T041 Persist telemetry provenance pointers for DONE/BLOCKED transitions
  - Evidence: state snapshot includes `telemetry.otel.trace_id_hex` and `telemetry.otel.span_id_hex`

## Phase 5 — Documentation
- [x] T050 Document how to run the MVP and how to add new features via create-new-feature.sh
  - Evidence: README section + example feature folder created
