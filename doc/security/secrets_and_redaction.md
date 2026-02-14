# Secrets And Redaction

## Policy

- Secrets must not be persisted in `ops/runtime/**` artifacts.
- Inputs and notes are treated as untrusted and may contain credentials.
- Redaction occurs before evidence bundle serialization.

## Secret Indicators

Sensitive keys are redacted when key names include:
- `secret`
- `token`
- `password`
- `api_key` / `apikey`
- `credential`

Sensitive assignment strings are also redacted, including:
- `api_key=...`
- `token: ...`
- `password=...`
- `secret=...`

## Runtime Guardrails

- CLI write paths must be repo-relative and under `ops/runtime/`.
- Absolute paths and parent traversal segments (`..`) are rejected.

## Verification

- `pytest -q tests/test_security.py`
- `just validate-ssot`
- `just test`
