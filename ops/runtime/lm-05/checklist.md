# LM-05 Checklist

- [x] Added packet artifacts for `pkt-dome-lm-05-reason-semantics-facts-spine`.
- [x] Added `failure_reason_code` + `policy_reason_code` columns and migration SQL in `tools/telemetry/memory_schema.sql`.
- [x] Updated `memory_api.query_priors` to use `failure_reason_code` with `reason_code` compatibility alias.
- [x] Updated `memory_api.upsert_capsule` to support separate `policy_reason_code`.
- [x] Extended `memoryd` to materialize `task_fact` and `event_fact` from run artifacts/event envelopes.
- [x] Added/updated tests for semantics split and materialization/idempotency.
- [x] Ran focused validation tests successfully.
