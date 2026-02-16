# High-Signal Event-Driven Monitoring Tools

## Recommended Core Stack

1. Falco (runtime threat detection; mature rules/plugins; strong signal when tuned)
2. Tetragon (eBPF runtime observability with optional enforcement)
3. Tracee (eBPF detections + runtime forensics)
4. osquery (high-value host event tables: process/file/yara events)
5. auditd (focused syscall/path watches for auth/privilege-sensitive controls)
6. Wazuh (broader SIEM-style correlation/response/compliance workflow)

## Package and Update Event Sources

- Arch Linux:
  - `pacman` hooks (`alpm-hooks`) for install/upgrade/remove completion events
  - `pacman.conf` `HookDir` for custom post-transaction emitters
- Debian/Ubuntu:
  - `unattended-upgrades` logs and service events
- Fedora/RHEL:
  - `dnf-automatic` timer/service results

## Suggested Watcher Topics

- `package.txn.completed`
- `package.txn.failed`
- `security.auth.failed`
- `security.sudo.denied`
- `security.kernel.audit.critical`
- `runtime.threat.detected`

## Candidate Profiles to Route

- `package_event_index` -> append transaction metadata + package list to JSONL
- `security_alert_notify` -> desktop notify and append alert record
- `threat_runtime_triage` -> collect process tree + command line + parent binary + cgroup

## Notes

- Start with a narrow, high-confidence ruleset and expand only with measured false-positive rates.
- Prefer deterministic event payload shapes (stable keys, required fields, timestamps in UTC).
- Keep package/security telemetry append-only in JSONL for replay and post-incident audit.
