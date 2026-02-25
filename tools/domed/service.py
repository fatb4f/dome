from __future__ import annotations

from concurrent import futures
import hashlib
import json
from pathlib import Path
import sys
from time import time
from typing import Any
from uuid import uuid4

import grpc  # type: ignore

from tools.domed.runtime_state import JobRecord, RuntimeStateStore

_GENERATED_ROOT = Path(__file__).resolve().parents[2] / "generated" / "python"
_ROOT = Path(__file__).resolve().parents[2]
_TOOL_REGISTRY = _ROOT / "ssot" / "domed" / "tool_registry.v1.json"
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


def _load_tool_registry() -> list[dict[str, Any]]:
    payload = json.loads(_TOOL_REGISTRY.read_text(encoding="utf-8"))
    tools = payload.get("tools", [])
    out: list[dict[str, Any]] = []
    for item in tools:
        description = str(item.get("description", ""))
        permissions = item.get("permissions", [])
        if not isinstance(permissions, list):
            permissions = []
        side_effects = item.get("side_effects", [])
        if not isinstance(side_effects, list):
            side_effects = []
        out.append(
            {
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
            }
        )
    return out


class InMemoryDomedService(domed_pb2_grpc.DomedServiceServicer):
    def __init__(self, store: RuntimeStateStore | None = None) -> None:
        self.store = store or RuntimeStateStore()

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
            self._execute_job(stored.job_id, request.skill_id, request.task_json)

        return domed_pb2.SkillExecuteResponse(
            status=_status_ok("replayed" if replay else "submitted"),
            run_id=stored.run_id,
            job_id=stored.job_id,
            state=_job_state_to_proto(stored.state),
            artifacts=[],
        )

    def _execute_job(self, job_id: str, skill_id: str, task_json: str) -> None:
        try:
            task = json.loads(task_json) if task_json else {}
            if not isinstance(task, dict):
                task = {}
        except Exception:
            task = {}

        self.store.transition(job_id=job_id, to_state="running")
        self.store.append_event(
            job_id=job_id,
            event_type="state_change",
            payload={"from": "queued", "to": "running"},
        )

        if skill_id in {"skill-execute", "job.noop"}:
            self.store.transition(job_id=job_id, to_state="succeeded")
            self.store.append_event(
                job_id=job_id,
                event_type="state_change",
                payload={"from": "running", "to": "succeeded", "job_type": "noop"},
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
                payload={"from": "running", "to": "succeeded", "job_type": "log"},
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
                payload={"from": "running", "to": "failed", "job_type": "fail"},
            )
            return

        self.store.append_event(
            job_id=job_id,
            event_type="error",
            payload={"reason": f"unsupported skill_id: {skill_id}"},
        )
        self.store.transition(job_id=job_id, to_state="failed")
        self.store.append_event(
            job_id=job_id,
            event_type="state_change",
            payload={"from": "running", "to": "failed", "job_type": "unsupported"},
        )

    def GetJobStatus(self, request: Any, context: Any) -> Any:  # noqa: N802
        job = self.store.get(request.job_id)
        if job is None:
            return domed_pb2.GetJobStatusResponse(
                status=_status_err(domed_pb2.E_NOT_FOUND, f"job not found: {request.job_id}"),
                state=domed_pb2.JOB_STATE_UNSPECIFIED,
            )
        return domed_pb2.GetJobStatusResponse(
            status=_status_ok(),
            run_id=job.run_id,
            job_id=job.job_id,
            state=_job_state_to_proto(job.state),
            artifacts=[],
            provenance=domed_pb2.RunProvenance(
                repo="dome",
                commit_sha="unknown",
                dirty_flag=False,
                contract_hashes_json="{}",
                tool_versions_json="{}",
                input_hash=job.request_hash,
                env_fingerprint="inmemory",
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
        for evt in self.store.events_since(job_id=request.job_id, since_seq=request.since_seq):
            yield domed_pb2.StreamJobEventsResponse(
                seq=evt.seq,
                event_id=f"{request.job_id}-{evt.seq}",
                ts=f"{evt.ts_epoch:.6f}",
                run_id=self.store.get(request.job_id).run_id or "",
                job_id=request.job_id,
                event_type=_event_type_to_proto(evt.event_type),
                payload_json=json.dumps(evt.payload, sort_keys=True),
            )

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
