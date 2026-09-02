from __future__ import annotations

from typing import Any, Iterable


VERSION = "proof-th-cross-section-v1"

# Первый вертикальный контур: характеристики, владельцем или значимым
# потребителем которых является раздел ТХ. Список ограничивает только метрику
# Proof-контура; универсальный межраздельный gate применяется ко всем правилам.
TECHNOLOGY_PROOF_PARAMETERS = {
    "CAPACITY",
    "DESIGN_CAPACITY",
    "SHIFT_DURATION",
    "PERSONNEL",
    "EQUIPMENT_COUNT",
    "STORAGE_CAPACITY",
    "STORAGE_MASS",
    "FLOW_RATE",
    "PRESSURE",
    "DIAMETER",
    "PIPELINE_CAPACITY",
    "PUMP_HEAD",
    "POWER_INSTALLED",
    "POWER_CALCULATED",
    "VOLTAGE",
    "RES_VOLUME",
    "VOLUME",
    "LENGTH",
    "WIDTH",
    "DEPTH",
    "QUANTITY",
    "MOISTURE",
    "BULK_DENSITY",
}

_COMPLETED_STATUS = {
    "СОВПАДАЕТ": "VERIFIED_OK",
    "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ": "PROJECT_FINDING",
    "КОНФЛИКТ ВНУТРИ РАЗДЕЛА": "PROJECT_FINDING",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _addressable_sources(row: dict[str, Any]) -> list[dict[str, Any]]:
    records = row.get("verification_evidence") or row.get("source_records") or []
    if not isinstance(records, list):
        return []
    return [
        item for item in records
        if isinstance(item, dict)
        and item.get("document")
        and item.get("page") not in (None, "")
    ]


def _is_cross_section_row(row: dict[str, Any]) -> bool:
    return bool(
        _text(row.get("category")) == "Межраздельная сверка"
        or _text(row.get("check_type")) == "Сводная межраздельная проверка"
        or _text(row.get("check_code")).startswith("CORE-XSEC-")
    )


def _block(row: dict[str, Any], reasons: list[str]) -> None:
    addressable = bool(_addressable_sources(row))
    status = _text(row.get("status")).upper()
    mismatch = status in {"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ", "КОНФЛИКТ ВНУТРИ РАЗДЕЛА"}
    kind = "REVIEW_QUESTION" if mismatch and addressable else "SYSTEM_LIMITATION"
    row.update({
        "final_verification_kind": kind,
        "final_verification_state": (
            "Требует проверки специалистом" if kind == "REVIEW_QUESTION"
            else "Не проверено автоматически"
        ),
        "verification_kind": kind,
        "verification_state": (
            "Требует проверки специалистом" if kind == "REVIEW_QUESTION"
            else "Не проверено автоматически"
        ),
        "proof_kind": "STRUCTURED_COMPARISON" if addressable else "EVIDENCE_GAP",
        "evidence_level": "L4" if addressable else "L2",
        "evidence_level_reason": "Межраздельный вывод не прошёл строгий контракт источников.",
        "adversarial_state": "BLOCKED",
        "deep_evidence_state": "BLOCKED",
        "automatic_verdict_eligible": False,
        "candidate_evidence_only": True,
        "coverage_state": "TARGETED_REVIEW" if kind == "REVIEW_QUESTION" else "AUTOMATION_GAP",
        "coverage_reason_code": "CROSS_SECTION_PROOF_GATE_BLOCKED",
        "coverage_reason": "; ".join(reasons),
        "finding_type": kind,
        "cross_section_gate_state": "BLOCKED",
        "cross_section_gate_reasons": reasons,
    })


def qualify_cross_section_verdicts(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Turns a comparison diagnostic into a fail-closed product verdict.

    A categorical result requires the same canonical object/property/unit,
    addressable trusted evidence from two section families and an owner→control
    route from the dependency matrix. AI is not part of this critical path.
    """
    checked = passed = blocked = 0
    for row in rows or []:
        if not _is_cross_section_row(row):
            continue
        checked += 1
        status = _text(row.get("status")).upper()
        target_kind = _COMPLETED_STATUS.get(status)
        sources = _addressable_sources(row)
        trusted_sources = [item for item in sources if item.get("trusted_for_mismatch")]
        trusted_sections = {
            _text(item.get("section")) for item in trusted_sources if _text(item.get("section"))
        }
        diagnostics = row.get("dependency_diagnostics") or {}
        owner_present = set(diagnostics.get("owner_present") or [])
        control_present = set(diagnostics.get("control_present") or [])
        binding = row.get("engineering_binding") or {}

        reasons: list[str] = []
        if not target_kind:
            reasons.append("Сопоставление не завершено категоричным статусом.")
        if len(trusted_sources) < 2 or len(trusted_sections) < 2:
            reasons.append("Нет двух адресных доверенных источников из независимых разделов.")
        if not owner_present:
            reasons.append("Не найден профильный раздел-владелец показателя.")
        if not control_present:
            reasons.append("Не найден независимый контрольный раздел.")
        if binding and not bool(binding.get("parameter_expected_for_object", True)):
            reasons.append("Показатель нетипичен для распознанного класса объекта.")
        if not _text(row.get("object_id")) or not _text(row.get("parameter_code")) or not _text(row.get("unit")):
            reasons.append("Не завершена каноническая привязка объекта, показателя или единицы.")

        row["cross_section_gate"] = {
            "version": VERSION,
            "required": True,
            "target_kind": target_kind,
            "owner_present": sorted(owner_present),
            "control_present": sorted(control_present),
            "trusted_sections": sorted(trusted_sections),
            "addressable_sources": len(sources),
            "passed": not reasons,
            "reasons": reasons,
        }
        row["cross_section_required"] = bool(owner_present and control_present)
        row["applicability_proven"] = bool(owner_present and control_present)
        row["checker_family"] = "Детерминированная межраздельная сверка"
        row["checker_mode"] = "Объект → показатель → единица → владелец → контроль"
        row["verification_level"] = "L3_CROSS_CHECK"

        if reasons:
            _block(row, reasons)
            blocked += 1
            continue

        state = "Соответствует" if target_kind == "VERIFIED_OK" else "Выявлено несоответствие"
        row.update({
            "final_verification_kind": target_kind,
            "final_verification_state": state,
            "verification_kind": target_kind,
            "verification_state": state,
            "proof_kind": "STRUCTURED_COMPARISON",
            "evidence_level": "L5",
            "evidence_level_reason": "Подтверждены объект, показатель, единица и независимый маршрут владелец→контроль.",
            "adversarial_state": "PASSED",
            "deep_evidence_state": "PASSED",
            "automatic_verdict_eligible": True,
            "candidate_evidence_only": False,
            "coverage_state": "AUTOMATED_COMPLETE" if target_kind == "VERIFIED_OK" else "PROJECT_FINDING_CONFIRMED",
            "coverage_reason_code": "CROSS_SECTION_PROOF_GATE_PASSED",
            "coverage_reason": "Строгая детерминированная межраздельная проверка завершена.",
            "finding_type": "PROJECT_STATUS" if target_kind == "VERIFIED_OK" else "PROJECT_FINDING",
            "cross_section_gate_state": "PASSED",
            "cross_section_gate_reasons": [],
        })
        passed += 1

    return {"version": VERSION, "checked": checked, "passed": passed, "blocked": blocked}


def technology_proof_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    selected = [
        row for row in rows or []
        if _text(row.get("parameter_code")).upper() in TECHNOLOGY_PROOF_PARAMETERS
        and _is_cross_section_row(row)
    ]
    completed = [
        row for row in selected
        if _text(row.get("final_verification_kind")).upper() in {"VERIFIED_OK", "PROJECT_FINDING"}
    ]
    addressable = [row for row in selected if _addressable_sources(row)]
    return {
        "version": VERSION,
        "scope": "ТХ и зависимые разделы",
        "parameters_supported": len(TECHNOLOGY_PROOF_PARAMETERS),
        "checks": len(selected),
        "completed": len(completed),
        "verified_ok": sum(_text(row.get("final_verification_kind")).upper() == "VERIFIED_OK" for row in selected),
        "project_findings": sum(_text(row.get("final_verification_kind")).upper() == "PROJECT_FINDING" for row in selected),
        "review_questions": sum(_text(row.get("final_verification_kind")).upper() == "REVIEW_QUESTION" for row in selected),
        "system_limitations": sum(_text(row.get("final_verification_kind")).upper() == "SYSTEM_LIMITATION" for row in selected),
        "strict_coverage_pct": round(100 * len(completed) / max(1, len(selected)), 1),
        "addressable_evidence_pct": round(100 * len(addressable) / max(1, len(selected)), 1),
    }
