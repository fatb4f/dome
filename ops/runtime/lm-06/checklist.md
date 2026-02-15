# LM-06 Checklist

- [x] Added packet artifacts for `pkt-dome-lm-06-deterministic-timestamps-replay`.
- [x] Made `memory_api.upsert_capsule` accept deterministic `updated_ts` input.
- [x] Removed reliance on runtime clock for run_fact first/last seen updates in `memoryd`.
- [x] Preserved deterministic task/event timestamp derivation from artifacts/envelopes.
- [x] Added regression coverage for deterministic updated_ts behavior.
