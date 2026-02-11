import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from opentelemetry import trace
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import task, workflow

OUT_DIR = Path(__file__).resolve().parent.parent / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _env_flag(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "y", "on"}


def init_tracing() -> None:
    """Option A: OpenLLMetry (Traceloop). Exports OTLP/HTTP to TRACELOOP_BASE_URL."""
    disable_batch = _env_flag("TRACELOOP_DISABLE_BATCH", default=True)
    Traceloop.init(
        app_name=os.getenv("APP_NAME", "mvpv0.2-demo"),
        disable_batch=disable_batch,
        resource_attributes={
            "ssot": "mvpv0.2",
            "loop": "plan-execute-gate",
        },
    )


def _sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class DAGNode:
    reqs: List[str]
    deps: List[str]
    provs: List[str]
    assert_: List[str]


def plan() -> Dict[str, DAGNode]:
    """PLAN: create a bounded DAG of work items."""
    return {
        "tool.smoke": DAGNode(
            reqs=["tool available: python"],
            deps=[],
            provs=[
                "telemetry.otel.trace_id_hex",
                "telemetry.otel.span_id_hex",
                "telemetry.signals.tool.exit_code",
                "telemetry.artifacts[].sha256",
            ],
            assert_=["tool.exit_code == 0"],
        )
    }


@task(name="execute.tool.smoke")
def execute_tool_smoke() -> Dict[str, Any]:
    """EXECUTE: run a tool action and capture rich signals.

    Critical rule: all decision-relevant signals must be emitted into telemetry.
    """
    ts = int(time.time() * 1000)
    stdout_path = OUT_DIR / f"stdout.{ts}.log"
    stderr_path = OUT_DIR / f"stderr.{ts}.log"

    cmd = ["python", "-c", "print('hello from tool')"]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    stdout_path.write_text(proc.stdout)
    stderr_path.write_text(proc.stderr)

    stdout_sha = _sha256_path(stdout_path)
    stderr_sha = _sha256_path(stderr_path)

    # ---- Telemetry emission (SSOT) ----
    span = trace.get_current_span()
    span.set_attribute("tool.command", " ".join(cmd))
    span.set_attribute("tool.exit_code", int(proc.returncode))
    span.set_attribute("artifact.stdout_path", str(stdout_path))
    span.set_attribute("artifact.stderr_path", str(stderr_path))
    span.set_attribute("artifact.stdout_sha256", stdout_sha)
    span.set_attribute("artifact.stderr_sha256", stderr_sha)

    ctx = span.get_span_context()
    telemetry_bundle = {
        "otel": {
            "backend": os.getenv("TELEMETRY_BACKEND", "langfuse"),
            "trace_id_hex": f"{ctx.trace_id:032x}",
            "span_id_hex": f"{ctx.span_id:016x}",
            "project": os.getenv("APP_NAME", "mvpv0.2-demo"),
            "run_id": f"run-{ts}",
        },
        "signals": {
            "tool.exit_code": int(proc.returncode),
        },
        "artifacts": [
            {
                "path": str(stdout_path),
                "sha256": stdout_sha,
                "bytes": stdout_path.stat().st_size,
            },
            {
                "path": str(stderr_path),
                "sha256": stderr_sha,
                "bytes": stderr_path.stat().st_size,
            },
        ],
    }

    # Return only the telemetry-derived bundle (gate must not use raw stdout/stderr contents)
    return telemetry_bundle


def gate(node: DAGNode, telemetry_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """GATE: update state only from telemetry.

    Deterministic rule for demo: ALLOW only when tool.exit_code == 0.
    """
    signals = telemetry_bundle.get("signals", {})
    exit_code = int(signals.get("tool.exit_code", 1))

    if exit_code == 0:
        return {"status": "DONE", "reason_code": None, "notes": None}

    return {"status": "BLOCKED", "reason_code": "EXEC.NONZERO_EXIT", "notes": None}


@workflow(name="mvpv0.2.plan_execute_gate")
def run() -> Dict[str, Any]:
    nodes = plan()

    # Execute the (single) frontier node
    telemetry_by_node: Dict[str, Dict[str, Any]] = {}
    telemetry_by_node["tool.smoke"] = execute_tool_smoke()

    results: Dict[str, Any] = {"nodes": {}, "meta": {}}
    for node_id, node in nodes.items():
        tb = telemetry_by_node.get(node_id, {})
        g = gate(node, tb)
        results["nodes"][node_id] = {
            "node": {
                "reqs": node.reqs,
                "deps": node.deps,
                "provs": node.provs,
                "assert": node.assert_,
            },
            "telemetry": tb,
            "gate": g,
        }

    # Write a lightweight state snapshot (v0.2 JSON)
    snapshot = {
        "version": "0.2.0",
        "memory": [],
        "task_preferences": {"default_priority": 0, "telemetry_is_ssot": True},
        "work_items": [
            {
                "work_id": "tool.smoke",
                "status": results["nodes"]["tool.smoke"]["gate"]["status"],
                "node": results["nodes"]["tool.smoke"]["node"],
                "telemetry": results["nodes"]["tool.smoke"]["telemetry"],
                "gate": results["nodes"]["tool.smoke"]["gate"],
            }
        ],
    }

    snapshot_path = OUT_DIR / "state.space.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2))

    return results


def main() -> None:
    init_tracing()
    run()


if __name__ == "__main__":
    main()
