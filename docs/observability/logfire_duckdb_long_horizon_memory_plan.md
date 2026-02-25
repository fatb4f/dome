# OTLP Backend + DuckDB Long-Horizon Memory Plan

Date: 2026-02-15

## Goal

Add durable long-horizon memory to `dome` by:

1. Emitting stable OpenTelemetry signals from orchestrator runs.
2. Exporting telemetry to an OTLP backend (for example, Logfire or Langfuse).
3. Running a daemon that materializes telemetry and evidence-capsule summaries into DuckDB.
4. Exposing query/update operations via MCP/A2A so planner/checker can retrieve priors.

This keeps memory outside prompt context windows and grounded in replayable artifacts.

## Non-Goals

- Replace existing `ops/runtime/runs/*` artifact generation.
- Store chain-of-thought or non-auditable raw reasoning.
- Make run execution depend on telemetry availability.

## System Topology

1. `dome` orchestrator emits events, task results, gate decisions, and evidence capsules.
2. OTel instrumentation exports spans/events to an OTLP backend.
3. `memoryd` daemon reads:
   - OTLP backend traces (primary),
   - local fallback artifacts under `ops/runtime/runs/*` (secondary).
   - current shipped implementation materializes from local artifacts and does not yet ingest backend cursors directly.
4. `memoryd` computes rollups/features and writes normalized tables to `ops/memory/memory.duckdb`.
5. MCP/A2A memory service exposes bounded queries and append operations for validated capsules.

## Instrumentation Points (Current Code Mapping)

Add/confirm spans and attributes at:

1. Planner stage
   - file: `tools/orchestrator/planner.py`
   - span: `dome.planner.translate`
   - attrs: `run.id`, `packet.id`, `task.count`, `base.ref`
2. Dispatcher wave scheduling
   - file: `tools/orchestrator/dispatcher.py`
   - span: `dome.dispatcher.wave`
   - attrs: `run.id`, `wave.size`, `max.workers`
3. Worker attempt execution
   - file: `tools/orchestrator/implementers.py`
   - span: `dome.worker.attempt`
   - attrs: `run.id`, `task.id`, `attempt`, `task.status`, `task.reason_code` (compat alias for `failure_reason_code`), `task.duration_ms`, `task.worker_model`
4. Gate/checker decision
   - file: `tools/orchestrator/checkers.py`
   - span: `dome.gate.evaluate`
   - attrs: `run.id`, `gate.status`, `gate.substrate_status`, `risk.score`, `confidence`
5. Promotion decision
   - file: `tools/orchestrator/promote.py`
   - span: `dome.promote.decide`
   - attrs: `run.id`, `promotion.decision`, `max.risk`
6. State write and replay
   - file: `tools/orchestrator/state_writer.py`
   - span: `dome.state.write`
   - attrs: `run.id`, `work.items`, `event.count`

Required attribute set for memory indexing:

- `run.id`
- `task.id` (for task-scoped spans)
- `task.status`
- `task.reason_code` (ingress compatibility alias for `failure_reason_code`)
- `policy_reason_code` when guard denials occur
- `task.worker_model`
- `task.duration_ms`
- `event.id` (if available)
- `evidence.capsule.path` (for persisted result events)

## Data Contracts For Memory Facts

Only persist memory facts from:

1. Schema-valid task results and evidence capsules.
2. Schema-valid gate decisions and promotion decisions.
3. OTel spans/events that include `run.id` and stage identity.

Reject or quarantine:

- records missing `run.id`,
- malformed JSON lines,
- events without deterministic stage mapping.

## DuckDB Layout

Database path:

- `ops/memory/memory.duckdb`

Core tables:

```sql
CREATE TABLE IF NOT EXISTS run_fact (
  run_id TEXT PRIMARY KEY,
  first_seen_ts TIMESTAMP,
  last_seen_ts TIMESTAMP,
  base_ref TEXT,
  gate_status TEXT,
  substrate_status TEXT,
  promotion_decision TEXT,
  risk_score INTEGER,
  confidence DOUBLE,
  repo_commit_sha TEXT,
  summary_path TEXT,
  state_space_path TEXT
);

CREATE TABLE IF NOT EXISTS task_fact (
  run_id TEXT,
  task_id TEXT,
  status TEXT,
  failure_reason_code TEXT,
  policy_reason_code TEXT,
  reason_code TEXT, -- compatibility alias
  attempts INTEGER,
  duration_ms BIGINT,
  worker_model TEXT,
  evidence_bundle_path TEXT,
  evidence_capsule_path TEXT,
  updated_ts TIMESTAMP,
  PRIMARY KEY (run_id, task_id)
);

CREATE TABLE IF NOT EXISTS event_fact (
  run_id TEXT,
  event_id TEXT,
  topic TEXT,
  sequence BIGINT,
  ts TIMESTAMP,
  payload_json TEXT,
  PRIMARY KEY (run_id, event_id)
);

CREATE TABLE IF NOT EXISTS memory_feature (
  feature_id TEXT PRIMARY KEY,
  run_id TEXT,
  task_id TEXT,
  feature_key TEXT,
  feature_value TEXT,
  feature_score DOUBLE,
  created_ts TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_reason ON task_fact(reason_code); -- compatibility
CREATE INDEX IF NOT EXISTS idx_task_failure_reason ON task_fact(failure_reason_code);
CREATE INDEX IF NOT EXISTS idx_task_status ON task_fact(status);
CREATE INDEX IF NOT EXISTS idx_run_gate ON run_fact(gate_status);
```

