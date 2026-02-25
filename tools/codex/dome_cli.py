from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.codex.browse_skill import (
    run_task_via_domed,
    validate_codex_browse_contract,
    validate_identity_graph_contracts,
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DOME codex-skill bridge")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate-contracts", help="Validate codex-browse and identity-graph contract pins")
    v.add_argument("--codex-browse-root", type=Path, required=True)
    v.add_argument("--identity-graph-root", type=Path, required=True)

    r = sub.add_parser("run-skill", help="Run a codex-browse skill task via DOME wrapper")
    r.add_argument("--task-json", type=Path, required=True)
    r.add_argument("--domed-endpoint")
    r.add_argument("--profile", default="work")
    r.add_argument("--idempotency-key", default="dome-cli")

    lt = sub.add_parser("list-tools", help="List discoverable domed tools")
    lt.add_argument("--domed-endpoint")

    gt = sub.add_parser("get-tool", help="Get full descriptor for one domed tool")
    gt.add_argument("--tool-id", required=True)
    gt.add_argument("--domed-endpoint")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    if args.cmd == "validate-contracts":
        validate_codex_browse_contract(args.codex_browse_root)
        validate_identity_graph_contracts(args.identity_graph_root)
        print("dome codex-browse contract validation ok")
        return 0
    if args.cmd == "run-skill":
        task = json.loads(args.task_json.read_text(encoding="utf-8"))
        result = run_task_via_domed(
            task=task,
            domed_endpoint=args.domed_endpoint,
            profile=args.profile,
            idempotency_key=args.idempotency_key,
        )
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        print()
        return 0
    if args.cmd == "list-tools":
        from tools.codex.domed_client import DomedClient, DomedClientConfig

        client = DomedClient(DomedClientConfig(endpoint=args.domed_endpoint))
        resp = client.list_tools()
        out = []
        for item in resp.tools:
            out.append(
                {
                    "tool_id": item.tool_id,
                    "version": item.version,
                    "title": item.title,
                    "short_description": item.short_description,
                    "kind": item.kind,
                }
            )
        json.dump({"ok": bool(resp.status.ok), "tools": out}, sys.stdout, indent=2, sort_keys=True)
        print()
        return 0
    if args.cmd == "get-tool":
        from tools.codex.domed_client import DomedClient, DomedClientConfig

        client = DomedClient(DomedClientConfig(endpoint=args.domed_endpoint))
        resp = client.get_tool(args.tool_id)
        out = {
            "ok": bool(resp.status.ok),
            "tool": {
                "tool_id": resp.tool.tool_id,
                "version": resp.tool.version,
                "title": resp.tool.title,
                "description": resp.tool.description,
                "short_description": resp.tool.short_description,
                "kind": resp.tool.kind,
                "input_schema_ref": resp.tool.input_schema_ref,
                "output_schema_ref": resp.tool.output_schema_ref,
                "executor_backend": resp.tool.executor_backend,
                "permissions": list(resp.tool.permissions),
                "side_effects": list(resp.tool.side_effects),
            },
            "status": {"code": int(resp.status.code), "message": resp.status.message},
        }
        json.dump(out, sys.stdout, indent=2, sort_keys=True)
        print()
        return 0
    raise RuntimeError(f"unsupported command {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
