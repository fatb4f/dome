# XA-10 Pattern Catalog Ingestion

Pipeline:
- seed input: `ssot/sources/awesome_agentic_patterns.seed.json`
- ingestion tool: `tools/orchestrator/ingest_pattern_catalog.py`
- output catalog: `ssot/catalog/pattern.catalog.v1.json`

The ingested catalog records source repo and commit for provenance.
