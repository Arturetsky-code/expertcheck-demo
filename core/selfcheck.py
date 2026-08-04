from __future__ import annotations
from pathlib import Path

REQUIRED_ROOT = [
    "app.py", "analyzer.py", "legacy_analyzer.py", "requirements.txt",
    "core", "knowledge", "parameters.json", "objects.json",
    "document_types.json", "engineering_rules.json",
]
REQUIRED_CORE = [
    "__init__.py", "pipeline.py",
        "xml_engine.py", "catalogs.py", "confidence.py",
    "rule_engine.py", "semantic_engine.py", "table_engine.py",
        "model_quality.py",
        "relations.py",
        "validation.py",
        "dem.py", "selfcheck.py",
]
REQUIRED_KNOWLEDGE = [
    "core/object_catalog.json", "core/parameter_catalog.json",
    "core/table_catalog.json", "core/rules.json",
]

def deployment_status(root: str | Path) -> dict:
    root = Path(root)
    missing_root = [name for name in REQUIRED_ROOT if not (root / name).exists()]
    missing_core = [name for name in REQUIRED_CORE if not (root / "core" / name).exists()]
    missing_knowledge = [name for name in REQUIRED_KNOWLEDGE if not (root / "knowledge" / name).exists()]
    return {
        "ok": not missing_root and not missing_core and not missing_knowledge,
        "missing_root": missing_root,
        "missing_core": missing_core,
        "missing_knowledge": missing_knowledge,
        "root": str(root),
    }
