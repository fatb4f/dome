# Tracker (Graph Fold Execution)

## Status Legend
- `not_started`
- `in_progress`
- `blocked`
- `done`

## Milestone Summary
| Milestone | Scope | Status | Target Gate |
|---|---|---|---|
| M1 | Authority + Contracts (`C1-C3`) | done | CL-REQ-0001..0003 checks passing |
| M2 | ControlEvent + Determinism (`C4-C6`) | done | CL-REQ-0004..0005 replay/integration passing |
| M3 | Wave Loop + Promotion (`C7-C8`) | done | deterministic gate/promotion artifacts |
| M4 | Traceability + CI Hard Gates (`C9-C10`) | done | requirement coverage + lint gates enforced |

## Component Tracker
| ID | Component | Milestone | GitHub Issue | Packet ID | Requirement IDs | Owner | Status | Depends On | Evidence Artifact |
|---|---|---|---|---|---|---|---|
| C1 | TaskSpec Authority Guard | M1 | `#45` | `pkt-dome-graph-001-taskspec-intent-authority` | CL-REQ-0001 | TBD | done | - | `ops/runtime/graph-001/checklist.md` |
| C2 | ToolContract/ToolProfile Enforcer | M1 | `#46` | `pkt-dome-graph-002-toolcontract-method-boundary` | CL-REQ-0002 | TBD | done | C1 | `ops/runtime/graph-001/command_output.txt` |
| C3 | SpawnSpec Validator | M1 | `#47` | `pkt-dome-graph-003-spawnspec-schema-gate` | CL-REQ-0003 | TBD | done | C1,C2 | `ssot/schemas/spawn.spec.schema.json` |
| C4 | ControlEvent Log Writer | M2 | `#48` | `pkt-dome-graph-004-controlevent-append-only-log` | CL-REQ-0004 | TBD | done | C2,C3 | `ops/runtime/graph-004/command_output.txt` |
| C5 | Deterministic Ledger Materializer | M2 | `#49` | `pkt-dome-graph-005-deterministic-ledger-materializer` | CL-REQ-0004,CL-REQ-0005 | TBD | done | C4 | `ops/runtime/graph-005/command_output.txt` |
| C6 | Deterministic Scheduler/Tie-Breaker | M2 | `#50` | `pkt-dome-graph-006-scheduler-tiebreak-contracts` | CL-REQ-0005 | TBD | done | C5 | `ops/runtime/graph-006/command_output.txt` |
| C7 | Wave Dispatcher | M3 | `#51` | `pkt-dome-graph-007-wave-dispatcher` | CL-REQ-0003,CL-REQ-0005 | TBD | done | C3 | `ops/runtime/graph-007/command_output.txt` |
| C8 | Gate/Promotion Engine | M3 | `#52` | `pkt-dome-graph-008-gate-promotion-engine` | CL-REQ-0004,CL-REQ-0005 | TBD | done | C5,C6,C7 | `ops/runtime/graph-008/command_output.txt` |
| C9 | Traceability Runner | M4 | `#53` | `pkt-dome-graph-009-requirement-traceability-runner` | CL-REQ-0001..0005 | TBD | done | C8 | `artifacts/ci/c9_traceability_report.json` |
| C10 | CI Policy & Lint Gates | M4 | `#54` | `pkt-dome-graph-010-ci-policy-deprecated-path-lint` | CL-REQ-0001..0005 | TBD | done | C9 | `.github/workflows/mvp-loop-gate.yml` |

## Blockers
| Date | Item | Impact | Owner | Resolution |
|---|---|---|---|---|
| TBD | None logged | - | - | - |

## Next Actions
1. Execute `C1` packet and post evidence under `ops/runtime/graph-001/`.
2. On `C1` completion, advance `C2` then `C3` sequentially.
3. Keep packet and issue status synchronized at each merge.
