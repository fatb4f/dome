#!/usr/bin/env bash
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || pwd
}

json_escape() {
  python - <<'PY'
import json,sys
print(json.dumps(sys.stdin.read()))
PY
}
