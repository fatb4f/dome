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
| M-01 | #2 | P0 | SLOs & Gates | Explicit SLO/SLI and go/no-go policy | - | @fatb4f | 2026-W08 | Done | XA-01 decision semantics | `doc/slo_and_release_gates.md` approved | `just validate-ssot && just test` | `ops/runtime/m01/` |
| M-02 | #3 | P0 | Runtime Contracts | Stable runtime config + policy schemas | M-01 | @fatb4f | 2026-W08 | Done | XA-02 runtime contract bridge | Schemas + examples validated in CI | `just validate-ssot && just test` | `ops/runtime/m02/` |
| M-03 | #4 | P0 | Security Baseline | AuthN/AuthZ, secret boundaries, path guardrails | M-02 | @fatb4f | 2026-W08 | Done | XA-05 transport boundary controls | Security checklist + negative tests pass | `pytest -q tests/test_security.py tests/test_dependency_allowlist.py && just test` | `ops/runtime/m03/` |
| M-04 | #5 | P0 | Event Reliability | Durable event model with idempotency/replay semantics | M-02, M-03 | @fatb4f | 2026-W09 | Done | XA-03 event envelope | Replay test reproduces deterministic decisions | `pytest -q tests/test_mcp_events.py tests/test_run_live_fix_demo.py && just test` | `ops/runtime/m04/` |
| M-05 | #6 | P1 | State Machine Hardening | Legal transition enforcement + invariants | M-02, M-04 | @fatb4f | 2026-W09 | Done | XA-06 controller transition guards | Invalid transitions rejected with reason codes | `pytest -q tests/test_state_machine.py tests/test_state_replay.py && just test` | `ops/runtime/m05/` |
| M-06 | #7 | P1 | Concurrency Safety | Locking/atomic writes/race protection | M-04, M-05 | @fatb4f | 2026-W09 | Done | XA-06 loop/worker serialization | Race/fault-injection tests green | `pytest -q tests/test_concurrency_safety.py && just test` | `ops/runtime/m06/` |
| M-07 | #8 | P1 | Retry/Backoff Policy | Bounded retry with jitter/circuit-breakers/DLQ | M-04, M-06 | @fatb4f | 2026-W09 | Done | XA-04 policy runtime hooks | Retry behavior verified under injected faults | `pytest -q tests/test_implementers.py && just test` | `ops/runtime/m07/` |
| M-08 | #9 | P1 | Observability & Alerting | Trace/metric/log correlation and alert thresholds | M-01, M-04 | @fatb4f | 2026-W10 | Done | XA-07 telemetry normalization | Dashboards + alert test playbook completed | `pytest -q tests/test_observability.py && just test` | `ops/runtime/m08/` |
| M-09 | #10 | P1 | Reproducibility & Provenance | Immutable run IDs, hashes, provenance manifest | M-04, M-05 | @fatb4f | 2026-W10 | Done | XA-02 + XA-09 provenance bridge | End-to-end reproducibility runbook passes | `pytest -q tests/test_provenance.py && just test` | `ops/runtime/m09/` |
| M-10 | #11 | P2 | CI/CD Promotion Pipeline | Branch protections, required checks, staged deploy | M-01, M-02, M-08 | @fatb4f | 2026-W10 | Done | XA-08 packet promotion gates | Canary and rollback gates automated | `pytest -q && python tools/orchestrator/run_demo.py --pre-contract ssot/examples/demo.pre_contract.json --run-root ops/runtime/runs --state-space ssot/examples/state.space.json --reason-codes ssot/policy/reason.codes.json` | `ops/runtime/m10/` |
| M-11 | #12 | P2 | Operational Runbooks | Incident/recovery/replay procedures | M-08, M-09, M-10 | @fatb4f | 2026-W11 | Done | XA-09 deterministic replay | Tabletop + live drill sign-off | `python ops/runbooks/run_drill.py --run-id pkt-dome-demo-0001 --out ops/runtime/m11/drill.json` | `ops/runtime/m11/` |
| M-12 | #13 | P2 | Compliance & Audit | Retention policy, auditability, data handling controls | M-03, M-09, M-11 | @fatb4f | 2026-W11 | Done | XA-10 audit export interfaces | Audit evidence package generated | `python tools/orchestrator/audit_drill.py --run-root ops/runtime/runs --run-id pkt-dome-demo-0001 --out ops/runtime/m12/audit.bundle.json` | `ops/runtime/m12/` |

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
| M-01 SLOs & Gates | `doc/slo_and_release_gates.md` | SLO/SLI and release gate policy with verification and evidence paths | Done |
| M-02 Runtime Contracts | `tools/orchestrator/runtime_config.py` | Runtime profile loader/validator consumed by demo runners | Done |
| M-02 Runtime Contracts | `ssot/schemas/runtime.config.schema.json` | Runtime config contract schema | Done |
| M-02 Runtime Contracts | `ssot/examples/runtime.config.json` | Runtime config example profiles (`tdd`, `refactor`) | Done |
| M-02 Runtime Contracts | `tests/test_runtime_config.py` | Validation tests for runtime profile loading behavior | Done |
| M-02 Runtime Contracts | `ssot/schemas/task.result.schema.json` | Task result contract for implementer/checker artifacts | Done |
| M-02 Runtime Contracts | `tests/test_ssot_policy_validate.py` | Policy JSON validation against authoritative schema | Done |
| M-02 Runtime Contracts | `tests/test_ssot_roundtrip.py` | SSOT JSON round-trip load/serialize verification | Done |
| M-03 Security Baseline | `doc/security/threat_model.md` | Threat model, trust boundaries, and control coverage | Done |
| M-03 Security Baseline | `doc/security/secrets_and_redaction.md` | Secret handling and runtime path guardrails policy | Done |
| M-03 Security Baseline | `tools/orchestrator/security.py` | Runtime path validation and payload redaction helpers | Done |
| M-03 Security Baseline | `ssot/schemas/orchestrator.secure_defaults.schema.json` | Secure defaults contract schema | Done |
| M-03 Security Baseline | `tests/test_security.py` | Path traversal rejection and redaction verification tests | Done |
| M-03 Security Baseline | `tests/test_dependency_allowlist.py` | Dependency allowlist audit test | Done |
| M-04 Event Reliability | `ssot/schemas/event.envelope.schema.json` | Event envelope contract with stable event IDs | Done |
| M-04 Event Reliability | `tools/orchestrator/mcp_loop.py` | Event-id idempotency and replay helpers for task-result streams | Done |
| M-04 Event Reliability | `tests/test_mcp_events.py` | Idempotent publish and replay ordering tests | Done |
| M-05 State Machine Hardening | `tools/orchestrator/state_machine.py` | Legal state transitions and reason-coded invalid transition rejection | Done |
| M-05 State Machine Hardening | `tests/test_state_machine.py` | Transition invariants and rejection tests | Done |
| M-06 Concurrency Safety | `tools/orchestrator/io_utils.py` | Atomic write utilities for runtime artifacts | Done |
| M-06 Concurrency Safety | `tests/test_concurrency_safety.py` | Parallel publish/write stress verification | Done |
| M-07 Retry/Backoff Policy | `doc/retry_and_backoff_policy.md` | Retry budget, jitter/backoff, and DLQ policy | Done |
| M-08 Observability & Alerting | `doc/observability/telemetry_and_alerts.md` | Telemetry field contract and alert thresholds | Done |
| M-09 Reproducibility & Provenance | `tools/orchestrator/audit_drill.py` | Run-level audit bundle generation and hash-chain checks | Done |
| M-10 CI/CD Promotion Pipeline | `.github/workflows/mvp-loop-gate.yml` | Required checks, replay/provenance verification, clean-runtime guard | Done |
| M-11 Operational Runbooks | `doc/runbooks/*.md` | Incident, replay, recovery, and retention runbooks | Done |
| M-12 Compliance & Audit | `doc/compliance/*.md` | Audit trail, retention, and data-handling policy artifacts | Done |

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
