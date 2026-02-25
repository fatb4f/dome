# Recover From Partial Run

Resume criteria:
- `summary.json` exists and pending tasks are identifiable.
- event log is parseable and not truncated.

Restart criteria:
- corrupted event log with unrecoverable parse errors.
- inconsistent artifact hash chain.

Recovery choice must be documented in runbook notes with reason code.
