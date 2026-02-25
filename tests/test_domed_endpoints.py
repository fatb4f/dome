from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.domed import endpoints


def test_default_client_endpoint_env_override(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("DOMED_ENDPOINT", "127.0.0.1:55051")
    assert endpoints.default_client_endpoint() == "127.0.0.1:55051"


def test_default_client_endpoint_uds_then_tcp(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("DOMED_ENDPOINT", raising=False)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    sock = tmp_path / "dome" / "domed.sock"
    sock.parent.mkdir(parents=True, exist_ok=True)
    assert endpoints.default_client_endpoint() == "127.0.0.1:50051"
    sock.touch()
    assert endpoints.default_client_endpoint() == f"unix://{sock}"


def test_default_sqlite_path_xdg_state(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert endpoints.default_sqlite_path() == tmp_path / "dome" / "domed.sqlite"

