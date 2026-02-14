import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.ingest_pattern_catalog import ingest


def test_ingest_catalog_from_seed(tmp_path: Path) -> None:
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "repo": "nibzard/awesome-agentic-patterns",
                "patterns": [{"id": "p1", "name": "Pattern 1", "category": "loop", "source_url": "x"}],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "catalog.json"
    payload = ingest(seed, out)
    assert payload["patterns"][0]["id"] == "p1"
    assert out.exists()
