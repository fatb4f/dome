from __future__ import annotations

from concurrent import futures
import hashlib
import json
from pathlib import Path
import sys
from time import sleep, time
from typing import Any
from uuid import uuid4

import grpc  # type: ignore

from tools.domed.runtime_state import JobRecord, RuntimeStateStore, TERMINAL_STATES
from tools.domed.executor import ExecutionEvent, ExecutionRequest
from tools.domed.executors.local_process import LocalProcessExecutor
from tools.domed.provenance import collect_runtime_provenance

_GENERATED_ROOT = Path(__file__).resolve().parents[2] / "generated" / "python"
_ROOT = Path(__file__).resolve().parents[2]
_TOOL_REGISTRY = _ROOT / "ssot" / "domed" / "tool_registry.v1.json"
_TOOLS_ROOT = _ROOT / "ssot" / "tools"
if str(_GENERATED_ROOT) not in sys.path:
    sys.path.insert(0, str(_GENERATED_ROOT))

from domed.v1 import domed_pb2, domed_pb2_grpc  # type: ignore  # noqa: E402


def _now_iso() -> str:
    return f"{time():.6f}"


def _status_ok(message: str = "ok") -> Any:
    return domed_pb2.RpcStatus(
        ok=True,
        code=domed_pb2.ERROR_CODE_UNSPECIFIED,
        message=message,
        retryable=False,
    )


def _status_err(code: int, message: str, retryable: bool = False) -> Any:
    return domed_pb2.RpcStatus(ok=False, code=code, message=message, retryable=retryable)


def _job_state_to_proto(state: str) -> int:
    mapping = {
        "queued": domed_pb2.JOB_STATE_QUEUED,
        "running": domed_pb2.JOB_STATE_RUNNING,
        "succeeded": domed_pb2.JOB_STATE_SUCCEEDED,
        "failed": domed_pb2.JOB_STATE_FAILED,
        "canceled": domed_pb2.JOB_STATE_CANCELED,
    }
    return mapping.get(state, domed_pb2.JOB_STATE_UNSPECIFIED)


def _event_type_to_proto(event_type: str) -> int:
    mapping = {
        "state_change": domed_pb2.EVENT_TYPE_STATE_CHANGE,
        "log": domed_pb2.EVENT_TYPE_LOG,
        "guard": domed_pb2.EVENT_TYPE_GUARD,
        "error": domed_pb2.EVENT_TYPE_ERROR,
    }
    return mapping.get(event_type, domed_pb2.EVENT_TYPE_UNSPECIFIED)


