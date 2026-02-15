# Post-LM11 OTLP Memory Execution Tracker

Date: 2026-02-15

Baseline:
- Last completed LM milestone: LM-11 (`#37`)
- Tracker issue for this phase: `#42`

## Planned Milestones

| Order | Milestone | Issue | Scope | Priority | Depends On | Status |
|---:|---|---:|---|---|---|---|
| 1 | PL-01 Binder shadow-mode daemon rollout | #38 | Run binder in daemon loop under explicit shadow mode with deterministic checkpointing. | P0 | LM-11 (#37) | Planned |
| 2 | PL-02 Binder-aware ops alerts + runbook wiring | #39 | Add binder health thresholds, alert hooks, and deterministic recovery runbook flows. | P1 | PL-01 (#38) | Planned |
| 3 | PL-03 Planner retrieval loop with memory priors | #41 | Query/rank memory priors by TaskSpec and apply bounded deterministic single-shot promo rules. | P0 | PL-01 (#38) | Planned |
| 4 | PL-04 Guardrails facts ingestion + policy reason-code path | #40 | Persist guard facts and preserve `policy_reason_code`/`failure_reason_code` separation end-to-end. | P0 | PL-01 (#38) | Planned |
| 5 | PL-05 End-to-end deterministic pipeline validation | #43 | Validate replay/fuzz determinism across materialize -> binder -> retrieve and enforce release gates. | P0 | PL-02 (#39), PL-03 (#41), PL-04 (#40) | Planned |

## Dependency Matrix

`1` means row item depends on column item.

| Row \\ Col | PL-01 | PL-02 | PL-03 | PL-04 | PL-05 |
|---|---:|---:|---:|---:|---:|
| PL-01 | 0 | 0 | 0 | 0 | 0 |
| PL-02 | 1 | 0 | 0 | 0 | 0 |
| PL-03 | 1 | 0 | 0 | 0 | 0 |
| PL-04 | 1 | 0 | 0 | 0 | 0 |
| PL-05 | 0 | 1 | 1 | 1 | 0 |

## Mapping To Plan Concepts

- PL-01 maps to revised substrate checklist: ingest/materialization/binder rollout behavior.
- PL-02 maps to revised substrate checklist: ops gates and runbook/alert wiring.
- PL-03 maps to revised substrate checklist: planner retrieval loop from memory priors.
- PL-04 maps to revised substrate checklist: guardrails facts + policy semantics path.
- PL-05 maps to revised substrate checklist: replay/fuzz deterministic pipeline validation.

Reference plan doc:
- `doc/observability/python_standard_and_memory_substrate_plan_with_concepts.md`
