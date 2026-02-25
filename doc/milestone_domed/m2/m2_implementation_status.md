# M2 Implementation Status

## Implemented

- Proto contract frozen at [`proto/domed/v1/domed.proto`](/home/src404/src/dome/proto/domed/v1/domed.proto).
- Reproducible codegen pipeline:
  - [`tools/domed/gen.sh`](/home/src404/src/dome/tools/domed/gen.sh)
  - [`tools/domed/requirements-codegen.txt`](/home/src404/src/dome/tools/domed/requirements-codegen.txt)
- Generated thin-client artifacts committed under:
  - [`generated/python`](/home/src404/src/dome/generated/python)
  - [`generated/descriptors/domed_v1.pb`](/home/src404/src/dome/generated/descriptors/domed_v1.pb)
  - [`generated/codegen_manifest.json`](/home/src404/src/dome/generated/codegen_manifest.json)
- CI enforcement wired:
  - drift gate via [`tools/domed/check_codegen_drift.sh`](/home/src404/src/dome/tools/domed/check_codegen_drift.sh)
  - breaking-change gate via [`tools/domed/check_proto_breaking.sh`](/home/src404/src/dome/tools/domed/check_proto_breaking.sh)
  - workflow integration in [`mvp-loop-gate.yml`](/home/src404/src/dome/.github/workflows/mvp-loop-gate.yml)
- Basic generated-stub smoke tests:
  - [`tests/test_domed_codegen.py`](/home/src404/src/dome/tests/test_domed_codegen.py)

## Remaining (handoff to M3/M4)

- Implement runtime `domed` service handlers against frozen RPC contracts (M3).
- Implement consumer thin-client overlay and Dome skill mapping to generated stubs (M4).

