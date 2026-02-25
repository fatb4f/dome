# M4 Clients + CI Analysis

## Baseline

- Proto and generated artifacts exist (`generated/python/domed/v1/*`).
- CI enforces drift and compatibility at source/proto level.

## Gap

- No thin-client wrapper for `domed` runtime usage from `dome` code paths.
- No documented runtime dependency setup for grpc/protobuf.

## Implementation slice (M4 now)

- Add a generated-client wrapper module with explicit dependency checks.
- Add a minimal call surface for health/capabilities/skill-execute/status/stream/cancel.
- Add tests for wrapper request-shape behavior using a fake stub object.

