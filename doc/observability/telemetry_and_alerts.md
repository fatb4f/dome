# Telemetry And Alerts

Required telemetry fields:
- `run.id`
- `task.id`
- `task.status`
- `task.attempts`
- `task.reason_code` (canonical `failure_reason_code`)
- `task.worker_model`
- `task.duration_ms`
- when guard denials occur: `policy_reason_code` (or `guard_reason_code`) as a separate field

Correlation path:
1. `summary.json` -> `evidence_bundle_path`
2. evidence bundle -> telemetry signals/artifact hashes
3. event log envelope (`event_id`, `sequence`, `run_id`) -> replayable event stream

Planner wrapper envelope (required for high-signal flow):
- `run_id`, optional `task_id`
- `group_id`, `signal`, `wrapper_policy`
- TaskSpec key context: `scope`, `target.kind`, `target.id`, `action.kind`, `failure_reason_code`
- evidence references (paths and/or hashes)

Minimum alert thresholds:
- Promotion block when gate status is `REJECT` or `NEEDS_HUMAN`
- Retry-storm warning when aggregate retries per run exceed threshold
- Error budget breach when failed task ratio exceeds SLO target

Machine-checkable alert gate:
- `tools/orchestrator/alert_gate.py --summary <run_summary.json> --max-fail-ratio 0.05 --max-total-retries 10`
- `tools/telemetry/memory_alert_gate.py --checkpoint <materialize.state.json> --min-processed-runs 1`

Cross-repo dependencies:
- `dome`: emits/consumes telemetry fields and wrapper envelopes in planner+daemon.
- `xtrlv2`: supplies guardrails/reason-code semantics consumed by telemetry normalization.
- `watcher`: contributes normalized event envelopes used for replay and high-signal grouping.
- `opctrl`: consumes alert outputs and enforces promotion/runbook policy.
