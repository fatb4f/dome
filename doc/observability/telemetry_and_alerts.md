# Telemetry And Alerts

Required telemetry fields:
- `run.id`
- `task.id`
- `task.status`
- `task.attempts`
- `task.reason_code`
- `task.worker_model`
- `task.duration_ms`

Correlation path:
1. `summary.json` -> `evidence_bundle_path`
2. evidence bundle -> telemetry signals/artifact hashes
3. event log envelope (`event_id`, `sequence`, `run_id`) -> replayable event stream

Minimum alert thresholds:
- Promotion block when gate status is `REJECT` or `NEEDS_HUMAN`
- Retry-storm warning when aggregate retries per run exceed threshold
- Error budget breach when failed task ratio exceeds SLO target

Machine-checkable alert gate:
- `tools/orchestrator/alert_gate.py --summary <run_summary.json> --max-fail-ratio 0.05 --max-total-retries 10`
