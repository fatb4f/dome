#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/common.sh"

JSON=0
REQUIRE_TASKS=0
INCLUDE_TASKS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON=1; shift;;
    --require-tasks) REQUIRE_TASKS=1; shift;;
    --include-tasks) INCLUDE_TASKS=1; shift;;
    *) shift;;
  esac
done

ROOT="$(repo_root)"
SPECS_DIR="$ROOT/.specify/specs"

[[ -d "$SPECS_DIR" ]] || die "Missing .specify/specs directory"

if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
  FEATURE_DIR="$SPECS_DIR/$SPECIFY_FEATURE"
else
  PICK="$(ls -1 "$SPECS_DIR" 2>/dev/null | sort -r | head -n 1 || true)"
  [[ -n "$PICK" ]] || die "No feature directories found in .specify/specs"
  FEATURE_DIR="$SPECS_DIR/$PICK"
fi

[[ -d "$FEATURE_DIR" ]] || die "Feature directory not found: $FEATURE_DIR"

AVAILABLE_DOCS=()
for f in spec.md plan.md tasks.md; do
  [[ -f "$FEATURE_DIR/$f" ]] && AVAILABLE_DOCS+=("$f")
done

if [[ "$REQUIRE_TASKS" -eq 1 && ! -f "$FEATURE_DIR/tasks.md" ]]; then
  die "tasks.md is required but missing in $FEATURE_DIR"
fi

ABS_FEATURE_DIR="$(python -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$FEATURE_DIR")"

if [[ "$JSON" -eq 1 ]]; then
  python - "$ABS_FEATURE_DIR" "$INCLUDE_TASKS" "${AVAILABLE_DOCS[@]}" <<'PY'
import json, os, sys

feature_dir = sys.argv[1]
include_tasks = sys.argv[2] == "1"
docs = sys.argv[3:]

out = {"FEATURE_DIR": feature_dir, "AVAILABLE_DOCS": docs}
if include_tasks:
    tasks_path = os.path.join(feature_dir, "tasks.md")
    if os.path.exists(tasks_path):
        out["TASKS_PATH"] = tasks_path

print(json.dumps(out))
PY
  exit 0
fi

echo "FEATURE_DIR=$ABS_FEATURE_DIR"
echo "AVAILABLE_DOCS=${AVAILABLE_DOCS[*]}"
if [[ "$INCLUDE_TASKS" -eq 1 && -f "$FEATURE_DIR/tasks.md" ]]; then
  echo "TASKS_PATH=$ABS_FEATURE_DIR/tasks.md"
fi
