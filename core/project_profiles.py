from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectProfile:
    code: str
    name: str
    description: str
    enabled_packs: tuple[str, ...]
    applicability: tuple[str, ...]


class ProjectProfileRegistry:
    """Загружает профили проекта и подключаемые пакеты знаний.

    Профиль не меняет работу универсального Core. Он только определяет,
    какие каталоги правил следует подключить на последующих этапах проверки.
    """

    def __init__(self, knowledge_root: str | Path):
        self.root = Path(knowledge_root)

    def load(self) -> list[ProjectProfile]:
        profiles: list[ProjectProfile] = []
        for path in sorted((self.root / "profiles").glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            profiles.append(ProjectProfile(
                code=str(payload.get("code") or path.stem),
                name=str(payload.get("name") or path.stem),
                description=str(payload.get("description") or ""),
                enabled_packs=tuple(payload.get("enabled_packs") or ("core",)),
                applicability=tuple(payload.get("applicability") or ()),
            ))
        return profiles

    def summary(self) -> dict[str, Any]:
        profiles = self.load()
        packs = sorted({pack for profile in profiles for pack in profile.enabled_packs})
        return {
            "profiles": len(profiles),
            "profile_codes": [profile.code for profile in profiles],
            "available_packs": packs,
        }
