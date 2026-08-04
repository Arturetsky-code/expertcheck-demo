from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeBase:
    """Read-only access to aggregated evidence from prior expert remarks."""

    def __init__(self, knowledge_root: Path):
        self.root = Path(knowledge_root)
        self.analytics_root = self.root / "analytics"
        self._summary = self._load("evidence_summary.json", {})
        self._parameter_index = self._load("parameter_evidence_index.json", {})

    def _load(self, name: str, default: Any) -> Any:
        path = self.analytics_root / name
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def summary(self) -> dict[str, Any]:
        return dict(self._summary)

    def evidence_for_parameter(self, parameter_code: str) -> dict[str, Any]:
        return dict(self._parameter_index.get(parameter_code, {}))

    @staticmethod
    def risk_level(projects_count: int, remarks_count: int) -> str:
        if projects_count >= 3 or remarks_count >= 8:
            return "Высокий"
        if projects_count >= 2 or remarks_count >= 3:
            return "Средний"
        if remarks_count >= 1:
            return "Низкий"
        return "Нет данных"

    def enrich_comparison(self, comparison: dict[str, Any]) -> None:
        evidence = self.evidence_for_parameter(str(comparison.get("parameter_code") or ""))
        remarks_count = int(evidence.get("remarks_count") or 0)
        projects_count = int(evidence.get("projects_count") or 0)
        comparison["knowledge_evidence_count"] = remarks_count
        comparison["knowledge_project_count"] = projects_count
        comparison["knowledge_risk_level"] = self.risk_level(projects_count, remarks_count)
        comparison["knowledge_project_ids"] = evidence.get("project_ids", [])
        comparison["knowledge_violation_types"] = evidence.get("violation_types", [])
        comparison["knowledge_examples"] = evidence.get("examples", [])
