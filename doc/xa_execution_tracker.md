# XA Execution Tracker

Date: 2026-02-14

## Sequence

| Order | XA | Milestone Issue | Packet ID | Status |
|---:|---|---:|---|---|
| 1 | XA-01 | #14 | `pkt-dome-xa-01-decision-semantics-map` | Ready |
| 2 | XA-02 | #15 | `pkt-dome-xa-02-envelope-dual-read` | Waiting on XA-01 |
| 3 | XA-03 | #16 | `pkt-dome-xa-03-helper-event-envelope` | Waiting on XA-02 |
| 4 | XA-04 | #17 | `pkt-dome-xa-04-evidence-capsule-adapter` | Waiting on XA-02 |
| 5 | XA-05 | #18 | `pkt-dome-xa-05-state-layout-compat-mode` | Waiting on XA-02 |
| 6 | XA-06 | #19 | `pkt-dome-xa-06-outer-loop-tick-controller` | Waiting on XA-02, XA-03 |
| 7 | XA-07 | #20 | `pkt-dome-xa-07-pattern-catalog-rank-policy` | Waiting on XA-02 |
| 8 | XA-08 | #21 | `pkt-dome-xa-08-schema-pin-lint-gates` | Waiting on XA-03 |
| 9 | XA-09 | #22 | `pkt-dome-xa-09-state-migration-bridge` | Waiting on XA-05 |
| 10 | XA-10 | #23 | `pkt-dome-xa-10-pattern-catalog-ingest` | Waiting on XA-01 |
| 11 | XA-11 | #24 | `pkt-dome-xa-11-profile-catalog-mapping` | Waiting on XA-07, XA-10 |

## Packet Root

- `packets/engineering/dome_xa_alignment/`

Each milestone packet includes:
- `<packet_id>.pre_contract.json`
- `<packet_id>/contract.json`
- `<packet_id>/EXEC_PROMPT.md`
