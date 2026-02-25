#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-domed-codegen"
REQ_FILE="${SCRIPT_DIR}/requirements-codegen.txt"
PROTO_FILE="${ROOT_DIR}/proto/domed/v1/domed.proto"
OUT_DIR="${ROOT_DIR}/generated/python"
DESC_DIR="${ROOT_DIR}/generated/descriptors"
DESC_FILE="${DESC_DIR}/domed_v1.pb"
MANIFEST_FILE="${ROOT_DIR}/generated/codegen_manifest.json"

PY_BIN="${CODEGEN_PYTHON:-python3}"

if [[ ! -f "${PROTO_FILE}" ]]; then
  echo "error: proto file missing: ${PROTO_FILE}" >&2
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PY_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip >/dev/null
"${VENV_DIR}/bin/python" -m pip install -r "${REQ_FILE}" >/dev/null

mkdir -p "${OUT_DIR}" "${DESC_DIR}"
rm -rf "${OUT_DIR}/domed" "${DESC_FILE}"

"${VENV_DIR}/bin/python" -m grpc_tools.protoc \
  -I "${ROOT_DIR}/proto" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  --descriptor_set_out="${DESC_FILE}" \
  --include_imports \
  "${PROTO_FILE}"

mkdir -p "${OUT_DIR}/domed" "${OUT_DIR}/domed/v1"
: > "${OUT_DIR}/__init__.py"
: > "${OUT_DIR}/domed/__init__.py"
: > "${OUT_DIR}/domed/v1/__init__.py"

PROTO_SHA="$("${VENV_DIR}/bin/python" - <<'PY' "${PROTO_FILE}"
import hashlib, pathlib, sys
p=pathlib.Path(sys.argv[1])
h=hashlib.sha256(p.read_bytes()).hexdigest()
print(h)
PY
)"

GRPC_TOOLS_VER="$("${VENV_DIR}/bin/python" - <<'PY'
import importlib.metadata as m
print(m.version("grpcio-tools"))
PY
)"

PROTOBUF_VER="$("${VENV_DIR}/bin/python" - <<'PY'
import importlib.metadata as m
print(m.version("protobuf"))
PY
)"

cat > "${MANIFEST_FILE}" <<EOF
{
  "contract_set": "domed.v1",
  "proto_file": "proto/domed/v1/domed.proto",
  "proto_sha256": "${PROTO_SHA}",
  "grpcio_tools_version": "${GRPC_TOOLS_VER}",
  "protobuf_version": "${PROTOBUF_VER}",
  "generated": {
    "python_root": "generated/python",
    "descriptor": "generated/descriptors/domed_v1.pb"
  }
}
EOF

echo "generated domed proto artifacts"
