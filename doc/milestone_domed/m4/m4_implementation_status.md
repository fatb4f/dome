# M4 Implementation Status

## Implemented slice

- Thin-client wrapper added at [`tools/codex/domed_client.py`](/home/src404/src/dome/tools/codex/domed_client.py) over generated gRPC stubs.
- Explicit dependency/runtime guards:
  - grpc/protobuf presence
  - generated stub availability
- Wrapper methods cover v1 RPC surface:
  - `health`, `list_capabilities`, `skill_execute`, `get_job_status`, `cancel_job`, `stream_job_events`.
- Generated-stub import path alignment fixed (`generated/python` path bootstrap + `domed.v1.*` imports).
- CI dependency pins added for grpc/protobuf in [`mvp-loop-gate.yml`](/home/src404/src/dome/.github/workflows/mvp-loop-gate.yml).

## Remaining

- Add typed SDK packaging and version pin policy for client consumers.
- Add mock/stub server harness variants (current integration test uses in-memory real server).
