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
  reason_code TEXT, -- compatibility alias; canonical field is failure_reason_code
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

CREATE TABLE IF NOT EXISTS binder_fact (
  derived_upsert_key TEXT PRIMARY KEY,
  idempotency_key TEXT UNIQUE,
  run_id TEXT,
  task_id TEXT,
  group_id TEXT,
  scope TEXT,
  target_kind TEXT,
  target_id TEXT,
  action_kind TEXT,
  failure_reason_code TEXT,
  policy_reason_code TEXT,
  fingerprint_hash TEXT,
  binder_version TEXT,
  support_count INTEGER,
  contradiction_count INTEGER,
  last_seen_ts TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_reason ON task_fact(reason_code); -- compatibility alias index
CREATE INDEX IF NOT EXISTS idx_task_failure_reason ON task_fact(failure_reason_code);
CREATE INDEX IF NOT EXISTS idx_task_status ON task_fact(status);
CREATE INDEX IF NOT EXISTS idx_run_gate ON run_fact(gate_status);
CREATE INDEX IF NOT EXISTS idx_binder_run_task ON binder_fact(run_id, task_id);
CREATE INDEX IF NOT EXISTS idx_binder_fingerprint ON binder_fact(fingerprint_hash);

ALTER TABLE task_fact ADD COLUMN IF NOT EXISTS failure_reason_code TEXT;
ALTER TABLE task_fact ADD COLUMN IF NOT EXISTS policy_reason_code TEXT;

CREATE VIEW IF NOT EXISTS mv_recent_failures_by_taskspec AS
SELECT
  run_id,
  task_id,
  status,
  COALESCE(failure_reason_code, reason_code) AS failure_reason_code,
  policy_reason_code,
  attempts,
  duration_ms,
  worker_model,
  evidence_capsule_path,
  updated_ts
FROM task_fact
WHERE status = 'FAIL'
ORDER BY updated_ts DESC, run_id ASC, task_id ASC;

CREATE VIEW IF NOT EXISTS mv_gate_rollup_by_failure_reason_code AS
SELECT
  COALESCE(failure_reason_code, reason_code) AS failure_reason_code,
  worker_model,
  status,
  COUNT(*) AS task_count
FROM task_fact
GROUP BY 1, 2, 3;

CREATE VIEW IF NOT EXISTS mv_guard_denials_by_policy_reason_code AS
SELECT
  run_id,
  task_id,
  policy_reason_code,
  status,
  updated_ts
FROM task_fact
WHERE COALESCE(policy_reason_code, '') != '';
