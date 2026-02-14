# Concurrency Model

- Worker execution uses bounded thread pools per wave.
- Event publishing is synchronized via an in-process lock in `EventBus`.
- Event append uses JSONL envelopes with monotonic `sequence` and unique `event_id`.

Atomic persistence policy:
- Runtime artifacts under `ops/runtime/**` are written via temp-file + `fsync` + atomic rename.
- Utility implementation: `tools/orchestrator/io_utils.py`.

Thread-safety guarantees:
- duplicate `event_id` publishes are ignored (idempotent)
- event sequence order is stable for replay.
