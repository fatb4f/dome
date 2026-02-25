# SLO And Release Gates

## Scope

This document defines what `production-ready` means for dome and the go/no-go rules that map to gate decisions.

## Operational Definition

- Workload: packetized orchestration runs with deterministic planning, implementation, checker, and promotion stages.
- Data sensitivity: run metadata and telemetry only; secrets must not be emitted in logs or persisted artifacts.
- Concurrency: default worker fanout of 2 (`work.queue.max_workers`), with bounded retries.
- Reliability target: deterministic replay of gate decisions for equivalent run inputs.

## SLOs

- SLO-1 Availability: >= 99.9% of scheduled orchestrator runs complete with a terminal gate decision in the calendar month.
- SLO-2 Determinism: >= 99% of replayed runs (same input contract and base ref) produce the same gate status.
- SLO-3 Evidence Completeness: 100% of approved runs produce required gate and promotion artifacts.
- SLO-4 Safety: 0 critical security policy violations (secret leakage, path traversal) in release candidates.

## Release Gate Policy

- `APPROVE`:
  - all deterministic verification checks pass
  - no failing task result
  - risk score below configured threshold
- `NEEDS_HUMAN`:
  - deterministic checks pass but risk score exceeds threshold
  - release requires explicit human override with reason
- `REJECT`:
  - deterministic verify command fails, or
  - any implementer task fails

Gate decision schema is authoritative at:
- `ssot/schemas/gate.decision.schema.json`

Reason code catalog is authoritative at:
- `ssot/policy/reason.codes.json`

## Verification Commands

1. Validate SSOT contracts:
   - `just validate-ssot`
2. Run deterministic tests:
   - `just test`
3. Produce a gated run artifact set:
   - `just smoke`
4. Validate gate schema via tests:
   - `pytest -q tests/test_checkers.py`

## Expected Evidence Artifacts

For run id `pkt-dome-demo-0001`:
- `ops/runtime/runs/pkt-dome-demo-0001/gate/gate.decision.json`
- `ops/runtime/runs/pkt-dome-demo-0001/promotion/promotion.decision.json`
- `ops/runtime/runs/pkt-dome-demo-0001/run.manifest.json`
- `ops/runtime/runs/pkt-dome-demo-0001/task_results/*.result.json`

Milestone evidence folders:
- `ops/runtime/m01/` for SLO and gate documentation verification artifacts
- `ops/runtime/m02/` for runtime contract validation artifacts

## xtrlv2 Hook (XA-01)

`gate.decision.status` maps to xtrlv2 decision envelope states:
- `APPROVE` -> promote
- `NEEDS_HUMAN` -> hold for manual control
- `REJECT` -> stop and return reason codes

`reason_codes` are preserved as stable machine-readable policy signals to avoid translation drift across substrates.
