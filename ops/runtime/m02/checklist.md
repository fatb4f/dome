# M-02 Checklist

- [x] Added `task.result` contract schema: `ssot/schemas/task.result.schema.json`
- [x] Added task result example: `ssot/examples/task.result.json`
- [x] Added policy schema-validation tests: `tests/test_ssot_policy_validate.py`
- [x] Added SSOT round-trip test: `tests/test_ssot_roundtrip.py`
- [x] Added `just validate-ssot` command and wired into `ci`
- [x] Captured command output in `ops/runtime/m02/command_output.txt`

## Verification

- `just validate-ssot`
- `just test`
