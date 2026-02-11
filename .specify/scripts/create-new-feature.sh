#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/common.sh"

NAME="${1:-}"
[[ -n "$NAME" ]] || die "Usage: create-new-feature.sh <feature-name>"

ROOT="$(repo_root)"
SPECS_DIR="$ROOT/.specify/specs"
TEMPLATES_DIR="$ROOT/.specify/templates"
[[ -d "$SPECS_DIR" ]] || die "Missing $SPECS_DIR"

# Determine next numeric prefix
LAST="$(ls -1 "$SPECS_DIR" 2>/dev/null | cut -d- -f1 | sort -n | tail -n 1 || true)"
if [[ -z "$LAST" ]]; then
  NEXT="001"
else
  NEXT="$(printf "%03d" $((10#$LAST + 1)))"
fi

SAFE_NAME="$(echo "$NAME" | tr ' ' '-' | tr -cd '[:alnum:]-_')"
FEATURE_DIR="$SPECS_DIR/${NEXT}-${SAFE_NAME}"
mkdir -p "$FEATURE_DIR"

cp "$TEMPLATES_DIR/spec-template.md"  "$FEATURE_DIR/spec.md"
cp "$TEMPLATES_DIR/plan-template.md"  "$FEATURE_DIR/plan.md"
cp "$TEMPLATES_DIR/tasks-template.md" "$FEATURE_DIR/tasks.md"

echo "Created: $FEATURE_DIR"
