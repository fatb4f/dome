from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("grpc")
pytest.importorskip("google.protobuf")

from tools.codex.domed_client import DomedClient, DomedClientConfig
from tools.domed.service import start_insecure_server


def test_get_job_status_populates_provenance_fields() -> None:
    server, port, _service = start_insecure_server()
    client = DomedClient(DomedClientConfig(endpoint=f"127.0.0.1:{port}"))
    try:
        submit = client.skill_execute(
            skill_id="domed.exec-probe",
            profile="work",
            idempotency_key="idem-prov-1",
            task={"stdout": ["x"], "exit_code": 0},
            constraints={},
        )
        status = client.get_job_status(submit.job_id)
        prov = status.provenance
        assert prov.repo == "dome"
        assert prov.commit_sha
        assert prov.contract_hashes_json
        assert prov.tool_versions_json
        assert prov.env_fingerprint

        tool_versions = json.loads(prov.tool_versions_json)
        assert "executor" in tool_versions
        assert "python" in tool_versions

        env = json.loads(prov.env_fingerprint)
        assert env.get("python")
        assert env.get("platform")
    finally:
        server.stop(grace=0).wait()

