# Threat Model

## Scope

This model covers the dome orchestrator runtime, including planner/implementer/checker/promotion flows and runtime artifacts under `ops/runtime/`.

## Assets

- Gate and promotion decisions
- Run manifests and evidence bundles
- Runtime contract inputs under `ssot/`
- Event log (`ops/runtime/mcp_events.jsonl`)

## Trust Boundaries

- Trusted:
  - checked-in code and schema contracts
  - deterministic artifact writers under `tools/orchestrator/`
- Untrusted:
  - external prompts/config content
  - task notes or tool output strings that may contain secrets
  - user-provided runtime CLI paths

## Primary Threats

- Path traversal and arbitrary write:
  - attacker passes `../` or absolute path to write outside runtime root.
- Secret leakage:
  - credentials included in task notes or tool output get persisted in evidence artifacts.
- Contract drift:
  - malformed runtime JSON bypasses schema checks and causes unsafe behavior.

## Controls

- Runtime path guardrails:
  - CLI entrypoints reject absolute paths and `..` traversal.
  - runtime outputs are constrained under `ops/runtime/`.
- Secret redaction:
  - sensitive key names (`token`, `secret`, `password`, `api_key`, etc.) are redacted before evidence write.
  - assignment-like secret strings are scrubbed (`token=...`, `api_key: ...`).
- Contract validation:
  - SSOT schemas validated by `just validate-ssot`.

## Residual Risk

- Runtime artifacts may still include non-secret sensitive operational metadata.
- Broader supply-chain controls (signed deps/build provenance) are not yet implemented.
