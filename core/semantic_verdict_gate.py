from __future__ import annotations

from typing import Any, Iterable


GATE_VERSION = "2.0-independent-semantic-verdict"


def evaluate_semantic_verdict_gate(
    atom: dict[str, Any], proof: str, evidence: Iterable[dict[str, Any]], *, categorical: bool,
) -> dict[str, Any]:
    if not categorical:
        return {"state": "NOT_REQUIRED", "reasons": [], "version": GATE_VERSION}
    rows = list(evidence or [])
    proof = str(proof or "").upper()
    reasons: list[str] = []

    if proof in {"STRUCTURED_VALUE", "STRUCTURED_COMPARISON"}:
        def trace_level(row: dict[str, Any]) -> str:
            locator = row.get("source_locator")
            locator_level = locator.get("physical_trace_level") if isinstance(locator, dict) else ""
            return str(row.get("physical_trace_level") or locator_level or "").upper()

        exact = [
            row for row in rows
            if trace_level(row) in {"ROW_TRACE", "CELL_TRACE"}
            and row.get("admitted", True) is not False
            and not str(row.get("engineering_plausibility_status") or "").upper().startswith("BLOCKED")
        ]
        if not exact:
            reasons.append("Числовой вывод не имеет допущенного физического следа до строки/ячейки источника.")
    elif proof == "VERIFIED_ENGINEERING_EVIDENCE":
        semantic = [
            row for row in rows
            if str(row.get("semantic_gate_state") or "").upper() == "PASSED"
            and str(row.get("contract_state") or "").upper() == "SATISFIED"
            and str(row.get("semantic_verdict") or row.get("judge_verdict") or "").upper() in {"SUPPORTS", "CONTRADICTS"}
        ]
        if not semantic:
            reasons.append("Ни один адресный фрагмент не прошёл независимый смысловой gate доказательственного контракта.")
    elif proof == "STRUCTURED_PRESENCE":
        present = [
            row for row in rows
            if row.get("document") and row.get("page") not in (None, "")
            and str(row.get("contract_state") or "").upper() == "SATISFIED"
            and str(row.get("semantic_gate_state") or "").upper() == "PASSED"
            and str(row.get("semantic_verdict") or row.get("judge_verdict") or "").upper() == "SUPPORTS"
        ]
        if not present:
            reasons.append("Наличие не подтверждено адресным структурированным фрагментом требуемого типа.")
    elif proof == "VERIFIED_CLAUSE":
        if not any(row.get("clause_verified") or str(row.get("semantic_gate_state") or "").upper() == "PASSED" for row in rows):
            reasons.append("Нормативный пункт не имеет проверенного адресного доказательства.")
    elif proof in {"VERIFIED_SET_EVIDENCE", "STRUCTURED_COMPLETENESS"}:
        if not any(row.get("set_complete") or row.get("completeness_verified") for row in rows):
            reasons.append("Комплектность не подтверждена полным адресным перечнем.")

    return {
        "state": "PASSED" if not reasons else "BLOCKED",
        "reasons": reasons,
        "version": GATE_VERSION,
    }
