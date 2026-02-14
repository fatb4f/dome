# Production Readiness Tracker

## Tracker

| ID | Workstream | Outcome | Depends On | Owner | Status | Exit Criteria |
|---|---|---|---|---|---|---|
| PR-01 | SLOs & Gates | Explicit SLO/SLI and go/no-go policy | - | TBD | Not Started | `doc/slo_and_release_gates.md` approved |
| PR-02 | Runtime Contracts | Stable runtime config + policy schemas | PR-01 | TBD | Not Started | Schemas + examples validated in CI |
| PR-03 | Security Baseline | AuthN/AuthZ, secret boundaries, path guardrails | PR-02 | TBD | Not Started | Security checklist + negative tests pass |
| PR-04 | Event Reliability | Durable event model with idempotency/replay semantics | PR-02 | TBD | Not Started | Replay test reproduces deterministic decisions |
| PR-05 | State Machine Hardening | Legal transition enforcement + invariants | PR-02, PR-04 | TBD | Not Started | Invalid transitions rejected with reason codes |
| PR-06 | Concurrency Safety | Locking/atomic writes/race protection | PR-04, PR-05 | TBD | Not Started | Race/fault-injection tests green |
| PR-07 | Retry/Backoff Policy | Bounded retry with jitter/circuit-breakers/DLQ | PR-04 | TBD | Not Started | Retry behavior verified under injected faults |
| PR-08 | Observability & Alerting | Trace/metric/log correlation and alert thresholds | PR-01, PR-04 | TBD | Not Started | Dashboards + alert test playbook completed |
| PR-09 | Reproducibility & Provenance | Immutable run IDs, hashes, provenance manifest | PR-04, PR-05 | TBD | Not Started | End-to-end reproducibility runbook passes |
| PR-10 | CI/CD Promotion Pipeline | Branch protections, required checks, staged deploy | PR-01, PR-02, PR-08 | TBD | Not Started | Canary and rollback gates automated |
| PR-11 | Operational Runbooks | Incident/recovery/replay procedures | PR-08, PR-10 | TBD | Not Started | Tabletop + live drill sign-off |
| PR-12 | Compliance & Audit | Retention policy, auditability, data handling controls | PR-03, PR-09, PR-11 | TBD | Not Started | Audit evidence package generated |

## Current In-Repo Deliverables

| Workstream | File | Purpose | Status |
|---|---|---|---|
| PR-02 Runtime Contracts | `tools/orchestrator/runtime_config.py` | Runtime profile loader/validator consumed by demo runners | In Progress |
| PR-02 Runtime Contracts | `ssot/schemas/runtime.config.schema.json` | Runtime config contract schema | In Progress |
| PR-02 Runtime Contracts | `ssot/examples/runtime.config.json` | Runtime config example profiles (`tdd`, `refactor`) | In Progress |
| PR-02 Runtime Contracts | `tests/test_runtime_config.py` | Validation tests for runtime profile loading behavior | In Progress |

## Dependency Matrix

`1` means row item depends on column item.

| Row \ Col | PR-01 | PR-02 | PR-03 | PR-04 | PR-05 | PR-06 | PR-07 | PR-08 | PR-09 | PR-10 | PR-11 | PR-12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PR-01 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-02 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-03 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-04 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-05 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-06 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-07 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-08 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-09 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PR-10 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| PR-11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| PR-12 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |

## Suggested Execution Order

1. PR-01
2. PR-02
3. PR-04
4. PR-05
5. PR-06
6. PR-07
7. PR-08
8. PR-09
9. PR-03
10. PR-10
11. PR-11
12. PR-12

## Weekly Update Template

- Week of:
- Completed IDs:
- Blocked IDs:
- Risks introduced:
- Changes to dependency graph:
- Go/No-Go recommendation:
