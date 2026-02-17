# Dependency Matrix (Graph Fold Implementation)

## Scope
Dependency mapping from requirements (`CL-REQ-*`) to implementation components, verification gates, and milestone ownership.

| Component | Description | Depends On | Enables | Requirement IDs | Verification | Milestone |
|---|---|---|---|---|---|---|
| C1: TaskSpec Authority Guard | Enforce TaskSpec as intent-layer authority; no method leakage | None | C2, C3, C7 | CL-REQ-0001 | Integration | M1 |
| C2: ToolContract/ToolProfile Enforcer | Resolve capability -> method allowlist and enforce side effects via `tool.api` | C1 | C3, C4, C8 | CL-REQ-0002 | Integration | M1 |
| C3: SpawnSpec Validator | Typed SpawnSpec schema gate with fail-closed unknown-field behavior | C1, C2 | C4, C7 | CL-REQ-0003 | CI Gate + Conformance | M1 |
| C4: ControlEvent Log Writer | Append-only ControlEvent stream with sequence and correlation keys | C2, C3 | C5, C6, C8 | CL-REQ-0004 | Integration | M2 |
| C5: Deterministic Ledger Materializer | Deterministic apply-order ledger from ControlEvents | C4 | C6, C8 | CL-REQ-0004, CL-REQ-0005 | Integration + Replay | M2 |
| C6: Deterministic Scheduler/Tie-Breaker | Stable ordering for scheduling/selection/conflict decisions | C5 | C8 | CL-REQ-0005 | CI Gate + Replay | M2 |
| C7: Wave Dispatcher | Dispatch loop using TaskSpec/WaveSpec + SpawnSpec | C3 | C8 | CL-REQ-0003, CL-REQ-0005 | Integration | M3 |
| C8: Gate/Promotion Engine | Deterministic gate and promotion decisions with evidence linkage | C5, C6, C7 | C9 | CL-REQ-0004, CL-REQ-0005 | Integration + Replay | M3 |
| C9: Traceability Runner | Resolve `CL-REQ-*` to checks and artifacts; fail on gaps | C8 | C10 | CL-REQ-0001..0005 | CI Gate | M4 |
| C10: CI Policy & Lint Gates | Deprecated path lint, requirement coverage gate, report publishing | C9 | Release readiness | CL-REQ-0001..0005 | CI Gate | M4 |

## Critical Path
`C1 -> C2 -> C3 -> C4 -> C5 -> C6 -> C8 -> C9 -> C10`

## Parallelizable Tracks
- Track A: `C1 -> C2 -> C3`
- Track B: `C4 -> C5 -> C6`
- Track C: `C7` (starts after C3)
- Converge: `C8`, then `C9 -> C10`

## Risk Notes
- Highest risk: C5/C6 replay determinism drift across environment/tooling versions.
- Control risk: enforce deterministic tie-break artifacts and lock toolchain versions in CI.
