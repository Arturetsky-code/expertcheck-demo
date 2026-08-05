from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .normalization import normalize_text


@dataclass(frozen=True)
class ProfileMatch:
    code: str
    name: str
    confidence: float
    matched_aliases: tuple[str, ...]
    properties: tuple[str, ...]


class KnowledgeEngine:
    """Версионно-независимый слой инженерных знаний.

    Core передает наименование объекта, а движок возвращает профиль и ожидаемые
    характеристики. Отраслевые знания хранятся в JSON, а не в алгоритмах Core.
    """

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1] / "knowledge"
        self.object_library = self._load("object_library.json", {"profiles": []})
        self.property_library = self._load("property_library.json", {"properties": []})
        self.profiles = list(self.object_library.get("profiles") or [])
        self.properties = {str(x.get("code")): x for x in self.property_library.get("properties") or []}

    def _load(self, filename: str, default: dict[str, Any]) -> dict[str, Any]:
        path = self.root / filename
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def classify(self, value: Any) -> ProfileMatch:
        text = normalize_text(value)
        best: tuple[float, dict[str, Any], list[str]] | None = None
        for profile in self.profiles:
            aliases = [normalize_text(a) for a in profile.get("aliases") or [] if normalize_text(a)]
            matched = [a for a in aliases if a in text]
            if not matched:
                continue
            longest = max(len(a) for a in matched)
            coverage = longest / max(1, len(text))
            score = min(0.99, 0.72 + 0.18 * coverage + 0.035 * min(3, len(matched)))
            if best is None or score > best[0]:
                best = (score, profile, matched)
        if best is None:
            return ProfileMatch("GENERIC_OBJECT", "Инженерный объект", 0.35, tuple(), tuple())
        score, profile, matched = best
        return ProfileMatch(
            str(profile.get("code") or "GENERIC_OBJECT"),
            str(profile.get("name") or "Инженерный объект"),
            round(score, 3),
            tuple(matched),
            tuple(str(x) for x in profile.get("properties") or []),
        )

    def expected_properties(self, profile_code: str) -> list[str]:
        for profile in self.profiles:
            if str(profile.get("code")) == profile_code:
                return [str(x) for x in profile.get("properties") or []]
        return []

    def property_name(self, code: str) -> str:
        return str((self.properties.get(code) or {}).get("name") or code)

    def summary(self) -> dict[str, int | str]:
        return {
            "version": str(self.object_library.get("version") or ""),
            "object_profiles": len(self.profiles),
            "properties": len(self.properties),
        }


@lru_cache(maxsize=1)
def default_knowledge_engine() -> KnowledgeEngine:
    return KnowledgeEngine()
