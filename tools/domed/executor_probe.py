from __future__ import annotations

import json
import os
import sys


def main() -> int:
    raw = os.environ.get("DOMED_TASK_JSON", "{}")
    try:
        task = json.loads(raw)
    except Exception:
        task = {}
    if not isinstance(task, dict):
        task = {}

    for line in task.get("stdout", []) if isinstance(task.get("stdout"), list) else []:
        print(str(line), flush=True)
    for line in task.get("stderr", []) if isinstance(task.get("stderr"), list) else []:
        print(str(line), file=sys.stderr, flush=True)
    progress = task.get("progress")
    if isinstance(progress, list):
        for item in progress:
            print(f"PROGRESS:{item}", flush=True)
    exit_code = task.get("exit_code", 0)
    try:
        return int(exit_code)
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

