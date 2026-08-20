from __future__ import annotations
from typing import Any


def _safe_int(value: Any, default: int = 0) -> int:
    """Accept int/float/numeric strings incl. comma decimal; never raise on UI/report data."""
    if value is None or value == "":
        return default
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(str(value).strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")))
    except (TypeError, ValueError, OverflowError):
        return default


def qualify_comparison(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("status") or row.get("Статус") or "").lower()
    trusted = _safe_int(row.get("independent_trusted_sources"), 0)
    sections = _safe_int(row.get("independent_section_count"), 0)
    source_text = str(row.get("sources") or row.get("document_values") or "").strip()

    if "расхожд" in status or "конфликт" in status:
        if trusted >= 2 and sections >= 2 and source_text:
            return {"finding_class":"CONFIRMED_ISSUE","user_status":"Выявлено несоответствие","finding_type":"PROJECT_FINDING","risk_eligible":True,"max_risk_level":"Высокий","reason":"Есть независимые доверенные доказательства из нескольких разделов."}
        return {"finding_class":"REVIEW","user_status":"Требует проверки","finding_type":"REVIEW_QUESTION","risk_eligible":True,"max_risk_level":"Средний","reason":"Есть различие, но недостаточно независимых доверенных доказательств."}
    if any(x in status for x in ("недостат", "нет данных", "не подтвержд", "отсутств")):
        return {"finding_class":"INSUFFICIENT_DATA","user_status":"Недостаточно данных","finding_type":"SYSTEM_LIMITATION","risk_eligible":False,"max_risk_level":"Недостаточно данных","reason":"Отсутствие найденного подтверждения не доказывает отсутствие сведений в проекте."}
    if "требует" in status:
        return {"finding_class":"REVIEW","user_status":"Требует проверки","finding_type":"REVIEW_QUESTION","risk_eligible":False,"max_risk_level":"Низкий","reason":"Диагностический статус требует проверки специалистом и сам по себе не является замечанием."}
    return {"finding_class":"OK","user_status":"Проверено","finding_type":"PROJECT_STATUS","risk_eligible":False,"max_risk_level":"Недостаточно данных","reason":"Оснований для риска нет."}


def qualify_checklist(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("status") or row.get("Соответствие") or row.get("result") or "").lower().strip()
    evidence = str(row.get("evidence") or row.get("Обоснование") or "").lower()
    sources = str(row.get("sources") or row.get("Источники") or "").strip()
    explicit_negative = status in {"нет", "не соответствует"}
    diagnostic_language = any(x in evidence for x in (
        "автоматически не выяв", "недостаточно", "без ai", "требуется провер", "не удалось проверить", "не найдено доказательств", "не найдено достаточ"
    ))
    if explicit_negative and sources and not diagnostic_language:
        return {"finding_class":"CONFIRMED_ISSUE","user_status":"Выявлено несоответствие","finding_type":"PROJECT_FINDING","risk_eligible":True,"max_risk_level":"Средний","reason":"Отрицательный результат подтверждён конкретным источником."}
    if explicit_negative and not diagnostic_language:
        return {"finding_class":"REVIEW","user_status":"Требует проверки","finding_type":"REVIEW_QUESTION","risk_eligible":False,"max_risk_level":"Низкий","reason":"Отрицательный результат без конкретного доказательного источника не допускается в реестр рисков."}
    if explicit_negative:
        return {"finding_class":"UNVERIFIED_BY_SYSTEM","user_status":"Не проверено системой","finding_type":"SYSTEM_LIMITATION","risk_eligible":False,"max_risk_level":"Недостаточно данных","reason":"Отрицательный статус получен только потому, что автоматический алгоритм не нашёл достаточных доказательств."}
    if status in {"частично", "требует проверки", "нет данных", "не проверено системой"}:
        return {"finding_class":"UNVERIFIED_BY_SYSTEM","user_status":"Не проверено системой","finding_type":"SYSTEM_LIMITATION","risk_eligible":False,"max_risk_level":"Недостаточно данных","reason":"Пункт требует специалиста или более сильного алгоритма проверки."}
    return {"finding_class":"OK","user_status":"Проверено","finding_type":"PROJECT_STATUS","risk_eligible":False,"max_risk_level":"Недостаточно данных","reason":"Оснований для риска нет."}


def coverage_summary(comparisons: list[dict[str, Any]], checklist: list[dict[str, Any]]) -> dict[str, Any]:
    rows=[]
    for row in comparisons or []:
        rows.append(qualify_comparison(row)["finding_class"])
    for row in checklist or []:
        rows.append(qualify_checklist(row)["finding_class"])
    total=len(rows)
    counts={k:rows.count(k) for k in {"CONFIRMED_ISSUE","REVIEW","INSUFFICIENT_DATA","UNVERIFIED_BY_SYSTEM","OK"}}
    automated=counts["CONFIRMED_ISSUE"]+counts["OK"]
    partial=counts["REVIEW"]+counts["INSUFFICIENT_DATA"]
    unsupported=counts["UNVERIFIED_BY_SYSTEM"]
    return {
        "total":total,
        "automatic_pct":round(automated/max(1,total)*100,1),
        "partial_pct":round(partial/max(1,total)*100,1),
        "requires_specialist_pct":round(unsupported/max(1,total)*100,1),
        "classes":counts,
    }
