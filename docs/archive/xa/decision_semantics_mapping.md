# XA-01 Decision Semantics Mapping

Mapping between dome gate statuses and xtrl substrate statuses:

- `APPROVE` -> `PROMOTE`
- `REJECT` -> `DENY`
- `NEEDS_HUMAN` -> `STOP`

Implementation:
- `tools/orchestrator/xa_mapping.py`
- `tools/orchestrator/checkers.py` emits `substrate_status`
