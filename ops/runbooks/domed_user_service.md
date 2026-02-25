# domed User Service

## Install

```bash
cd /home/src404/src/dome
bash scripts/install_domed_user_service.sh
```

This script:

- creates `~/.config/systemd/user/domed.service`
- installs unit template from `ops/systemd/user/domed.service`
- creates `.venv-domed`
- installs pinned runtime deps (`grpcio==1.76.0`, `protobuf==6.33.5`)
- enables and starts `domed.service`

## Operate

```bash
systemctl --user status domed.service
systemctl --user restart domed.service
journalctl --user -u domed.service -n 100 --no-pager
```

## Healthcheck

```bash
cd /home/src404/src/dome
python tools/domed/operator_healthcheck.py --profile work
```

Endpoint resolution order:

1. `DOMED_ENDPOINT` env override
2. UDS default: `${XDG_RUNTIME_DIR}/dome/domed.sock`
3. TCP fallback: `127.0.0.1:50051`
