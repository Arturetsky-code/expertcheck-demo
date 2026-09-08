from __future__ import annotations

from typing import Any, Iterable


VERSION = "18.7-cross-section-proof-v2"

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


def _source_value_key(item: dict[str, Any]) -> tuple[str, str]:
    raw = item.get("value")
    try:
        value = f"{float(raw):.9g}"
    except (TypeError, ValueError):
        value = _text(raw or item.get("text")).casefold()
    return value, _text(item.get("unit")).casefold()


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

        # 18.7 separates proof of agreement from proof of contradiction.
        # A mismatch/finding still requires the owner→control dependency route.
        # An exact/tolerance-safe agreement may be closed from two strong,
        # independent addressable project sources once canonical binding is
        # complete; a missing owner mapping in the knowledge base is then not a
        # reason to keep a true agreement in the specialist queue.
        agreement_mode = target_kind == "VERIFIED_OK"
        trusted_value_keys = {
            _source_value_key(item)
            for item in trusted_sources
            if _source_value_key(item)[0]
        }
        independent_conflict_mode = bool(
            target_kind == "PROJECT_FINDING"
            and len(trusted_value_keys) >= 2
        )
        trusted_count = max(
            len(trusted_sources),
            int(row.get("independent_trusted_sources") or 0),
        )
        trusted_family_count = max(
            len(trusted_sections),
            len(row.get("trusted_section_families") or []),
        )
        canonical_binding_complete = bool(
            _text(row.get("object_id"))
            and _text(row.get("parameter_code"))
            and _text(row.get("unit"))
        )
        strong_independent_evidence = bool(
            len(sources) >= 2
            and trusted_count >= 2
            and trusted_family_count >= 2
        )

        reasons: list[str] = []
        if not target_kind:
            reasons.append("Сопоставление не завершено категоричным статусом.")
        if not strong_independent_evidence:
            reasons.append("Нет двух адресных доверенных источников из независимых разделов.")
        if not agreement_mode and not independent_conflict_mode:
            if not owner_present:
                reasons.append("Не найден профильный раздел-владелец показателя.")
            if not control_present:
                reasons.append("Не найден независимый контрольный раздел.")
        if binding and not bool(binding.get("parameter_expected_for_object", True)):
            reasons.append("Показатель нетипичен для распознанного класса объекта.")
        if not canonical_binding_complete:
            reasons.append("Не завершена каноническая привязка объекта, показателя или единицы.")

        proof_route = (
            "INDEPENDENT_AGREEMENT"
            if agreement_mode and strong_independent_evidence and canonical_binding_complete
            else "INDEPENDENT_CONFLICT"
            if independent_conflict_mode and strong_independent_evidence and canonical_binding_complete
            else "OWNER_CONTROL"
        )
        row["cross_section_gate"] = {
            "version": VERSION,
            "required": True,
            "target_kind": target_kind,
            "proof_route": proof_route,
            "owner_present": sorted(owner_present),
            "control_present": sorted(control_present),
            "trusted_sections": sorted(
                trusted_sections or set(row.get("trusted_section_families") or [])
            ),
            "trusted_source_count": trusted_count,
            "addressable_sources": len(sources),
            "passed": not reasons,
            "reasons": reasons,
        }
        row["cross_section_required"] = bool(
            (
                (agreement_mode or independent_conflict_mode)
                and strong_independent_evidence
                and canonical_binding_complete
            )
            or (owner_present and control_present)
        )
        row["applicability_proven"] = row["cross_section_required"]
        row["checker_family"] = "Детерминированная межраздельная сверка"
        row["checker_mode"] = (
            "Объект → показатель → единица → 2 независимых совпадающих источника"
            if proof_route == "INDEPENDENT_AGREEMENT"
            else "Объект → показатель → единица → 2 независимых противоречащих источника"
            if proof_route == "INDEPENDENT_CONFLICT"
            else "Объект → показатель → единица → владелец → контроль"
        )
        row["verification_level"] = "L3_CROSS_CHECK"

        if reasons:
            _block(row, reasons)
            blocked += 1
            continue

        state = "Соответствует" if target_kind == "VERIFIED_OK" else "Выявлено несоответствие"
        agreement_proof = target_kind == "VERIFIED_OK" and proof_route == "INDEPENDENT_AGREEMENT"
        conflict_proof = target_kind == "PROJECT_FINDING" and proof_route == "INDEPENDENT_CONFLICT"
        row.update({
            "final_verification_kind": target_kind,
            "final_verification_state": state,
            "verification_kind": target_kind,
            "verification_state": state,
            "proof_kind": (
                "STRUCTURED_AGREEMENT" if agreement_proof
                else "STRUCTURED_CONFLICT" if conflict_proof
                else "STRUCTURED_COMPARISON"
            ),
            "evidence_level": "L5",
            "evidence_level_reason": (
                "Совпадение подтверждено двумя независимыми доверенными источниками при завершённой канонической привязке."
                if agreement_proof
                else "Конфликт подтверждён двумя независимыми доверенными источниками; правильное значение требует owner-раздела."
                if conflict_proof
                else "Подтверждены объект, показатель, единица и независимый маршрут владелец→контроль."
            ),
            "adversarial_state": "PASSED",
            "deep_evidence_state": "PASSED",
            "automatic_verdict_eligible": True,
            "candidate_evidence_only": False,
            "coverage_state": "AUTOMATED_COMPLETE" if target_kind == "VERIFIED_OK" else "PROJECT_FINDING_CONFIRMED",
            "coverage_reason_code": (
                "CROSS_SECTION_INDEPENDENT_AGREEMENT"
                if agreement_proof
                else "CROSS_SECTION_INDEPENDENT_CONFLICT"
                if conflict_proof
                else "CROSS_SECTION_PROOF_GATE_PASSED"
            ),
            "coverage_reason": (
                "Два независимых доверенных раздела подтверждают одно значение одного объекта и показателя."
                if agreement_proof
                else "Два независимых доверенных раздела подтверждают конфликт значений одного объекта и показателя."
                if conflict_proof
                else "Строгая детерминированная межраздельная проверка завершена."
            ),
            "conflict_confirmed": bool(conflict_proof or target_kind == "PROJECT_FINDING"),
            "correct_value_verified": bool(target_kind != "PROJECT_FINDING" or (owner_present and control_present)),
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
