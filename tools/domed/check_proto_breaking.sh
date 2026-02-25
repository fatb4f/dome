#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

# Ensure the pinned codegen runtime is available before running compatibility checks.
"${SCRIPT_DIR}/gen.sh" >/dev/null

"${ROOT_DIR}/.venv-domed-codegen/bin/python" "${SCRIPT_DIR}/check_proto_breaking.py" "$@"

