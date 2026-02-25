# M4 SDK Packaging and Versioning Policy

## Scope

This policy governs the generated `domed.v1` client usage and release hygiene for `dome`.

## Versioning

- Canonical API surface is `proto/domed/v1/domed.proto`.
- `v1` is non-breaking:
  - no RPC removals
  - no message/enum removals
  - no field number/type/label changes
- Additive-only evolution is allowed under `v1`.
- Breaking changes require a new versioned package (`v2`) and explicit migration notes.

## Runtime dependency pins

- `grpcio==1.76.0`
- `protobuf==6.33.5`

These pins are required in CI and must be kept consistent with codegen outputs.

## Artifacts

Committed generated artifacts:

- `generated/python/domed/v1/domed_pb2.py`
- `generated/python/domed/v1/domed_pb2_grpc.py`
- `generated/descriptors/domed_v1.pb`
- `generated/codegen_manifest.json`

Generation command:

- `tools/domed/gen.sh`

## Enforcement

- Drift gate: `tools/domed/check_codegen_drift.sh`
- Breaking gate: `tools/domed/check_proto_breaking.sh`
- Production command path (`dome-codex-skill run-skill`) must route via generated thin client (`run_task_via_domed`), enforced by:
  - `tools/codex/check_generated_client_only.py`
- Stub harness matrix required:
  - `tests/test_domed_client_stub_matrix.py`

## Release criteria for M4

- Generated-client-only production path is validated in CI.
- Stub matrix tests pass.
- Integration path through `DomedClient` is validated.

