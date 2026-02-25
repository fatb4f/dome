# Retry And Backoff Policy

- Retry scope: transient failures (`transient=true` or reason code prefix `TRANSIENT.`).
- Max attempts: configured by `max_retries` (attempts = retries + first try).
- Backoff: exponential with bounded jitter.
  - base delay = `retry-base-ms`
  - capped by `retry-max-ms`
- DLQ semantics:
  - when transient failures exhaust retry budget, task is persisted to `ops/runtime/runs/<run_id>/dlq/<task>.dlq.json`.
  - reprocessing entrypoint: `tools/orchestrator/dlq_reprocess.py`
  - default action is manual review classification output, not automatic replay.

Reason code mapping:
- transient -> `TRANSIENT.*`
- deterministic execution failure -> `EXEC.NONZERO_EXIT`
- verify failure -> `VERIFY.TEST_FAILURE`
