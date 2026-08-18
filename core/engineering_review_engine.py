from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code
from .normative_intelligence import NormativeIntelligence
from .engineering_verification_v2 import EngineeringVerification2


class CrossSectionDependencyEngine:
    """Adds engineering meaning to cross-section comparisons.

    The registry does not decide legal compliance. It describes who owns a value,
    where the value is expected to be repeated and why a mismatch matters.
    """
    def __init__(self, knowledge_root: str | Path):
        root = Path(knowledge_root)
        self.rules = self._load(root / "cross_section_dependency_rules.json")
        self.norms = self._load(root / "normative_requirements_v2.json") or self._load(root / "normative_requirements_v1.json")
        self.normative = NormativeIntelligence(root)
        self.verification2 = EngineeringVerification2(root)
        self.by_parameter = {str(r.get("parameter_code") or "").upper(): r for r in self.rules if r.get("parameter_code")}

    @staticmethod
    def _load(path: Path) -> list[dict[str, Any]]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []


    @staticmethod
    def _sections_in_row(row: dict[str, Any]) -> set[str]:
        """Best-effort section extraction from comparison evidence."""
        values=[]
        for key in ("sections","section","document_values","sources","documents"):
            value=row.get(key)
            if isinstance(value, dict):
                values.extend(str(k) for k in value.keys())
                values.extend(str(v) for v in value.values())
            elif isinstance(value, (list,tuple,set)):
                values.extend(str(x) for x in value)
            elif value:
                values.append(str(value))
        blob=" ".join(values).upper()
        aliases={
            "ПЗ":["ПЗ","ПОЯСНИТЕЛЬН"],
            "ПЗУ":["ПЗУ","ГЕНПЛАН","ГЕНЕРАЛЬН"],
            "АР":["АР","АРХИТЕКТУР"],
            "КР":["КР","КОНСТРУКТИВ"],
            "ТХ":["ТХ","ТЕХНОЛОГИЧ"],
            "ИОС1":["ИОС1","ЭОМ","ЭС","ЭЛЕКТРОСНАБ"],
            "ИОС2":["ИОС2","ВК","ВОДОСНАБ"],
            "ИОС3":["ИОС3","ВОДООТВ"],
            "ПБ":["ПБ","ПОЖАР"],
            "ООС":["ООС","ОХРАНЕ ОКРУЖ"],
            "ПОС":["ПОС","ОРГАНИЗАЦИИ СТРОИТЕЛЬ"],
            "АД":["АД","АВТОМОБИЛЬН"],
            "ГТ":["ГТ","ГИДРОТЕХ"],
            "ИГИ":["ИГИ","ИНЖЕНЕРНО-ГЕОЛ"],
        }
        found=set()
        for section,tokens in aliases.items():
            if any(t in blob for t in tokens):
                found.add(section)
        return found

    def dependency_diagnostics(self, row: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
        present=self._sections_in_row(row)
        owners=list(rule.get("owner_sections") or [])
        controls=list(rule.get("control_sections") or [])
        owner_present=[x for x in owners if x in present]
        control_present=[x for x in controls if x in present]
        return {
            "present_sections": sorted(present),
            "owner_present": owner_present,
            "control_present": control_present,
            "owner_missing": [x for x in owners if x not in present],
            "control_missing": [x for x in controls if x not in present],
            "owner_evidence_ok": bool(owner_present) if owners else True,
            "cross_section_coverage": len(owner_present)+len(control_present),
        }

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
            binding=self.verification2.validate_binding(
                str(row.get("object") or row.get("object_name") or ""),
                code,
                " ".join(self._sections_in_row(row))
            )
            row["engineering_binding"]=binding
            diag=self.dependency_diagnostics(row, rule)
            row["dependency_diagnostics"] = diag
            row["data_owner_evidence"] = "Подтверждён" if diag.get("owner_evidence_ok") else "Не найден профильный источник"
            row["missing_expected_sections"] = list(dict.fromkeys((diag.get("owner_missing") or []) + (diag.get("control_missing") or [])))
            reqs=self.normative.search(
                question=str(row.get("parameter_name") or row.get("parameter") or ""),
                parameter_codes=[code],
                section=" ".join(sorted(self._sections_in_row(row))),
                object_type=(binding.get("object_type") or ""),
                limit=6
            ) or self.requirements_for_parameter(code)
            row["normative_requirements"] = [
                {"id":x.get("id"),"source":x.get("source"),"paragraph":x.get("paragraph"),"topic":x.get("topic"),"requirement":x.get("requirement"),"status":x.get("status"),"legal_confidence":x.get("legal_confidence") or self.normative.legal_confidence(x)}
                for x in reqs
            ]
            status = normalize_text(row.get("status") or "")
            evidence = int(row.get("strong_evidence_count") or row.get("evidence_count") or 0)
            if "расхожд" in status or "конфликт" in status:
                row["preliminary_compliance"] = "Выявлен риск несоответствия"
            elif not diag.get("owner_evidence_ok"):
                row["preliminary_compliance"] = "Недостаточно данных: не найден профильный источник"
            elif "совпад" in status or "подтверж" in status:
                row["preliminary_compliance"] = "Предварительно согласовано"
            elif evidence < 2 or "недостат" in status:
                row["preliminary_compliance"] = "Недостаточно данных"
            else:
                row["preliminary_compliance"] = "Требует инженерной проверки"
            changed += 1
        return changed

    def checklist_context(self, question: str, compiled_rule: dict[str, Any]) -> list[dict[str, Any]]:
        codes=[canonical_parameter_code(x) for x in (compiled_rule.get("parameter_codes") or [])]
        results=self.normative.search(question=question,parameter_codes=codes,limit=6)
        return results


    def summary(self) -> dict[str, int]:
        return {"dependency_rules":len(self.rules),"normative_requirements":len(self.norms),**self.normative.summary()}
