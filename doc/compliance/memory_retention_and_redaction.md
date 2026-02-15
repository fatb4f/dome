# Memory Retention And Redaction

## Scope

This policy governs long-horizon memory data persisted by telemetry materialization
(`tools/telemetry/memoryd.py`) into DuckDB artifacts under `ops/memory/`.

## Retention Policy

1. Keep normalized run/task facts for 90 days by default.
2. Keep raw payload blobs (`event_fact.payload_json`) for 30 days.
3. Keep checkpoint metadata (`ops/memory/checkpoints/*.json`) as generated runtime state only (not committed).

## Redaction Policy

1. Secrets, tokens, and credentials must be redacted before OTel export.
2. Persist only allowlisted operational metadata fields.
3. Do not persist raw tool stdout/stderr unless explicitly approved and scrubbed.

## Auditability

1. Persist `repo_commit_sha` and artifact references for each run-level fact.
2. Link memory facts back to evidence capsules where available.
3. Ensure deterministic query ordering for repeatable audit reports.

