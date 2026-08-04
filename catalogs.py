from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    payload: dict[str, Any]
    source: str

class KnowledgeRegistry:
    """Loads core and optional knowledge packs without coupling code to project types."""
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def load_json(self, relative: str | Path, default=None):
        path = self.root / relative
        if not path.exists():
            return [] if default is None else default
        return json.loads(path.read_text(encoding="utf-8"))

    def iter_pack_files(self, pack_names: Iterable[str] | None = None):
        packs_dir = self.root / "packs"
        if not packs_dir.exists():
            return
        allowed = set(pack_names or [])
        for path in packs_dir.rglob("*.json"):
            relative = path.relative_to(packs_dir)
            if allowed and relative.parts[0] not in allowed:
                continue
            yield path

    def load_rules(self, pack_names: Iterable[str] | None = None) -> list[dict]:
        rules = list(self.load_json("core/rules.json", []))
        for path in self.iter_pack_files(pack_names):
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                rules.extend(x for x in data if isinstance(x, dict) and ("rule_kind" in x or "parameter_code" in x))
        return rules

    def summary(self) -> dict[str, int]:
        return {
            "objects": len(self.load_json("core/object_catalog.json", [])),
            "parameters": len(self.load_json("core/parameter_catalog.json", [])),
            "tables": len(self.load_json("core/table_catalog.json", [])),
            "core_rules": len(self.load_json("core/rules.json", [])),
            "pack_files": sum(1 for _ in self.iter_pack_files()),
        }
