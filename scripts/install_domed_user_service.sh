#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_SRC="${ROOT_DIR}/ops/systemd/user/domed.service"
UNIT_DST="${HOME}/.config/systemd/user/domed.service"
VENV_DIR="${ROOT_DIR}/.venv-domed"
PY_BIN="${PYTHON_BIN:-python3}"

mkdir -p "${HOME}/.config/systemd/user"
mkdir -p "${ROOT_DIR}/ops/runtime/domed"
mkdir -p "${HOME}/.local/state/dome"

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PY_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip >/dev/null
"${VENV_DIR}/bin/python" -m pip install grpcio==1.76.0 protobuf==6.33.5 >/dev/null

cp "${UNIT_SRC}" "${UNIT_DST}"
systemctl --user daemon-reload
systemctl --user enable domed.service >/dev/null
systemctl --user restart domed.service
systemctl --user --no-pager --full status domed.service | sed -n '1,80p'
