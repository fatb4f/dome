# Production Readiness Tracker

## Production Definition (dome)

For this tracker, `production-ready` means:
- `availability`: core orchestration flows sustain 99.9% monthly successful run completion for supported workloads.
- `reliability`: retries, replay, and state transitions are deterministic and auditable under failure injection.
- `security`: secrets are never logged, untrusted inputs are validated, and filesystem/process boundaries are enforced.
- `operability`: incidents can be detected, triaged, and recovered using runbooks with drill evidence.
- `compliance`: evidence artifacts are retained, queryable, and reproducible for audit windows.

## Tracker

| ID | Issue | Priority | Workstream | Outcome | Depends On | Owner | Target | Status | xtrlv2 Hook | Exit Criteria | Verify Command | Evidence Path |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M-01 | #2 | P0 | SLOs & Gates | Explicit SLO/SLI and go/no-go policy | - | @fatb4f | 2026-W08 | In Progress | XA-01 decision semantics | `doc/slo_and_release_gates.md` approved | `just validate-ssot && just test` | `ops/runtime/m01/` |
| M-02 | #3 | P0 | Runtime Contracts | Stable runtime config + policy schemas | M-01 | @fatb4f | 2026-W08 | In Progress | XA-02 runtime contract bridge | Schemas + examples validated in CI | `just validate-ssot && just test` | `ops/runtime/m02/` |
| M-03 | #4 | P0 | Security Baseline | AuthN/AuthZ, secret boundaries, path guardrails | M-02 | @fatb4f | 2026-W08 | In Progress | XA-05 transport boundary controls | Security checklist + negative tests pass | `pytest -q tests/test_security.py tests/test_dependency_allowlist.py && just test` | `ops/runtime/m03/` |
| M-04 | #5 | P0 | Event Reliability | Durable event model with idempotency/replay semantics | M-02, M-03 | TBD | 2026-W09 | Not Started | XA-03 event envelope | Replay test reproduces deterministic decisions | `just test` | `ops/runtime/m04/` |
| M-05 | #6 | P1 | State Machine Hardening | Legal transition enforcement + invariants | M-02, M-04 | TBD | 2026-W09 | Not Started | XA-06 controller transition guards | Invalid transitions rejected with reason codes | `just test` | `ops/runtime/m05/` |
| M-06 | #7 | P1 | Concurrency Safety | Locking/atomic writes/race protection | M-04, M-05 | TBD | 2026-W09 | Not Started | XA-06 loop/worker serialization | Race/fault-injection tests green | `just test` | `ops/runtime/m06/` |
| M-07 | #8 | P1 | Retry/Backoff Policy | Bounded retry with jitter/circuit-breakers/DLQ | M-04, M-06 | TBD | 2026-W09 | Not Started | XA-04 policy runtime hooks | Retry behavior verified under injected faults | `just test` | `ops/runtime/m07/` |
| M-08 | #9 | P1 | Observability & Alerting | Trace/metric/log correlation and alert thresholds | M-01, M-04 | TBD | 2026-W10 | Not Started | XA-07 telemetry normalization | Dashboards + alert test playbook completed | `just test` | `ops/runtime/m08/` |
| M-09 | #10 | P1 | Reproducibility & Provenance | Immutable run IDs, hashes, provenance manifest | M-04, M-05 | TBD | 2026-W10 | Not Started | XA-02 + XA-09 provenance bridge | End-to-end reproducibility runbook passes | `just test` | `ops/runtime/m09/` |
| M-10 | #11 | P2 | CI/CD Promotion Pipeline | Branch protections, required checks, staged deploy | M-01, M-02, M-08 | TBD | 2026-W10 | Not Started | XA-08 packet promotion gates | Canary and rollback gates automated | `just test` | `ops/runtime/m10/` |
| M-11 | #12 | P2 | Operational Runbooks | Incident/recovery/replay procedures | M-08, M-09, M-10 | TBD | 2026-W11 | Not Started | XA-09 deterministic replay | Tabletop + live drill sign-off | `just test` | `ops/runtime/m11/` |
| M-12 | #13 | P2 | Compliance & Audit | Retention policy, auditability, data handling controls | M-03, M-09, M-11 | TBD | 2026-W11 | Not Started | XA-10 audit export interfaces | Audit evidence package generated | `just test` | `ops/runtime/m12/` |

## Tracker to Issues Mapping

| Tracker ID | GitHub Issue |
|---|---|
| M-01 | #2 |
| M-02 | #3 |
| M-03 | #4 |
| M-04 | #5 |
| M-05 | #6 |
| M-06 | #7 |
| M-07 | #8 |
| M-08 | #9 |
| M-09 | #10 |
| M-10 | #11 |
| M-11 | #12 |
| M-12 | #13 |

## Current In-Repo Deliverables

| Workstream | File | Purpose | Status |
|---|---|---|---|
| M-01 SLOs & Gates | `doc/slo_and_release_gates.md` | SLO/SLI and release gate policy with verification and evidence paths | In Progress |
| M-02 Runtime Contracts | `tools/orchestrator/runtime_config.py` | Runtime profile loader/validator consumed by demo runners | In Progress |
| M-02 Runtime Contracts | `ssot/schemas/runtime.config.schema.json` | Runtime config contract schema | In Progress |
| M-02 Runtime Contracts | `ssot/examples/runtime.config.json` | Runtime config example profiles (`tdd`, `refactor`) | In Progress |
| M-02 Runtime Contracts | `tests/test_runtime_config.py` | Validation tests for runtime profile loading behavior | In Progress |
| M-02 Runtime Contracts | `ssot/schemas/task.result.schema.json` | Task result contract for implementer/checker artifacts | In Progress |
| M-02 Runtime Contracts | `tests/test_ssot_policy_validate.py` | Policy JSON validation against authoritative schema | In Progress |
| M-02 Runtime Contracts | `tests/test_ssot_roundtrip.py` | SSOT JSON round-trip load/serialize verification | In Progress |
| M-03 Security Baseline | `doc/security/threat_model.md` | Threat model, trust boundaries, and control coverage | In Progress |
| M-03 Security Baseline | `doc/security/secrets_and_redaction.md` | Secret handling and runtime path guardrails policy | In Progress |
| M-03 Security Baseline | `tools/orchestrator/security.py` | Runtime path validation and payload redaction helpers | In Progress |
| M-03 Security Baseline | `ssot/schemas/orchestrator.secure_defaults.schema.json` | Secure defaults contract schema | In Progress |
| M-03 Security Baseline | `tests/test_security.py` | Path traversal rejection and redaction verification tests | In Progress |
| M-03 Security Baseline | `tests/test_dependency_allowlist.py` | Dependency allowlist audit test | In Progress |

## Dependency Matrix

`1` means row item depends on column item.

| Row \\ Col | M-01 | M-02 | M-03 | M-04 | M-05 | M-06 | M-07 | M-08 | M-09 | M-10 | M-11 | M-12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M-01 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-02 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-03 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-04 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-05 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-06 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-07 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-08 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-09 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-10 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| M-11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 |
| M-12 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |

## Suggested Execution Order

1. M-01
2. M-02
3. M-03
4. M-04
5. M-05
6. M-06
7. M-07
8. M-08
9. M-09
10. M-10
11. M-11
12. M-12

## Weekly Update Template

- Week of:
- Completed IDs:
- Blocked IDs:
- Risks introduced:
- Changes to dependency graph:
- Go/No-Go recommendation:
