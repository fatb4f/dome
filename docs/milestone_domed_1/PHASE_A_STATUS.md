# Phase A Status

Phase A (`#73`) implementation status: **completed**.

## Delivered

- User service unit (authoritative path): `deploy/systemd/user/domed.service`
- Installer/uninstaller helpers:
  - `scripts/install_domed_user_service.sh`
  - `scripts/uninstall_domed_user_service.sh`
- Just targets:
  - `domed-install-user-service`
  - `domed-uninstall-user-service`
  - `domed-status`
- XDG + UDS defaults:
  - socket: `${XDG_RUNTIME_DIR}/dome/domed.sock`
  - sqlite: `${XDG_STATE_HOME:-~/.local/state}/dome/domed.sqlite`
- Client endpoint detection:
  1. `DOMED_ENDPOINT` override
  2. UDS default if socket exists
  3. TCP fallback `127.0.0.1:50051`

## Verification

- `systemctl --user restart domed.service` succeeds
- `tools/domed/operator_healthcheck.py` succeeds without explicit endpoint
- Runtime endpoint resolves to UDS by default when socket exists
