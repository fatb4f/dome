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
        cap = domed_pb2.Capability(
            name="skill-execute",
            version="v1",
            schema_version="v1",
            feature_flags=["inmemory", "stream-events"],
        )
        return domed_pb2.ListCapabilitiesResponse(
            status=_status_ok(),
            server_version="v1",
            api_versions=["domed.v1"],
            capabilities=[cap],
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

        return domed_pb2.SkillExecuteResponse(
            status=_status_ok("replayed" if replay else "submitted"),
            run_id=stored.run_id,
            job_id=stored.job_id,
            state=_job_state_to_proto(stored.state),
            artifacts=[],
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


def start_insecure_server(bind: str = "127.0.0.1:0") -> tuple[grpc.Server, int, InMemoryDomedService]:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    service = InMemoryDomedService()
    domed_pb2_grpc.add_DomedServiceServicer_to_server(service, server)
    port = server.add_insecure_port(bind)
    server.start()
    return server, port, service
