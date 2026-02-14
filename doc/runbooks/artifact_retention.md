# Artifact Retention

Retain per run:
- work queue, summary, gate decision, promotion decision, state space, manifest, evidence bundles.

Default retention:
- operational artifacts: 30 days
- compliance/audit bundle snapshots: 90 days

Deletion process:
- generate audit of to-be-deleted run IDs
- delete artifacts
- log deletion manifest with timestamp and actor
