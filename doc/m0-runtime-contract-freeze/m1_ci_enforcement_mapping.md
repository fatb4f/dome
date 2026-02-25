# M1 CI Enforcement Mapping

Issue: `#57`  
Depends on: `#61` (Runtime Contract Freeze, decision-only)  
Last updated: 2026-02-25

## Purpose

Define the CI/policy gates that enforce M1 decisions before M2-M4 implementation is promoted.

## Gate map

| Gate ID | Enforcement target | Rule | Evidence |
| --- | --- | --- | --- |
| G-CI-001 | Schema integrity | SSOT schema/examples must validate. | `tests/test_schema_examples_validate.py` |
| G-CI-002 | Policy schema integrity | Policy JSON must validate against SSOT schemas. | `tests/test_ssot_policy_validate.py` |
| G-CI-003 | Contract pin integrity | Pinned upstream schema hashes must match manifest. | `tests/test_xtrlv2_contract_pin.py` |
| G-CI-004 | Reuse-only guard | New contract families must not duplicate an existing reusable SSOT family. | `m1_contract_reuse_matrix.md` + duplication check script (M2 task) |
| G-CI-005 | Compatibility class enforcement | Contract changes (`proto`, `schema`, `manifest`) must pass required compatibility checks. | change classification policy + CI checks (M2/M4 tasks) |
| G-CI-006 | Thin-client-only runtime path | Runtime execution path must use generated thin clients only. | static guard + integration test (M4 task) |
| G-CI-007 | Provenance presence | Each run must emit canonical provenance fields. | `run.manifest` validation + integration run checks (M3 task) |
| G-CI-008 | Stream determinism | Event stream cursor/sequence behavior must be deterministic and replay-safe. | stream resume tests (M3/M4 task) |

## Change classification and required checks

| Change class | Examples | Required checks |
| --- | --- | --- |
| `schema` | `ssot/schemas/*`, schema-required fields | schema validation + compatibility rule check |
| `proto` | gateway rpc/messages | breaking-change check + codegen drift |
| `manifest` | skill/tool/runtime manifest contracts | schema validation + policy gate checks |
| `policy` | reason codes, secure defaults, thin-client policy | policy schema validation + integration conformance |

## Execution ownership

| Owner issue | CI/policy responsibilities |
| --- | --- |
| `#58` | Define and wire API compatibility + drift checks |
| `#59` | Enforce provenance and stream behavior at runtime |
| `#60` | Enforce thin-client-only path and client integration checks |

