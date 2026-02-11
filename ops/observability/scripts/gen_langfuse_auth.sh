#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Missing $ROOT/.env. Copy .env.example -> .env and fill keys." >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$ROOT/.env"

if [[ -z "${LANGFUSE_PUBLIC_KEY:-}" || -z "${LANGFUSE_SECRET_KEY:-}" ]]; then
  echo "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in $ROOT/.env" >&2
  exit 1
fi

AUTH="$(printf '%s:%s' "$LANGFUSE_PUBLIC_KEY" "$LANGFUSE_SECRET_KEY" | base64 | tr -d '\n')"

echo "LANGFUSE_AUTH=$AUTH"
echo
echo "Paste into ops/observability/.env as LANGFUSE_AUTH=..."
