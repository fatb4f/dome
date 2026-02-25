# M5 Issue Execution Map

Parent:

- `#62` - M5 Tool Migration Execution Plan

Sub-issues:

1. `#63` - M5-D1 Inventory and Classification Baseline
2. `#64` - M5-D2 Transport Mapping Specification
3. `#65` - M5-D3 Adapter Implementation for Required Paths
4. `#66` - M5-D4 CI Bypass Guardrail Expansion
5. `#67` - M5-D5 Migration Integration and Failure Tests
6. `#68` - M5-D6 Legacy Deprecation and Removal Schedule
7. `#69` - M5-D7 Production Cutover to domed
8. `#70` - M5-D8 Legacy Path Removal

Suggested execution sequence:

1. `#63`
2. `#64`
3. `#66` (in parallel start once baseline exists)
4. `#65`
5. `#67`
6. `#68`
7. `#69`
8. `#70`

D2 artifacts:

- `doc/milestone_domed/m5/m5_transport_mapping_spec.csv`
- `doc/milestone_domed/m5/m5_transport_mapping_notes.md`

D3 artifacts:

- `doc/milestone_domed/m5/m5_d3_adapter_resolution.md`
- `tests/test_m5_d3_resolution.py`

D5 artifacts:

- `tests/test_m5_failure_modes.py`
