# M5 Tool Migration Dependency Matrix

## Work packages

| ID | Work package | Depends on | Output |
|---|---|---|---|
| M5-D1 | Migration register (entrypoint inventory + classification) | M4 closures (`#60`) | `m5_tool_migration_register.csv` |
| M5-D2 | Transport mapping (`legacy call -> domed job type`) | M5-D1 | mapping table and adapter specs |
| M5-D3 | Adapter implementation for `ADAPTER_REQUIRED` paths | M5-D2 | migrated wrappers |
| M5-D4 | CI guardrail expansion for bypass detection | M5-D1 | static checks in workflow |
| M5-D5 | Integration tests per migrated family | M5-D3 | passing migration test suite |
| M5-D6 | Legacy deprecation notices + removal plan | M5-D1 | deprecation schedule doc |
| M5-D7 | Production cutover | M5-D3, M5-D4, M5-D5 | all prod paths daemonized |
| M5-D8 | Legacy path removal | M5-D6, M5-D7 | bypass-free production surface |

## External dependencies

| Dependency | Why it matters | Owner | Status |
|---|---|---|---|
| `domed` daemon stability | all migrated paths require runtime availability | `dome` runtime | baseline implemented |
| generated client compatibility | migration must remain contract-safe | M2/M4 gates | active |
| operational runbooks | operator recovery during cutover | docs | pending expansion |

## Completion gate

M5 completes when:

- M5-D1..M5-D8 are complete.
- CI blocks direct production execution bypass patterns.
- Parent issue closure notes include migration delta and removed legacy surfaces.

