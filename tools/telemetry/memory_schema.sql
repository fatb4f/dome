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
  reason_code TEXT,
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

CREATE INDEX IF NOT EXISTS idx_task_reason ON task_fact(reason_code);
CREATE INDEX IF NOT EXISTS idx_task_status ON task_fact(status);
CREATE INDEX IF NOT EXISTS idx_run_gate ON run_fact(gate_status);

