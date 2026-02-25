from __future__ import annotations

import argparse
from pathlib import Path
from threading import Event, Thread
import time

from tools.domed.endpoints import default_server_bind, default_sqlite_path
from tools.domed.service import InMemoryDomedService, start_insecure_server
from tools.domed.sqlite_state import SQLiteRuntimeStateStore


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="domed runtime daemon")
    p.add_argument("--bind", default=default_server_bind())
    p.add_argument("--db-path", default=str(default_sqlite_path()))
    p.add_argument("--ttl-seconds", type=int, default=86400)
    p.add_argument("--gc-interval-seconds", type=int, default=300)
    return p.parse_args()


def _gc_loop(stop_evt: Event, store: SQLiteRuntimeStateStore, ttl_seconds: int, interval_seconds: int) -> None:
    while not stop_evt.is_set():
        try:
            deleted = store.gc(ttl_seconds=ttl_seconds)
            if deleted:
                print(f"domed gc deleted_jobs={deleted}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"domed gc error: {exc}", flush=True)
        stop_evt.wait(timeout=interval_seconds)


def main() -> int:
    args = _parse_args()
    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    bind = str(args.bind)
    if bind.startswith("unix://"):
        sock_path = Path(bind[len("unix://") :])
        sock_path.parent.mkdir(parents=True, exist_ok=True)
        if sock_path.exists():
            sock_path.unlink()

    store = SQLiteRuntimeStateStore(str(db_path))
    service = InMemoryDomedService(store=store)
    server, port, _ = start_insecure_server(bind=bind, service=service)

    stop_evt = Event()
    gc_thread = Thread(
        target=_gc_loop,
        args=(stop_evt, store, args.ttl_seconds, args.gc_interval_seconds),
        daemon=True,
        name="domed-gc",
    )
    gc_thread.start()

    print(f"domed listening bind={bind} port={port} db={db_path}", flush=True)
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        stop_evt.set()
        server.stop(grace=2).wait()
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
