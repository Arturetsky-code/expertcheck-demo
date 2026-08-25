from __future__ import annotations

from typing import Any

from .general_plan_engine import is_service_role_label
from .page_evidence_store import section_matches, source_section


def validate_review_plan(
    plan: dict[str, Any],
    *,
    object_registry: list[dict[str, Any]] | None = None,
    checklist_rows: list[dict[str, Any]] | None = None,
    comparisons: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate report metrics before they become management conclusions."""
    issues: list[str] = []
    domains = plan.get("domains") or {}
    checked_domains = 0
    for code in ("assignment", "normative", "checklist"):
        summary = domains.get(code) or {}
        if not summary:
            issues.append(f"Отсутствует сводка контура {code}.")
            continue
        checked_domains += 1
        total = int(summary.get("total") or 0)
        verified = int(summary.get("verified_ok") or summary.get("confirmed") or 0)
        findings = int(summary.get("project_findings") or summary.get("issue") or 0)
        review = int(summary.get("review_questions") or summary.get("review") or 0)
        limitations = int(summary.get("system_limitations") or summary.get("system_limitation") or 0)
        informational = int(summary.get("informational") or 0)
        completed = int(summary.get("completed") or 0)
        if completed != verified + findings:
            issues.append(f"{code}: completed не равен confirmed + findings.")
        if total != verified + findings + review + limitations + informational:
            issues.append(f"{code}: сумма классов результатов не равна total.")
        expected = round(100 * completed / max(1, total), 1)
        actual = round(float(summary.get("automatic_coverage_pct", summary.get("coverage_pct", 0)) or 0), 1)
        if actual != expected:
            issues.append(f"{code}: покрытие {actual}% не соответствует {completed}/{total} ({expected}%).")

    for item in plan.get("items") or []:
        status = str(item.get("status") or "").lower()
        title = str(item.get("title") or item.get("plan_id") or "проверка")[:100]
        if "предварительно" in status and item.get("verification_kind") == "VERIFIED_OK":
            issues.append(f"Предварительный результат ошибочно подтверждён: {title}.")
        if item.get("verification_kind") == "VERIFIED_OK" and item.get("adversarial_state") == "BLOCKED":
            issues.append(f"Заблокированный adversarial gate результат остался подтверждённым: {title}.")
        if item.get("verification_kind") == "PROJECT_FINDING" and item.get("adversarial_state") == "BLOCKED":
            issues.append(f"Заблокированный adversarial gate результат остался несоответствием: {title}.")
        if item.get("verification_kind") in {"VERIFIED_OK", "PROJECT_FINDING"}:
            if item.get("adversarial_state") != "PASSED":
                issues.append(f"Категоричный вывод не имеет пройденной проверки достаточности: {title}.")
            if int(item.get("evidence_candidate_count") or 0) <= 0:
                issues.append(f"Категоричный вывод не имеет адресного доказательства: {title}.")
        recommendation = str(item.get("recommendation") or "").lower()
        if item.get("verification_kind") == "REVIEW_QUESTION" and "дополнительное действие не требуется" in recommendation:
            issues.append(f"Вопрос специалисту ошибочно помечен как не требующий действия: {title}.")

    for row in object_registry or []:
        name = str(row.get("Наименование объекта") or row.get("Наименование") or row.get("name") or "").strip()
        if name and is_service_role_label(name):
            issues.append(f"В реестр объектов попала служебная роль основной надписи: {name[:100]}.")
        low=name.lower()
        if any(token in low for token in ('ethernet tx','ethernet fx','usb кабель','vga кабель','условные обозначения')):
            issues.append(f"В реестр объектов попала строка легенды/соединения: {name[:100]}.")

    wrong_section=0
    for row in checklist_rows or []:
        if str(row.get('final_verification_kind') or row.get('verification_kind') or '').upper()=='VERIFIED_OK':
            typed=str(row.get('typed_check') or (row.get('compiled_rule') or {}).get('typed_check') or '').upper()
            if typed in {'SPECIALIST_REVIEW','ENGINEERING_SEMANTIC_REVIEW','NORMATIVE_CONTENT_REVIEW'}:
                issues.append(
                    f"Чек-лист {row.get('item_no') or row.get('position') or ''}: экспертный тип {typed} ошибочно закрыт автоматически."
                )
            if row.get('automatic_verdict_eligible') is False or row.get('candidate_evidence_only'):
                issues.append(
                    f"Чек-лист {row.get('item_no') or row.get('position') or ''}: поисковый кандидат ошибочно стал категоричным выводом."
                )
        expected=[row.get('automatic_section')] if row.get('automatic_section') else []
        if not expected:
            continue
        for evidence in row.get('deep_evidence_candidates') or []:
            if not section_matches(source_section(evidence),expected):
                wrong_section+=1
                if wrong_section<=5:
                    issues.append(
                        f"Чек-лист {row.get('item_no') or row.get('position') or ''}: доказательство из раздела "
                        f"{source_section(evidence) or 'не определён'} не соответствует {expected[0]}."
                    )
    if wrong_section>5:
        issues.append(f"Дополнительно обнаружено нерелевантных источников чек-листов: {wrong_section-5}.")

    for row in comparisons or []:
        status=str(row.get('status') or row.get('result') or '').upper()
        if not any(token in status for token in ('СОВПАД','РАСХОЖД','КОНФЛИКТ')):
            continue
        parameter=str(row.get('parameter_name') or row.get('parameter') or row.get('rule_name') or '').strip()
        values=row.get('document_values') or row.get('values_by_section') or row.get('values')
        if not parameter:
            issues.append('Завершённая межраздельная сверка не содержит наименование показателя.')
        if not values and str(row.get('parameter_code') or '').upper() not in {'GP_EXPLICATION_FIELD','GP_DOCUMENT_COVERAGE'}:
            issues.append(f"Межраздельная сверка «{parameter or 'без показателя'}» не содержит сопоставленные значения.")

    return {
        "status": "PASSED" if not issues and checked_domains == 3 else "FAILED",
        "issues": issues,
        "checked_domains": checked_domains,
        "checks": len(plan.get("items") or []),
        "checked_objects": len(object_registry or []),
        "wrong_section_evidence": wrong_section,
    }