def _request_hash(req: Any) -> str:
    payload = {
        "skill_id": req.skill_id,
        "profile": req.profile,
        "task_json": req.task_json,
        "constraints_json": req.constraints_json,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _hash_json_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _normalize_tool_item(item: dict[str, Any]) -> dict[str, Any]:
    description = str(item.get("description", ""))
    permissions = item.get("permissions", [])
    if not isinstance(permissions, list):
        permissions = []
    side_effects = item.get("side_effects", [])
    if not isinstance(side_effects, list):
        side_effects = []
    entrypoint = item.get("entrypoint", [])
    if not isinstance(entrypoint, list):
        entrypoint = []
    timeout_seconds = item.get("timeout_seconds", 120)
    try:
        timeout_seconds = int(timeout_seconds)
    except Exception:
        timeout_seconds = 120
    env_allowlist = item.get("env_allowlist", [])
    if not isinstance(env_allowlist, list):
        env_allowlist = []
    return {
        "tool_id": str(item.get("tool_id", "")),
        "version": str(item.get("version", "v1")),
        "title": str(item.get("title", item.get("tool_id", ""))),
        "description": description,
        "short_description": str(item.get("short_description", description)),
        "kind": str(item.get("kind", "skill")),
        "input_schema_ref": str(item.get("input_schema_ref", "")),
        "output_schema_ref": str(item.get("output_schema_ref", "")),
        "executor_backend": str(item.get("executor_backend", "unknown")),
        "permissions": [str(x) for x in permissions],
        "side_effects": [str(x) for x in side_effects],
        "entrypoint": [str(x) for x in entrypoint if str(x).strip()],
        "timeout_seconds": max(timeout_seconds, 1),
        "env_allowlist": [str(x) for x in env_allowlist],
    }


def _load_tool_manifests() -> list[dict[str, Any]]:
    if not _TOOLS_ROOT.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(_TOOLS_ROOT.glob("*/manifest.yaml")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        out.append(_normalize_tool_item(payload))
    return [item for item in out if item["tool_id"]]


def _load_tool_registry() -> list[dict[str, Any]]:
    manifests = _load_tool_manifests()
    if manifests:
        return manifests
    payload = json.loads(_TOOL_REGISTRY.read_text(encoding="utf-8"))
    tools = payload.get("tools", [])
    out: list[dict[str, Any]] = []
    for item in tools:
        if isinstance(item, dict):
            out.append(_normalize_tool_item(item))
    return out


def _find_tool(tool_id: str) -> dict[str, Any] | None:
    target = tool_id.strip()
    for item in _load_tool_registry():
        if item["tool_id"] == target:
            return item
    return None


def _build_provenance(job: JobRecord) -> dict[str, Any]:
    tool = _find_tool(job.skill_id) or {
        "executor_backend": "unknown",
        "tool_id": job.skill_id,
        "version": "unknown",
    }
    manifest_hash = _hash_json_payload(
        {
            "tool_id": tool.get("tool_id"),
            "version": tool.get("version"),
            "executor_backend": tool.get("executor_backend"),
            "entrypoint": tool.get("entrypoint", []),
            "input_schema_ref": tool.get("input_schema_ref", ""),
            "output_schema_ref": tool.get("output_schema_ref", ""),
        }
    )
    return collect_runtime_provenance(
        _ROOT,
        executor_backend=str(tool.get("executor_backend", "unknown")),
        manifest_hash=manifest_hash,
    )


class InMemoryDomedService(domed_pb2_grpc.DomedServiceServicer):
    def __init__(self, store: RuntimeStateStore | None = None) -> None:
        self.store = store or RuntimeStateStore()
        self.local_executor = LocalProcessExecutor()

    def Health(self, request: Any, context: Any) -> Any:  # noqa: N802
        return domed_pb2.HealthResponse(
            status=_status_ok(),
            ts=_now_iso(),
            daemon_version="domed-mvp-m3",
        )

    def ListCapabilities(self, request: Any, context: Any) -> Any:  # noqa: N802
        tools = _load_tool_registry()
        cap = domed_pb2.Capability(
            name="skill-execute",
            version="v1",
            schema_version="v1",
            feature_flags=[f"tool_count:{len(tools)}", "inmemory", "stream-events"],
        )
        return domed_pb2.ListCapabilitiesResponse(
            status=_status_ok(),
            server_version="v1",
            api_versions=["domed.v1"],
            capabilities=[cap],
        )

    def ListTools(self, request: Any, context: Any) -> Any:  # noqa: N802
        tools = [
            domed_pb2.ToolSummary(
                tool_id=item["tool_id"],
                version=item["version"],
                title=item["title"],
                short_description=item["short_description"],
                kind=item["kind"],
            )
            for item in _load_tool_registry()
        ]
        return domed_pb2.ListToolsResponse(status=_status_ok(), tools=tools)

    def GetTool(self, request: Any, context: Any) -> Any:  # noqa: N802
        target = request.tool_id.strip()
        for item in _load_tool_registry():
            if item["tool_id"] == target:
                return domed_pb2.GetToolResponse(
                    status=_status_ok(),
                    tool=domed_pb2.ToolDescriptor(
                        tool_id=item["tool_id"],
                        version=item["version"],
                        title=item["title"],
                        description=item["description"],
                        short_description=item["short_description"],
                        kind=item["kind"],
                        input_schema_ref=item["input_schema_ref"],
                        output_schema_ref=item["output_schema_ref"],
                        executor_backend=item["executor_backend"],
                        permissions=item["permissions"],
                        side_effects=item["side_effects"],
                    ),
                )
        return domed_pb2.GetToolResponse(
            status=_status_err(domed_pb2.E_NOT_FOUND, f"tool not found: {target}"),
            tool=domed_pb2.ToolDescriptor(),
        )

    def SkillExecute(self, request: Any, context: Any) -> Any:  # noqa: N802
        if not request.skill_id or not request.profile or not request.idempotency_key:
            return domed_pb2.SkillExecuteResponse(
                status=_status_err(domed_pb2.E_INVALID_REQUEST, "missing required request fields"),
                state=domed_pb2.JOB_STATE_UNSPECIFIED,
            )
        tool = _find_tool(request.skill_id)
        if tool is None:
            return domed_pb2.SkillExecuteResponse(
                status=_status_err(domed_pb2.E_NOT_FOUND, f"tool not found: {request.skill_id}"),
                state=domed_pb2.JOB_STATE_UNSPECIFIED,
            )

        run_id = f"run-{uuid4().hex[:12]}"
        job_id = f"job-{uuid4().hex[:12]}"
        job = JobRecord(
            job_id=job_id,
            run_id=run_id,
            state="queued",
            skill_id=request.skill_id,
            profile=request.profile,
            idempotency_key=request.idempotency_key,
            request_hash=_request_hash(request),
        )
        try:
            stored, replay = self.store.submit(job=job)
        except ValueError as exc:
            return domed_pb2.SkillExecuteResponse(
                status=_status_err(domed_pb2.E_IDEMPOTENCY_KEY_REUSED, str(exc)),
                state=domed_pb2.JOB_STATE_UNSPECIFIED,
            )

        if not replay:
            self.store.append_event(
                job_id=stored.job_id,
                event_type="state_change",
                payload={"from": "unspecified", "to": "queued"},
            )
            self._execute_job(stored.job_id, tool, request.task_json, request.constraints_json)

        return domed_pb2.SkillExecuteResponse(
            status=_status_ok("replayed" if replay else "submitted"),
            run_id=stored.run_id,
            job_id=stored.job_id,
            state=_job_state_to_proto(stored.state),
            artifacts=[],
        )

    def _execute_job(
        self,
        job_id: str,
        tool: dict[str, Any],
        task_json: str,
        constraints_json: str,
    ) -> None:
        try:
            task = json.loads(task_json) if task_json else {}
            if not isinstance(task, dict):
                task = {}
        except Exception:
            task = {}
        try:
            constraints = json.loads(constraints_json) if constraints_json else {}
            if not isinstance(constraints, dict):
                constraints = {}
        except Exception:
            constraints = {}

        skill_id = tool["tool_id"]
        job = self.store.get(job_id)
        run_id = job.run_id if job is not None else ""
        profile = job.profile if job is not None else ""

        self.store.transition(job_id=job_id, to_state="running")
        self.store.append_event(
            job_id=job_id,
            event_type="state_change",
            payload={
                "from": "queued",
                "to": "running",
                "tool_id": tool["tool_id"],
                "tool_version": tool["version"],
                "executor_backend": tool["executor_backend"],
            },
        )

        if tool["executor_backend"] == "local-process":
            req = ExecutionRequest(
                run_id=run_id,
                job_id=job_id,
                tool_id=tool["tool_id"],
                profile=profile,
                task=task,
                constraints=constraints,
                entrypoint=list(tool.get("entrypoint", [])),
                cwd=_ROOT,
                timeout_seconds=int(tool.get("timeout_seconds", 120)),
                env_allowlist=list(tool.get("env_allowlist", [])),
            )

            def _sink(evt: ExecutionEvent) -> None:
                if evt.kind == "error":
                    self.store.append_event(job_id=job_id, event_type="error", payload=evt.payload)
                    return
                self.store.append_event(job_id=job_id, event_type="log", payload=evt.payload)

            result = self.local_executor.execute(req, _sink)
            self.store.transition(job_id=job_id, to_state=result.terminal_state)
            self.store.append_event(
                job_id=job_id,
                event_type="state_change",
                payload={
                    "from": "running",
                    "to": result.terminal_state,
                    "tool_id": tool["tool_id"],
                    "exit_code": result.exit_code,
                    "message": result.message,
                },
            )
            return

        if skill_id in {"skill-execute", "job.noop"}:
            self.store.transition(job_id=job_id, to_state="succeeded")
            self.store.append_event(
                job_id=job_id,
                event_type="state_change",
                payload={
                    "from": "running",
                    "to": "succeeded",
                    "job_type": "noop",
                    "tool_id": tool["tool_id"],
                    "exit_code": 0,
                },
            )
            return

        if skill_id == "job.log":
            lines = task.get("lines", [])
            if not isinstance(lines, list):
                lines = [str(lines)]
            for line in lines[:100]:
                self.store.append_event(
                    job_id=job_id,
                    event_type="log",
                    payload={"line": str(line)},
                )
            self.store.transition(job_id=job_id, to_state="succeeded")
            self.store.append_event(
                job_id=job_id,
                event_type="state_change",
                payload={
                    "from": "running",
                    "to": "succeeded",
                    "job_type": "log",
                    "tool_id": tool["tool_id"],
                    "exit_code": 0,
                },
            )
            return

        if skill_id == "job.fail":
            reason = str(task.get("reason", "simulated failure"))
            self.store.append_event(
                job_id=job_id,
                event_type="error",
                payload={"reason": reason},
            )
            self.store.transition(job_id=job_id, to_state="failed")
            self.store.append_event(
                job_id=job_id,
                event_type="state_change",
                payload={
                    "from": "running",
                    "to": "failed",
                    "job_type": "fail",
                    "tool_id": tool["tool_id"],
                    "exit_code": 1,
                },
            )
            return

        self.store.append_event(
            job_id=job_id,
            event_type="error",
            payload={
                "reason": f"unsupported skill_id: {skill_id}",
                "tool_id": tool["tool_id"],
                "executor_backend": tool["executor_backend"],
            },
        )
        self.store.transition(job_id=job_id, to_state="failed")
        self.store.append_event(
            job_id=job_id,
            event_type="state_change",
            payload={
                "from": "running",
                "to": "failed",
                "job_type": "unsupported",
                "tool_id": tool["tool_id"],
                "exit_code": 2,
            },
        )

    def GetJobStatus(self, request: Any, context: Any) -> Any:  # noqa: N802
        job = self.store.get(request.job_id)
        if job is None:
            return domed_pb2.GetJobStatusResponse(
                status=_status_err(domed_pb2.E_NOT_FOUND, f"job not found: {request.job_id}"),
                state=domed_pb2.JOB_STATE_UNSPECIFIED,
            )
        prov = _build_provenance(job)
        return domed_pb2.GetJobStatusResponse(
            status=_status_ok(),
            run_id=job.run_id,
            job_id=job.job_id,
            state=_job_state_to_proto(job.state),
            artifacts=[],
            provenance=domed_pb2.RunProvenance(
                repo=prov["repo"],
                commit_sha=prov["commit_sha"],
                dirty_flag=bool(prov["dirty_flag"]),
                contract_hashes_json=prov["contract_hashes_json"],
                tool_versions_json=prov["tool_versions_json"],
                input_hash=job.request_hash,
                env_fingerprint=prov["env_fingerprint"],
            ),
        )

    def CancelJob(self, request: Any, context: Any) -> Any:  # noqa: N802
        job = self.store.get(request.job_id)
        if job is None:
            return domed_pb2.CancelJobResponse(
                status=_status_err(domed_pb2.E_NOT_FOUND, f"job not found: {request.job_id}"),
                job_id=request.job_id,
                state=domed_pb2.JOB_STATE_UNSPECIFIED,
            )
        canceled = self.store.cancel(request.job_id)
        self.store.append_event(
            job_id=canceled.job_id,
            event_type="state_change",
            payload={"from": job.state, "to": canceled.state},
        )
        return domed_pb2.CancelJobResponse(
            status=_status_ok(),
            job_id=canceled.job_id,
            state=_job_state_to_proto(canceled.state),
        )

    def StreamJobEvents(self, request: Any, context: Any) -> Any:  # noqa: N802
        if self.store.get(request.job_id) is None:
            return
        cursor = int(request.since_seq)
        poll_interval = 0.05
        while True:
            job = self.store.get(request.job_id)
            if job is None:
                return
            events = self.store.events_since(job_id=request.job_id, since_seq=cursor)
            for evt in events:
                cursor = evt.seq
                yield domed_pb2.StreamJobEventsResponse(
                    seq=evt.seq,
                    event_id=f"{request.job_id}-{evt.seq}",
                    ts=f"{evt.ts_epoch:.6f}",
                    run_id=job.run_id or "",
                    job_id=request.job_id,
                    event_type=_event_type_to_proto(evt.event_type),
                    payload_json=json.dumps(evt.payload, sort_keys=True),
                )
            if not request.follow:
                return
            if job.state in TERMINAL_STATES and not events:
                return
            if hasattr(context, "is_active") and not context.is_active():
                return
            sleep(poll_interval)

    def GetGateDecision(self, request: Any, context: Any) -> Any:  # noqa: N802
        return domed_pb2.GetGateDecisionResponse(
            status=_status_err(domed_pb2.E_NOT_FOUND, "gate decision unavailable in m3"),
            run_id=request.run_id,
            gate_decision_path="",
        )

    def GetPromotionDecision(self, request: Any, context: Any) -> Any:  # noqa: N802
        return domed_pb2.GetPromotionDecisionResponse(
            status=_status_err(domed_pb2.E_NOT_FOUND, "promotion decision unavailable in m3"),
            run_id=request.run_id,
            promotion_decision_path="",
        )


def start_insecure_server(
    bind: str = "127.0.0.1:0",
    service: InMemoryDomedService | None = None,
) -> tuple[grpc.Server, int, InMemoryDomedService]:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    service = service or InMemoryDomedService()
    domed_pb2_grpc.add_DomedServiceServicer_to_server(service, server)
    port = server.add_insecure_port(bind)
    server.start()
    return server, port, service
