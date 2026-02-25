#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from google.protobuf import descriptor_pb2


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout


def _compile_descriptor(pybin: str, proto_root: Path, proto_file: Path, out_file: Path) -> descriptor_pb2.FileDescriptorSet:
    cmd = [
        pybin,
        "-m",
        "grpc_tools.protoc",
        "-I",
        str(proto_root),
        "--descriptor_set_out",
        str(out_file),
        "--include_imports",
        str(proto_file),
    ]
    _run(cmd)
    ds = descriptor_pb2.FileDescriptorSet()
    ds.ParseFromString(out_file.read_bytes())
    return ds


def _service_map(ds: descriptor_pb2.FileDescriptorSet) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for f in ds.file:
        pkg = f.package
        for svc in f.service:
            name = f"{pkg}.{svc.name}" if pkg else svc.name
            out[name] = {m.name for m in svc.method}
    return out


def _enum_map(ds: descriptor_pb2.FileDescriptorSet) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}

    def walk(prefix: str, enums: list[descriptor_pb2.EnumDescriptorProto], msgs: list[descriptor_pb2.DescriptorProto]) -> None:
        for e in enums:
            name = f"{prefix}.{e.name}" if prefix else e.name
            out[name] = {v.name for v in e.value}
        for m in msgs:
            mname = f"{prefix}.{m.name}" if prefix else m.name
            walk(mname, list(m.enum_type), list(m.nested_type))

    for f in ds.file:
        walk(f.package, list(f.enum_type), list(f.message_type))
    return out


def _message_fields(ds: descriptor_pb2.FileDescriptorSet) -> dict[str, dict[int, tuple[str, int, int]]]:
    out: dict[str, dict[int, tuple[str, int, int]]] = {}

    def walk(prefix: str, msgs: list[descriptor_pb2.DescriptorProto]) -> None:
        for m in msgs:
            mname = f"{prefix}.{m.name}" if prefix else m.name
            out[mname] = {f.number: (f.name, f.type, f.label) for f in m.field}
            walk(mname, list(m.nested_type))

    for f in ds.file:
        walk(f.package, list(f.message_type))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check domed proto breaking changes against base ref")
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--proto", default="proto/domed/v1/domed.proto")
    ap.add_argument("--python", default=".venv-domed-codegen/bin/python")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    proto_rel = Path(args.proto)
    current_proto = root / proto_rel
    if not current_proto.exists():
        raise SystemExit(f"missing current proto: {current_proto}")

    show = subprocess.run(
        ["git", "show", f"{args.base_ref}:{proto_rel.as_posix()}"],
        cwd=str(root),
        text=True,
        capture_output=True,
        check=False,
    )
    if show.returncode != 0:
        print(f"proto baseline not found at {args.base_ref}:{proto_rel}; skipping breaking check")
        return 0

    pybin = str((root / args.python).resolve())
    if not Path(pybin).exists():
        raise SystemExit(f"missing python runtime: {pybin} (run tools/domed/gen.sh first)")

    with tempfile.TemporaryDirectory(prefix="domed-proto-break-") as td:
        tdir = Path(td)
        base_root = tdir / "base" / "proto" / "domed" / "v1"
        base_root.mkdir(parents=True, exist_ok=True)
        base_proto = base_root / "domed.proto"
        base_proto.write_text(show.stdout, encoding="utf-8")

        cur_desc = tdir / "cur.pb"
        base_desc = tdir / "base.pb"
        cur_ds = _compile_descriptor(pybin, root / "proto", current_proto, cur_desc)
        base_ds = _compile_descriptor(pybin, tdir / "base" / "proto", base_proto, base_desc)

    errs: list[str] = []

    base_services = _service_map(base_ds)
    cur_services = _service_map(cur_ds)
    for svc, methods in base_services.items():
        if svc not in cur_services:
            errs.append(f"removed service: {svc}")
            continue
        missing = sorted(methods - cur_services[svc])
        if missing:
            errs.append(f"removed rpc methods from {svc}: {missing}")

    base_enums = _enum_map(base_ds)
    cur_enums = _enum_map(cur_ds)
    for ename, vals in base_enums.items():
        if ename not in cur_enums:
            errs.append(f"removed enum: {ename}")
            continue
        missing_vals = sorted(vals - cur_enums[ename])
        if missing_vals:
            errs.append(f"removed enum values from {ename}: {missing_vals}")

    base_msgs = _message_fields(base_ds)
    cur_msgs = _message_fields(cur_ds)
    for mname, fields in base_msgs.items():
        if mname not in cur_msgs:
            errs.append(f"removed message: {mname}")
            continue
        cur_fields = cur_msgs[mname]
        for num, (fname, ftype, flabel) in fields.items():
            if num not in cur_fields:
                errs.append(f"removed field {mname}.{fname}#{num}")
                continue
            cname, ctype, clabel = cur_fields[num]
            if ctype != ftype or clabel != flabel:
                errs.append(
                    f"changed field type/label {mname}.{fname}#{num}: "
                    f"was(type={ftype},label={flabel}) now(type={ctype},label={clabel})"
                )
            if cname != fname:
                errs.append(f"renamed field {mname}#{num}: {fname} -> {cname}")

    if errs:
        print("breaking proto changes detected:")
        for e in errs:
            print(f"- {e}")
        return 1

    print("domed proto breaking check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
