# Milestones and Issues (Execution Backlog)

## Milestones

### M1: Authority and Contracts Baseline
- Scope: `C1-C3`
- Requirements: `CL-REQ-0001`, `CL-REQ-0002`, `CL-REQ-0003`
- Success: SpawnSpec + authority split fully enforced by automated gates.

### M2: Closed-Loop Ledger and Deterministic Execution
- Scope: `C4-C6`
- Requirements: `CL-REQ-0004`, `CL-REQ-0005`
- Success: ControlEvent SSOT + deterministic replay checks passing.

### M3: Wave Orchestration and Promotion Gates
- Scope: `C7-C8`
- Requirements: `CL-REQ-0003`, `CL-REQ-0004`, `CL-REQ-0005`
- Success: deterministic dispatch/gate/promotion loop in integration tests.

### M4: Traceability and CI Hard Gates
- Scope: `C9-C10`
- Requirements: `CL-REQ-0001..0005`
- Success: CI blocks missing requirement evidence and deprecated references.

## Issues

### DOME-GRAPH-001: Enforce TaskSpec Intent Authority
- Milestone: M1
- Depends on: None
- Requirements: CL-REQ-0001
- Deliverables:
  - TaskSpec authority guard implementation
  - negative test for method leakage
- Acceptance Criteria:
  - intent-level actions cannot directly invoke concrete methods
  - integration test proves capability resolution occurs only via ToolContract

### DOME-GRAPH-002: Enforce ToolContract Method Boundary
- Milestone: M1
- Depends on: DOME-GRAPH-001
- Requirements: CL-REQ-0002
- Deliverables:
  - ToolContract allowlist enforcement in `tool.api`
  - structured contract-violation errors
- Acceptance Criteria:
  - out-of-contract tool calls are rejected with typed errors
  - side effects only occur through contract-validated paths

### DOME-GRAPH-003: Implement SpawnSpec Schema Gate
- Milestone: M1
- Depends on: DOME-GRAPH-001, DOME-GRAPH-002
- Requirements: CL-REQ-0003
- Deliverables:
  - SpawnSpec schema and validator
  - fail-closed unknown-field behavior
- Acceptance Criteria:
  - invalid/unknown fields block dispatch
  - dispatch audit includes schema validation result

### DOME-GRAPH-004: Implement ControlEvent Append-Only Log
- Milestone: M2
- Depends on: DOME-GRAPH-002, DOME-GRAPH-003
- Requirements: CL-REQ-0004
- Deliverables:
  - authoritative ControlEvent writer
  - event sequence + correlation keys
- Acceptance Criteria:
  - ledger decisions read from ControlEvent stream only
  - OTel records can be generated from ControlEvent events

### DOME-GRAPH-005: Build Deterministic Ledger Materializer
- Milestone: M2
- Depends on: DOME-GRAPH-004
- Requirements: CL-REQ-0004, CL-REQ-0005
- Deliverables:
  - deterministic apply-order engine
  - replay harness for ledger equivalence
- Acceptance Criteria:
  - replay on identical inputs yields same ledger state
  - divergence emits deterministic failure signal

### DOME-GRAPH-006: Implement Scheduler Tie-Break Contracts
- Milestone: M2
- Depends on: DOME-GRAPH-005
- Requirements: CL-REQ-0005
- Deliverables:
  - deterministic tie-break policy for scheduling/selection/conflict
  - persisted decision artifact fields
- Acceptance Criteria:
  - equal-score cases resolve identically across repeated runs
  - artifact logs include tie-break fields for every decision

### DOME-GRAPH-007: Implement Wave Dispatcher
- Milestone: M3
- Depends on: DOME-GRAPH-003
- Requirements: CL-REQ-0003, CL-REQ-0005
- Deliverables:
  - dispatch wave loop with bounded SpawnSpec
  - worker lifecycle state handling
- Acceptance Criteria:
  - wave dispatch follows deterministic ordering inputs
  - worker completion/timeout paths emit ControlEvents

### DOME-GRAPH-008: Implement Gate/Promotion Engine
- Milestone: M3
- Depends on: DOME-GRAPH-005, DOME-GRAPH-006, DOME-GRAPH-007
- Requirements: CL-REQ-0004, CL-REQ-0005
- Deliverables:
  - deterministic gate decision computation
  - promotion decision with evidence linkage
- Acceptance Criteria:
  - gate/promotion outputs are reproducible from ledger + evidence
  - promotion payload includes full evidence references

### DOME-GRAPH-009: Implement Requirement Traceability Runner
- Milestone: M4
- Depends on: DOME-GRAPH-008
- Requirements: CL-REQ-0001..0005
- Deliverables:
  - requirement-to-check mapping resolver
  - traceability coverage report artifact
- Acceptance Criteria:
  - all CL-REQ IDs map to checks and evidence paths
  - unresolved requirement mappings fail the job

### DOME-GRAPH-010: Enforce CI Policy and Deprecated Path Lint
- Milestone: M4
- Depends on: DOME-GRAPH-009
- Requirements: CL-REQ-0001..0005
- Deliverables:
  - CI rule for requirement coverage
  - lint rule blocking `doc/reviews/dome_review_pack_v2` references in active docs
- Acceptance Criteria:
  - CI fails on missing coverage or deprecated reference regressions
  - CI publishes policy gate summary artifact
