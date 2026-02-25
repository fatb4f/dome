#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

"${SCRIPT_DIR}/gen.sh"

if ! git -C "${ROOT_DIR}" diff --quiet -- generated/python generated/descriptors generated/codegen_manifest.json; then
  echo "error: domed generated code drift detected (run tools/domed/gen.sh and commit outputs)" >&2
  git -C "${ROOT_DIR}" --no-pager diff -- generated/python generated/descriptors generated/codegen_manifest.json | sed -n '1,220p' >&2
  exit 1
fi

echo "domed codegen drift check passed"
