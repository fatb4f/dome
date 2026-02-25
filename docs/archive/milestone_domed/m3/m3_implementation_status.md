# M3 Implementation Status

## Implemented slice

- Runtime lifecycle state store added at [`tools/domed/runtime_state.py`](/home/src404/src/dome/tools/domed/runtime_state.py):
  - job submit with idempotency ledger
  - transition guards for terminal states
  - cancel semantics
  - monotonic per-job event sequencing with cursor reads
- Coverage tests added at [`tests/test_domed_runtime_state.py`](/home/src404/src/dome/tests/test_domed_runtime_state.py).
- Live in-memory gRPC service implemented at [`tools/domed/service.py`](/home/src404/src/dome/tools/domed/service.py) for:
  - `Health`, `ListCapabilities`, `SkillExecute`, `GetJobStatus`, `CancelJob`, `StreamJobEvents`
  - `GetGateDecision`, `GetPromotionDecision` as explicit `E_NOT_FOUND` placeholders for M3
- End-to-end lifecycle integration test added at [`tests/test_domed_service_integration.py`](/home/src404/src/dome/tests/test_domed_service_integration.py).
- Durable runtime state backend added at [`tools/domed/sqlite_state.py`](/home/src404/src/dome/tools/domed/sqlite_state.py) with:
  - sqlite persistence for jobs/idempotency/events
  - TTL garbage collection (`gc(ttl_seconds=...)`)
- Daemon entrypoint implemented at [`tools/domed/daemon.py`](/home/src404/src/dome/tools/domed/daemon.py) and exposed as `domed` script in [`pyproject.toml`](/home/src404/src/dome/pyproject.toml).
- Concrete job types wired in `SkillExecute`:
  - `skill-execute` / `job.noop` (success path)
  - `job.log` (log events + success)
  - `job.fail` (error event + failed state)
- Additional persistence tests added:
  - [`tests/test_domed_sqlite_state.py`](/home/src404/src/dome/tests/test_domed_sqlite_state.py)

## Remaining

- Replace placeholder gate/promotion responses once policy artifacts are wired.
