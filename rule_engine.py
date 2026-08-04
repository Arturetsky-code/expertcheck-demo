from __future__ import annotations
from typing import Any

class RuleEngine:
    def __init__(self, rules: list[dict]):
        self.rules = [r for r in rules if r.get("enabled", True)]

    def applicable_rules(self, document_types: set[str] | None = None) -> list[dict]:
        if not document_types:
            return self.rules
        out=[]
        for rule in self.rules:
            sources=set(rule.get("comparison_documents") or rule.get("scope") or [])
            if not sources or sources & document_types:
                out.append(rule)
        return out

    def explain(self, rule: dict, evidence: dict[str, Any]) -> str:
        title=rule.get("name") or rule.get("title") or rule.get("id","Правило")
        values=evidence.get("values", "")
        return f"{title}. Сопоставлены подтверждённые источники: {values}".strip()
