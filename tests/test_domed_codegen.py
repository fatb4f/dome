from __future__ import annotations

from pathlib import Path


def test_generated_domed_stubs_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    pb2 = root / "generated/python/domed/v1/domed_pb2.py"
    pb2_grpc = root / "generated/python/domed/v1/domed_pb2_grpc.py"
    assert pb2.exists(), f"missing generated stub: {pb2}"
    assert pb2_grpc.exists(), f"missing generated stub: {pb2_grpc}"


def test_generated_service_symbol_present() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "generated/python/domed/v1/domed_pb2_grpc.py").read_text(encoding="utf-8")
    assert "class DomedServiceStub" in text
    assert "add_DomedServiceServicer_to_server" in text