Feature examples:

- `retry_profile=high`
- `failure_signature=TRANSIENT.NETWORK+implement`
- `pattern_profile=tdd`
- `repo_area=orchestrator`

## Daemon Responsibilities (`memoryd`)

Loop (default every 10s):

1. Pull incremental traces/events from OTLP backend provider (cursor checkpoint, when enabled).
2. Parse and stage records.
3. Merge with local artifact facts (`run.manifest.json`, `summary.json`, `*.evidence.capsule.json`) for consistency.
4. Upsert normalized tables.
5. Compute feature rows and rolling aggregates.
6. Emit daemon health metrics and checkpoint.

State/checkpoint files:

- `ops/memory/checkpoints/otlp.cursor.json` (or provider-specific alias)
- `ops/memory/checkpoints/materialize.state.json`

Failure policy:

- never block orchestrator runs,
- on daemon failure: keep local artifact generation unchanged,
- on restart: resume from checkpoint idempotently.

## MCP/A2A Memory Interface

Expose a narrow contract for planning/checking:

1. `memory.query_priors`
   - input:
     - `scope`: `task|run|repo`
     - `filters`: `failure_reason_code` (canonical), optional compatibility alias `reason_code`, plus `task_status`
     - `limit` (default 20, max 200)
   - output:
     - ranked prior entries with evidence refs and confidence scores.
2. `memory.upsert_capsule`
   - input:
     - capsule payload or path,
     - `run_id`, `task_id`, `status`, `failure_reason_code`
     - optional `policy_reason_code` for guard denials
   - behavior:
     - validate capsule schema before write.
3. `memory.get_run_summary`
   - input: `run_id`
   - output: run-level fact row + task rollup + top failure signatures.
4. `memory.health`
   - output: daemon liveness, checkpoint lag, last ingest timestamp.

Determinism constraints:

- all query endpoints must support stable sorting,
- same query + same DB snapshot must return same ordering.

## Query Patterns For EPSL/Prior Retrieval

Use bounded templates:

1. Similar failure priors:

```sql
SELECT run_id, task_id, COALESCE(failure_reason_code, reason_code) AS failure_reason_code, attempts, duration_ms, evidence_capsule_path
FROM task_fact
WHERE COALESCE(failure_reason_code, reason_code) = ? AND status = 'FAIL'
ORDER BY updated_ts DESC
LIMIT ?;
```

2. Best-known-success priors:

```sql
SELECT run_id, task_id, worker_model, attempts, duration_ms, evidence_capsule_path
FROM task_fact
WHERE status = 'PASS'
ORDER BY attempts ASC, duration_ms ASC, updated_ts DESC
LIMIT ?;
```

3. Gate risk trend:

```sql
SELECT date_trunc('day', last_seen_ts) AS day, avg(risk_score) AS avg_risk
FROM run_fact
GROUP BY 1
ORDER BY 1 DESC
LIMIT 30;
```

## Security And Compliance Controls

1. Redact secrets before OTel export (reuse `tools/orchestrator/security.py` policies).
2. Do not persist raw tool stdout/stderr unless explicitly allowlisted.
3. Restrict DB file permissions to runtime owner.
4. Record provenance (`repo_commit_sha`, artifact hashes) for each persisted fact.
5. Enforce retention windows for raw event payloads.

## Rollout Plan

Phase 1: OTel + OTLP backend baseline

1. Add/verify spans for planner/dispatcher/implementers/checker/promote/state writer.
2. Verify required attrs are present in test runs.
3. Exit criteria:
   - `just test` passes,
   - one run has end-to-end trace correlation by `run.id`.

Phase 2: `memoryd` + DuckDB materialization

1. Implement daemon with checkpointed ingestion.
2. Create normalized tables and upsert paths.
3. Add replay/idempotency tests for duplicate event ingestion.
4. Exit criteria:
   - deterministic row counts under replay,
   - no run-time coupling with orchestrator execution.

Phase 3: MCP/A2A memory service

1. Expose `query_priors`, `upsert_capsule`, `get_run_summary`, `health`.
2. Integrate planner/checker to request bounded priors.
3. Add contract tests for sorting/stability and schema validation.
4. Exit criteria:
   - planner can consume priors without nondeterministic ordering,
   - gate behavior remains reproducible with same memory snapshot.

Phase 4: Policy hardening

1. Retention, redaction, and audit export checks.
2. Alerting on ingest lag, DB growth, and invalid capsule rates.
3. Exit criteria:
   - operational runbook for daemon incident/recovery,
   - compliance evidence bundle generated from memory tables.

## Minimal Implementation Backlog

1. `tools/telemetry/memoryd.py` (daemon skeleton + checkpoints)
2. `tools/telemetry/memory_schema.sql` (DuckDB DDL)
3. `tools/telemetry/memory_api.py` (MCP/A2A handlers)
4. `tests/test_memoryd_idempotency.py`
5. `tests/test_memory_query_contract.py`
6. `ops/memory/README.md` (ops runbook and retention policy)
