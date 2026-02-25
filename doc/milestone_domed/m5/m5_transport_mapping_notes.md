# M5 Transport Mapping Notes (D2)

## Purpose

Define deterministic mapping from `ADAPTER_REQUIRED` local subprocess callsites to `domed` transport primitives.

Authoritative mapping table:

- `doc/milestone_domed/m5/m5_transport_mapping_spec.csv`

## Mapping rules

1. All migrated callsites use `DomedClient.skill_execute` (`SkillExecute` RPC).
2. `idempotency_key` must be deterministic:
   - derived from stable run context (`run_id`, `packet_id`, stage key), or
   - explicit caller key where already present.
3. Status mapping is transport-first:
   - `RpcStatus.ok=true` + terminal success state => migrated step success
   - `RpcStatus.ok=false` or failed/canceled state => migrated step failure
4. Failure paths must preserve machine-readable semantics:
   - include `job_id`, `run_id`, `state`, `status_message`
   - preserve policy/gate reason where available
5. Logging:
   - callsites currently depending on local `stdout/stderr` should consume streamed events from `StreamJobEvents`.

## Non-migrated classes

- `KEEP_LOCAL` callsites remain local by design (CI tooling and read-only metadata helpers).
- `DEPRECATE_REMOVE` callsites follow D6/D8 schedule.

