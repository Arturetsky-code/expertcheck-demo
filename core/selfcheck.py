from __future__ import annotations
from pathlib import Path

REQUIRED_ROOT = [
    "app.py", "analyzer.py", "legacy_analyzer.py", "requirements.txt",
    "core", "knowledge", "parameters.json", "objects.json",
    "document_types.json", "engineering_rules.json",
]
REQUIRED_CORE = [
    "__init__.py", "pipeline.py", "catalogs.py", "confidence.py",
    "rule_engine.py", "semantic_engine.py", "table_engine.py",
]

def deployment_status(root: str | Path) -> dict:
    root = Path(root)
    missing_root = [name for name in REQUIRED_ROOT if not (root / name).exists()]
    missing_core = [name for name in REQUIRED_CORE if not (root / "core" / name).exists()]
    return {
        "ok": not missing_root and not missing_core,
        "missing_root": missing_root,
        "missing_core": missing_core,
        "root": str(root),
    }
