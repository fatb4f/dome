# Production Readiness Tracker

## Tracker

| ID | Workstream | Outcome | Depends On | Owner | Status | Exit Criteria |
|---|---|---|---|---|---|---|
| M-01 | SLOs & Gates | Explicit SLO/SLI and go/no-go policy | - | TBD | Not Started | `doc/slo_and_release_gates.md` approved |
| M-02 | Runtime Contracts | Stable runtime config + policy schemas | M-01 | TBD | Not Started | Schemas + examples validated in CI |
| M-03 | Security Baseline | AuthN/AuthZ, secret boundaries, path guardrails | M-02 | TBD | Not Started | Security checklist + negative tests pass |
| M-04 | Event Reliability | Durable event model with idempotency/replay semantics | M-02 | TBD | Not Started | Replay test reproduces deterministic decisions |
| M-05 | State Machine Hardening | Legal transition enforcement + invariants | M-02, M-04 | TBD | Not Started | Invalid transitions rejected with reason codes |
| M-06 | Concurrency Safety | Locking/atomic writes/race protection | M-04, M-05 | TBD | Not Started | Race/fault-injection tests green |
| M-07 | Retry/Backoff Policy | Bounded retry with jitter/circuit-breakers/DLQ | M-04 | TBD | Not Started | Retry behavior verified under injected faults |
| M-08 | Observability & Alerting | Trace/metric/log correlation and alert thresholds | M-01, M-04 | TBD | Not Started | Dashboards + alert test playbook completed |
| M-09 | Reproducibility & Provenance | Immutable run IDs, hashes, provenance manifest | M-04, M-05 | TBD | Not Started | End-to-end reproducibility runbook passes |
| M-10 | CI/CD Promotion Pipeline | Branch protections, required checks, staged deploy | M-01, M-02, M-08 | TBD | Not Started | Canary and rollback gates automated |
| M-11 | Operational Runbooks | Incident/recovery/replay procedures | M-08, M-10 | TBD | Not Started | Tabletop + live drill sign-off |
| M-12 | Compliance & Audit | Retention policy, auditability, data handling controls | M-03, M-09, M-11 | TBD | Not Started | Audit evidence package generated |

## Current In-Repo Deliverables

| Workstream | File | Purpose | Status |
|---|---|---|---|
| M-02 Runtime Contracts | `tools/orchestrator/runtime_config.py` | Runtime profile loader/validator consumed by demo runners | In Progress |
| M-02 Runtime Contracts | `ssot/schemas/runtime.config.schema.json` | Runtime config contract schema | In Progress |
| M-02 Runtime Contracts | `ssot/examples/runtime.config.json` | Runtime config example profiles (`tdd`, `refactor`) | In Progress |
| M-02 Runtime Contracts | `tests/test_runtime_config.py` | Validation tests for runtime profile loading behavior | In Progress |

## Dependency Matrix

`1` means row item depends on column item.

| Row \ Col | M-01 | M-02 | M-03 | M-04 | M-05 | M-06 | M-07 | M-08 | M-09 | M-10 | M-11 | M-12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M-01 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-02 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-03 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-04 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-05 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-06 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-07 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-08 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-09 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M-10 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| M-11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| M-12 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |

## Suggested Execution Order

1. M-01
2. M-02
3. M-04
4. M-05
5. M-06
6. M-07
7. M-08
8. M-09
9. M-03
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
