# xtrlv2 SSOT Pins

This directory pins SSOT artifacts from `xtrlv2` that `dome` depends on for
cross-repo compatibility tests.

## Update workflow

1. Copy updated artifacts from `xtrlv2` into this directory.
2. Recompute SHA-256 for each artifact.
3. Update `pin_manifest.json`.
4. Run:
   - `pytest -q tests/test_xtrlv2_contract_pin.py`
5. Commit pin updates with migration notes in observability docs when semantics change.
