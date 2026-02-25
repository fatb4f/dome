from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except Exception:  # noqa: BLE001
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]

REQUIRED_IDENTITY_GRAPH_CONTRACTS = {
    "browse_feedback_event": "1.0.0",
    "browse_feedback_batch": "1.0.0",
    "feedforward_policy_bundle": "1.0.0",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(schema_path: Path, obj: Any, label: str) -> None:
    schema = _load_json(schema_path)
    if Draft202012Validator is not None and FormatChecker is not None:
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(obj), key=lambda e: list(e.path))
        if errors:
            err = errors[0]
            path = ".".join(str(p) for p in err.path) or "<root>"
            raise RuntimeError(f"{label} schema error at {path}: {err.message}")
        return

    # Fallback checks when jsonschema dependency is unavailable.
    if schema.get("type") == "object" and not isinstance(obj, dict):
        raise RuntimeError(f"{label} schema error: expected object")
    for key in schema.get("required", []):
        if key not in obj:
            raise RuntimeError(f"{label} schema error: missing required key {key}")


def validate_codex_browse_contract(codex_browse_root: Path) -> dict[str, Path]:
    skill_root = codex_browse_root / "docs" / "codex-web-browse-skill"
    contract_path = skill_root / "contract.json"
    contract = _load_json(contract_path)
    schemas = contract.get("schemas", {})
    for key in ("task", "result", "prefs"):
        if key not in schemas:
            raise RuntimeError(f"missing schema mapping for {key}")
    paths = {
        "contract": contract_path,
        "task": skill_root / schemas["task"],
        "result": skill_root / schemas["result"],
        "prefs": skill_root / schemas["prefs"],
        "runner": skill_root / contract["skill"]["entrypoint"],
    }
    for p in paths.values():
        if not p.exists():
            raise RuntimeError(f"missing required codex-browse artifact: {p}")
    # Parse schema JSON eagerly.
    _ = _load_json(paths["task"])
    _ = _load_json(paths["result"])
    _ = _load_json(paths["prefs"])
    return paths


def validate_identity_graph_contracts(identity_graph_root: Path) -> None:
    version_path = identity_graph_root / "spec" / "version.json"
    version = _load_json(version_path)
    contracts = version.get("contracts", {})
    for name, expected in REQUIRED_IDENTITY_GRAPH_CONTRACTS.items():
        if contracts.get(name) != expected:
            raise RuntimeError(f"identity-graph contract mismatch for {name}: {contracts.get(name)} != {expected}")
    for name in [
        "browse_feedback_event.schema.json",
        "browse_feedback_batch.schema.json",
        "feedforward_policy_bundle.schema.json",
    ]:
        path = identity_graph_root / "spec" / name
        if not path.exists():
            raise RuntimeError(f"identity-graph schema missing: {path}")
        _ = _load_json(path)


def run_task(codex_browse_root: Path, task: dict[str, Any], prefs_path: Path | None = None) -> dict[str, Any]:
    paths = validate_codex_browse_contract(codex_browse_root)
    _validate(paths["task"], task, "task")
    env = os.environ.copy()
    if prefs_path is not None:
        env["CODEX_BROWSE_PREFS"] = str(prefs_path)
        _validate(paths["prefs"], _load_json(prefs_path), "prefs")
    proc = subprocess.run(
        ["python3", str(paths["runner"])],
        input=json.dumps(task),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"runner failed rc={proc.returncode}: {proc.stderr.strip()}")
    result = json.loads(proc.stdout)
    _validate(paths["result"], result, "result")
    return result


def run_task_via_domed(
    *,
    task: dict[str, Any],
    domed_endpoint: str,
    profile: str = "work",
    idempotency_key: str = "dome-cli",
    max_attempts: int = 2,
    retry_sleep_seconds: float = 0.05,
) -> dict[str, Any]:
    from tools.codex.domed_client import DomedClient, DomedClientConfig

    client = DomedClient(DomedClientConfig(endpoint=domed_endpoint))
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.skill_execute(
                skill_id="skill-execute",
                profile=profile,
                idempotency_key=idempotency_key,
                task=task,
                constraints={},
            )
            break
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= max_attempts:
                raise RuntimeError(
                    f"domed skill_execute failed after {attempt} attempts: {exc}"
                ) from exc
            time.sleep(retry_sleep_seconds)
    else:  # pragma: no cover
        raise RuntimeError(f"domed skill_execute failed: {last_exc}")
    return {
        "ok": bool(resp.status.ok),
        "job_id": resp.job_id,
        "run_id": resp.run_id,
        "state": int(resp.state),
        "status_message": resp.status.message,
    }
