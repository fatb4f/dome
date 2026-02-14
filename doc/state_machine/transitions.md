# State Transition Table

Legal transitions:
- `QUEUED -> CLAIMED` on `claim`
- `CLAIMED -> RUNNING` on `run`
- `RUNNING -> GATED` on `gate_pass`
- `RUNNING -> BLOCKED` on `gate_fail`
- `GATED -> DONE` on `gate_pass`
- `GATED -> BLOCKED` on `gate_fail`
- `QUEUED|CLAIMED|RUNNING|GATED -> BLOCKED` on `block`

Runtime enforcement lives in `tools/orchestrator/state_machine.py`.
Invalid transitions emit reason codes of form `STATE.INVALID_TRANSITION.<from>.<signal>`.

Versioning:
- transition table version is currently `0.2.0` aligned with runtime artifact schema version.
- when state shape evolves, transition compatibility rules must preserve deterministic replay for prior manifests.
