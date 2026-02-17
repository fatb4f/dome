# Tracker (Graph Fold Execution)

## Status Legend
- `not_started`
- `in_progress`
- `blocked`
- `done`

## Milestone Summary
| Milestone | Scope | Status | Target Gate |
|---|---|---|---|
| M1 | Authority + Contracts (`C1-C3`) | not_started | CL-REQ-0001..0003 checks passing |
| M2 | ControlEvent + Determinism (`C4-C6`) | not_started | CL-REQ-0004..0005 replay/integration passing |
| M3 | Wave Loop + Promotion (`C7-C8`) | not_started | deterministic gate/promotion artifacts |
| M4 | Traceability + CI Hard Gates (`C9-C10`) | not_started | requirement coverage + lint gates enforced |

## Component Tracker
| ID | Component | Milestone | Requirement IDs | Owner | Status | Depends On | Evidence Artifact |
|---|---|---|---|---|---|---|---|
| C1 | TaskSpec Authority Guard | M1 | CL-REQ-0001 | TBD | not_started | - | `artifacts/conformance/c1_authority_guard.json` |
| C2 | ToolContract/ToolProfile Enforcer | M1 | CL-REQ-0002 | TBD | not_started | C1 | `artifacts/integration/c2_tool_enforcement.json` |
| C3 | SpawnSpec Validator | M1 | CL-REQ-0003 | TBD | not_started | C1,C2 | `artifacts/ci/c3_spawnspec_gate.json` |
| C4 | ControlEvent Log Writer | M2 | CL-REQ-0004 | TBD | not_started | C2,C3 | `artifacts/integration/c4_controlevent_log.json` |
| C5 | Deterministic Ledger Materializer | M2 | CL-REQ-0004,CL-REQ-0005 | TBD | not_started | C4 | `artifacts/replay/c5_ledger_replay.json` |
| C6 | Deterministic Scheduler/Tie-Breaker | M2 | CL-REQ-0005 | TBD | not_started | C5 | `artifacts/ci/c6_tiebreak_determinism.json` |
| C7 | Wave Dispatcher | M3 | CL-REQ-0003,CL-REQ-0005 | TBD | not_started | C3 | `artifacts/integration/c7_wave_dispatch.json` |
| C8 | Gate/Promotion Engine | M3 | CL-REQ-0004,CL-REQ-0005 | TBD | not_started | C5,C6,C7 | `artifacts/integration/c8_gate_promotion.json` |
| C9 | Traceability Runner | M4 | CL-REQ-0001..0005 | TBD | not_started | C8 | `artifacts/ci/c9_traceability_report.json` |
| C10 | CI Policy & Lint Gates | M4 | CL-REQ-0001..0005 | TBD | not_started | C9 | `artifacts/ci/c10_policy_gates.json` |

## Blockers
| Date | Item | Impact | Owner | Resolution |
|---|---|---|---|---|
| TBD | None logged | - | - | - |

## Next Actions
1. Assign owners for `C1-C3`.
2. Create initial check stubs for `CL-REQ-0001..0003`.
3. Wire tracker updates into weekly review cadence.
