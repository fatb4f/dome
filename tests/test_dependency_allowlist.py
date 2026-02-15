from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _dep_name(spec: str) -> str:
    return spec.split(";", 1)[0].strip().split("[", 1)[0].split(" ", 1)[0].split(">=", 1)[0].split("==", 1)[0]


def test_project_dependencies_are_allowlisted() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = pyproject.get("project", {}).get("dependencies", [])
    allowlist = {"duckdb", "jsonschema", "pytest", "opentelemetry-sdk"}
    unknown = sorted({name for name in (_dep_name(spec) for spec in deps) if name not in allowlist})
    assert not unknown, f"Dependencies outside allowlist: {unknown}"
