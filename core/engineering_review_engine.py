from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code


class CrossSectionDependencyEngine:
    """Adds engineering meaning to cross-section comparisons.

    The registry does not decide legal compliance. It describes who owns a value,
    where the value is expected to be repeated and why a mismatch matters.
    """
    def __init__(self, knowledge_root: str | Path):
        root = Path(knowledge_root)
        self.rules = self._load(root / "cross_section_dependency_rules.json")
        self.norms = self._load(root / "normative_requirements_v1.json")
        self.by_parameter = {str(r.get("parameter_code") or "").upper(): r for r in self.rules if r.get("parameter_code")}

    @staticmethod
    def _load(path: Path) -> list[dict[str, Any]]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def requirements_for_parameter(self, parameter_code: str) -> list[dict[str, Any]]:
        code = canonical_parameter_code(parameter_code)
        out=[]
        for req in self.norms:
            if code and code in set(req.get("parameter_codes") or []):
                out.append(req)
        # universal evidence + cross-section rules are intentionally attached
        for req in self.norms:
            if req.get("id") in {"NR-CROSS-001","NR-EVID-001"}:
                out.append(req)
        return out

    def enrich_comparisons(self, comparisons: list[dict[str, Any]]) -> int:
        changed=0
        for row in comparisons:
            code = canonical_parameter_code(row.get("parameter_code") or row.get("parameter"))
            rule = self.by_parameter.get(code)
            if not rule:
                continue
            row["data_owner_sections"] = list(rule.get("owner_sections") or [])
            row["dependent_sections"] = list(rule.get("control_sections") or [])
            row["dependency_rationale"] = str(rule.get("rationale") or "")
            row["dependency_priority"] = str(rule.get("priority") or row.get("priority") or "")
            reqs=self.requirements_for_parameter(code)
            row["normative_requirements"] = [
                {"id":x.get("id"),"source":x.get("source"),"topic":x.get("topic"),"requirement":x.get("requirement"),"status":x.get("status")}
                for x in reqs
            ]
            status = normalize_text(row.get("status") or "")
            evidence = int(row.get("strong_evidence_count") or row.get("evidence_count") or 0)
            if "расхожд" in status or "конфликт" in status:
                row["preliminary_compliance"] = "Выявлен риск несоответствия"
            elif "совпад" in status or "подтверж" in status:
                row["preliminary_compliance"] = "Предварительно согласовано"
            elif evidence < 2 or "недостат" in status:
                row["preliminary_compliance"] = "Недостаточно данных"
            else:
                row["preliminary_compliance"] = "Требует инженерной проверки"
            changed += 1
        return changed

    def checklist_context(self, question: str, compiled_rule: dict[str, Any]) -> list[dict[str, Any]]:
        low=normalize_text(question)
        codes={canonical_parameter_code(x) for x in (compiled_rule.get("parameter_codes") or [])}
        ranked=[]
        for req in self.norms:
            score=0
            if codes and codes.intersection(set(req.get("parameter_codes") or [])):
                score += 5
            for token in req.get("keywords") or []:
                if normalize_text(token) in low:
                    score += 1
            if score:
                ranked.append((score, req))
        ranked.sort(key=lambda x:x[0], reverse=True)
        return [dict(x[1]) for x in ranked[:4]]

    def summary(self) -> dict[str, int]:
        return {"dependency_rules":len(self.rules),"normative_requirements":len(self.norms)}
