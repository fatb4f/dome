from __future__ import annotations

import os
from pathlib import Path


def default_runtime_dir() -> Path:
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime:
        return Path(xdg_runtime)
    return Path(f"/run/user/{os.getuid()}")


def default_state_home() -> Path:
    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home)
    return Path.home() / ".local" / "state"


def default_uds_socket_path() -> Path:
    return default_runtime_dir() / "dome" / "domed.sock"


def default_sqlite_path() -> Path:
    return default_state_home() / "dome" / "domed.sqlite"


def default_client_endpoint() -> str:
    env = os.environ.get("DOMED_ENDPOINT")
    if env:
        return env
    sock = default_uds_socket_path()
    if sock.exists():
        return f"unix://{sock}"
    return "127.0.0.1:50051"


def default_server_bind() -> str:
    env = os.environ.get("DOMED_ENDPOINT")
    if env:
        return env
    return f"unix://{default_uds_socket_path()}"

