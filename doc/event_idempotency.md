# Event Idempotency Behavior

## Current Runtime Semantics

- Idempotency key: `event_id` on each event envelope.
- Duplicate handling: duplicate `event_id` values are ignored by `EventBus` within a single process lifetime.
- Ordering: events persisted with monotonic `sequence` for deterministic replay order.

## Restart Semantics

- Current cache scope is in-memory (`EventBus._seen_event_ids`), so duplicate suppression does not persist across process restarts.
- On restart, duplicate suppression relies on upstream producers generating stable/unique `event_id` values and downstream replay consumers deduplicating when needed.

## Persistence Roadmap

To make restart-safe idempotency strict:
1. persist seen-id window per `run_id` to disk (e.g., `ops/runtime/runs/<run_id>/idempotency.index.json`)
2. load index at startup
3. expire old ids by retention policy
