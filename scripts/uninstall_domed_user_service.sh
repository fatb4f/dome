#!/usr/bin/env bash
set -euo pipefail

UNIT_DST="${HOME}/.config/systemd/user/domed.service"

systemctl --user disable --now domed.service >/dev/null 2>&1 || true
rm -f "${UNIT_DST}"
systemctl --user daemon-reload

echo "domed user service removed"

