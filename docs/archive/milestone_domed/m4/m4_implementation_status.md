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
- Consumer path exercised against live service in integration tests via [`tools/codex/domed_client.py`](/home/src404/src/dome/tools/codex/domed_client.py).
- Production `run-skill` path now routes through generated thin client via [`run_task_via_domed`](/home/src404/src/dome/tools/codex/browse_skill.py) and [`dome_cli.py`](/home/src404/src/dome/tools/codex/dome_cli.py).
- Generated-client-only guardrail script added:
  - [`tools/codex/check_generated_client_only.py`](/home/src404/src/dome/tools/codex/check_generated_client_only.py)
- Stub harness matrix added:
  - [`tests/test_domed_client_stub_matrix.py`](/home/src404/src/dome/tests/test_domed_client_stub_matrix.py)
- Skill-path client wiring test added:
  - [`tests/test_browse_skill_domed_path.py`](/home/src404/src/dome/tests/test_browse_skill_domed_path.py)
- SDK/package policy documented at:
  - [`doc/milestone_domed/m4/m4_sdk_packaging_policy.md`](/home/src404/src/dome/doc/milestone_domed/m4/m4_sdk_packaging_policy.md)

## Remaining

- No remaining M4 scope for milestone closure.
