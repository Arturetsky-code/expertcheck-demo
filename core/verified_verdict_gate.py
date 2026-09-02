from __future__ import annotations

from typing import Any, Iterable


GATE_VERSION = "17.0-final-verdict-gate-v1"
CATEGORICAL = {"VERIFIED_OK", "PROJECT_FINDING"}
DETERMINISTIC_PROOFS = {
    "STRUCTURED_VALUE",
    "STRUCTURED_COMPARISON",
    "VERIFIED_SET_EVIDENCE",
    "STRUCTURED_COMPLETENESS",
    "NORMATIVE_EVIDENCE",
    "VERIFIED_CLAUSE",
}


def _kind(row: dict[str, Any]) -> str:
    return str(row.get("final_verification_kind") or row.get("verification_kind") or "").upper()


def _addressable_item(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(
            (value.get("document") and value.get("page") not in (None, ""))
            or value.get("source_locator")
        )
    text = str(value or "").lower()
    return bool(text and ("стр." in text or "стр " in text or "page " in text))


def _has_addressable_evidence(row: dict[str, Any]) -> bool:
    for key in ("verification_evidence", "evidence", "evidence_candidates", "deep_evidence_candidates"):
        value = row.get(key)
        if isinstance(value, list) and any(_addressable_item(item) for item in value):
            return True
        if not isinstance(value, list) and _addressable_item(value):
            return True
    return False


def verdict_gate(row: dict[str, Any], *, domain: str = "") -> dict[str, Any]:
    kind = _kind(row)
    if kind not in CATEGORICAL and str(row.get("evidence_level") or "") != "L5":
        return {"passed": True, "required": False, "reasons": []}

    reasons: list[str] = []
    proof = str(row.get("proof_kind") or row.get("evidence_quality_state") or "").upper()
    addressable = _has_addressable_evidence(row)
    adversarial = str(row.get("adversarial_state") or row.get("deep_evidence_state") or "").upper()
    semantic_completed = int(row.get("semantic_consensus_completed") or 0)
    checker_family = str(row.get("checker_family") or "").lower()
    checker_mode = str(row.get("checker_mode") or "").lower()
    semantic_route = bool(
        semantic_completed
        or str(row.get("semantic_consensus_state") or "").upper() == "PASSED"
        or "смыслов" in checker_family
        or "консенсус" in checker_mode
        or proof == "VERIFIED_ENGINEERING_EVIDENCE"
    )

    deterministic_ok = proof in DETERMINISTIC_PROOFS
    if proof == "ATOMIC_AGGREGATION":
        deterministic_ok = bool(
            int(row.get("atomic_completed") or 0) > 0
            and str(row.get("atomic_verified_core_gate_state") or "").upper() == "PASSED"
        )
    if domain == "normative" and row.get("verified_clause") and addressable:
        deterministic_ok = True
    semantic_ok = bool(
        semantic_completed > 0
        and adversarial == "PASSED"
        and addressable
        and (
            str(row.get("semantic_consensus_state") or "").upper() == "PASSED"
            or str(row.get("semantic_gate_state") or "").upper() == "PASSED"
        )
    )
    # Atomic AI decisions carry the full machine contract.  Parent rows carry
    # the completed-atom counter after aggregation.
    if row.get("semantic_judge") or row.get("semantic_critic"):
        semantic_ok = semantic_ok and bool(
            row.get("semantic_consensus_independent")
            and (row.get("semantic_judge") or {}).get("valid")
            and (row.get("semantic_critic") or {}).get("valid")
            and str(row.get("evidence_contract_state") or "").upper() == "SATISFIED"
        )

    if not addressable:
        reasons.append("Категоричный вывод не содержит адресного доказательства.")
    if adversarial != "PASSED":
        reasons.append("Не пройден итоговый adversarial gate.")
    if semantic_route and not semantic_ok:
        reasons.append("Смысловой маршрут не завершил проверяемые условия и машинный контракт.")
    if not semantic_route and not deterministic_ok:
        reasons.append("Не указан специализированный детерминированный механизм, разрешающий категоричный вывод.")
    if kind not in CATEGORICAL:
        reasons.append("Уровень L5 противоречит итоговому классу проверки.")

    return {
        "passed": not reasons,
        "required": True,
        "version": GATE_VERSION,
        "domain": domain,
        "proof_kind": proof,
        "semantic_route": semantic_route,
        "semantic_completed": semantic_completed,
        "addressable_evidence": addressable,
        "reasons": reasons,
    }


def _downgrade(row: dict[str, Any], gate: dict[str, Any]) -> None:
    previous = _kind(row) or str(row.get("verification_kind") or "")
    addressable = bool(gate.get("addressable_evidence"))
    kind = "REVIEW_QUESTION" if addressable else "SYSTEM_LIMITATION"
    state = "Требует проверки специалистом" if addressable else "Не проверено автоматически"
    status = "Требует проверки" if addressable else "Не проверено системой"
    reasons = list(dict.fromkeys(str(value) for value in gate.get("reasons") or [] if value))
    row.update({
        "pre_verified_core_kind": previous,
        "final_verification_kind": kind,
        "final_verification_state": state,
        "verification_kind": kind,
        "verification_state": state,
        "status": status,
        "evidence_level": "L4" if addressable else "L2",
        "evidence_level_reason": "Категоричный вывод заблокирован итоговым Verified Core gate.",
        "verified_core_gate": gate,
        "verified_core_gate_state": "BLOCKED",
        "verified_core_gate_reasons": reasons,
        "adversarial_state": "BLOCKED",
        "deep_evidence_state": "BLOCKED",
        "automatic_verdict_eligible": False,
        "candidate_evidence_only": True,
        "coverage_state": "TARGETED_REVIEW" if addressable else "AUTOMATION_GAP",
        "coverage_reason_code": "VERIFIED_CORE_FINAL_GATE_BLOCKED",
        "coverage_reason": "; ".join(reasons),
    })
    existing = list(row.get("adversarial_reasons") or [])
    row["adversarial_reasons"] = list(dict.fromkeys(existing + reasons))
    row["deep_evidence_reasons"] = list(row["adversarial_reasons"])
    recommendation = str(row.get("recommendation") or "")
    if not recommendation or "дополнительное действие не требуется" in recommendation.lower():
        row["recommendation"] = "Проверить адресные доказательства и зафиксировать решение специалиста."


def enforce_verified_verdicts(rows: Iterable[dict[str, Any]], *, domain: str) -> dict[str, Any]:
    checked = passed = blocked = 0
    for row in rows or []:
        gate = verdict_gate(row, domain=domain)
        if not gate.get("required"):
            continue
        checked += 1
        row["verified_core_gate"] = gate
        row["verified_core_gate_state"] = "PASSED" if gate.get("passed") else "BLOCKED"
        row["verified_core_gate_reasons"] = list(gate.get("reasons") or [])
        if gate.get("passed"):
            passed += 1
        else:
            _downgrade(row, gate)
            blocked += 1
    return {
        "version": GATE_VERSION,
        "domain": domain,
        "checked": checked,
        "passed": passed,
        "blocked": blocked,
    }


def enforce_project_verdicts(
    *,
    assignment_rows: list[dict[str, Any]],
    normative_rows: list[dict[str, Any]],
    checklist_review: dict[str, Any],
    comparisons: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    checklist_rows = list((checklist_review or {}).get("results") or [])
    domains = {
        "assignment": enforce_verified_verdicts(assignment_rows, domain="assignment"),
        "normative": enforce_verified_verdicts(normative_rows, domain="normative"),
        "checklist": enforce_verified_verdicts(checklist_rows, domain="checklist"),
        "comparison": enforce_verified_verdicts(comparisons or [], domain="comparison"),
    }
    return {
        "version": GATE_VERSION,
        "domains": domains,
        "checked": sum(row["checked"] for row in domains.values()),
        "passed": sum(row["passed"] for row in domains.values()),
        "blocked": sum(row["blocked"] for row in domains.values()),
    }
