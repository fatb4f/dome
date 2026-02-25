from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any


@dataclass(slots=True)
class DomedClientConfig:
    endpoint: str


class DomedClient:
    """Thin client wrapper around generated domed gRPC stubs."""

    def __init__(self, cfg: DomedClientConfig) -> None:
        try:
            import grpc  # type: ignore
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("grpc dependency missing; install grpcio/protobuf to use DomedClient") from exc

        generated_root = Path(__file__).resolve().parents[2] / "generated" / "python"
        if str(generated_root) not in sys.path:
            sys.path.insert(0, str(generated_root))

        try:
            from domed.v1 import domed_pb2, domed_pb2_grpc
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("generated domed stubs unavailable; run tools/domed/gen.sh") from exc

        self._pb2 = domed_pb2
        self._channel = grpc.insecure_channel(cfg.endpoint)
        self._stub = domed_pb2_grpc.DomedServiceStub(self._channel)

    def health(self) -> Any:
        return self._stub.Health(self._pb2.HealthRequest())

    def list_capabilities(self, profile: str) -> Any:
        return self._stub.ListCapabilities(self._pb2.ListCapabilitiesRequest(profile=profile))

    def skill_execute(
        self,
        *,
        skill_id: str,
        profile: str,
        idempotency_key: str,
        task: dict[str, Any],
        constraints: dict[str, Any] | None = None,
    ) -> Any:
        return self._stub.SkillExecute(
            self._pb2.SkillExecuteRequest(
                skill_id=skill_id,
                profile=profile,
                idempotency_key=idempotency_key,
                task_json=json.dumps(task, sort_keys=True),
                constraints_json=json.dumps(constraints or {}, sort_keys=True),
            )
        )

    def get_job_status(self, job_id: str) -> Any:
        return self._stub.GetJobStatus(self._pb2.GetJobStatusRequest(job_id=job_id))

    def cancel_job(self, *, job_id: str, idempotency_key: str) -> Any:
        return self._stub.CancelJob(
            self._pb2.CancelJobRequest(job_id=job_id, idempotency_key=idempotency_key)
        )

    def stream_job_events(self, *, job_id: str, since_seq: int = 0, follow: bool = False) -> Any:
        req = self._pb2.StreamJobEventsRequest(job_id=job_id, since_seq=since_seq, follow=follow)
        return self._stub.StreamJobEvents(req)
