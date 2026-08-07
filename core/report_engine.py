from __future__ import annotations

from collections import Counter
from typing import Any


def _group(status: Any) -> str:
    text = str(status or "").upper()
    if "РАСХОЖД" in text or "КОНФЛИКТ" in text or "НЕ СООТВЕТ" in text:
        return "high"
    if any(token in text for token in ("НЕДОСТАТОЧ", "УТОЧ", "НЕ ПОДТВЕРЖ", "ТРЕБУЕТ", "НЕТ ДАННЫХ", "ЧАСТИЧНО")):
        return "medium"
    if "СОВПАД" in text or "ПОДТВЕРЖ" in text or text.strip() == "ДА":
        return "ok"
    return "info"


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", []):
            return str(value)
    return ""


def _checklist_summary(checklist_results: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in checklist_results:
        status = _text(row, "status", "Соответствие", "result").strip().lower()
        if status in {"да", "соответствует"}:
            counts["yes"] += 1
        elif status in {"нет", "не соответствует"}:
            counts["no"] += 1
        elif status == "частично":
            counts["partial"] += 1
        elif status in {"требует проверки", "нет данных", "не рассмотрено"}:
            counts["review"] += 1
    counts["total"] = sum(counts.values())
    return dict(counts)


def build_structured_report(
    project_name: str,
    documents: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    risks: list[dict[str, Any]] | None = None,
    checklist_results: list[dict[str, Any]] | None = None,
    assembly_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Builds a concise management report plus a separate technical appendix model."""
    risks = risks or []
    checklist_results = checklist_results or []
    assembly_rows = assembly_rows or []
    first = documents[0] if documents else {}
    registry = list(first.get("consolidated_registry") or [])

    problems: list[dict[str, Any]] = []
    counts = Counter()
    for index, row in enumerate(comparisons):
        level = _group(row.get("status") or row.get("result"))
        counts[level] += 1
        if level not in {"high", "medium"}:
            continue
        problems.append({
            "id": _text(row, "comparison_id", "check_code", "rule_id") or f"XCHK-{index+1:03d}",
            "object": _text(row, "object", "Объект", "object_name") or "Объект не определён",
            "parameter": _text(row, "parameter_name", "rule_name", "parameter", "Параметр") or "Проверка",
            "status": _text(row, "status", "result", "Результат") or "Требует проверки",
            "priority": "Высокий" if level == "high" else "Средний",
            "values": row.get("document_values") or row.get("documents") or row.get("values") or "",
            "explanation": _text(row, "explanation", "Пояснение") or "Проверьте исходные значения и актуальность разделов.",
            "sources": row.get("sources") or row.get("sections") or "",
        })
    # Один инженерный вопрос — одна строка в стандартном отчёте.
    deduped = {}
    for item in problems:
        key = (item["object"].strip().lower(), item["parameter"].strip().lower(), item["status"].strip().lower())
        if key not in deduped:
            deduped[key] = item
    problems = list(deduped.values())
    problems.sort(key=lambda x: (x["priority"] != "Высокий", x["object"], x["parameter"]))

    high_risks = [r for r in risks if str(r.get("level")) == "Высокий"]
    medium_risks = [r for r in risks if str(r.get("level")) == "Средний"]
    low_risks = [r for r in risks if str(r.get("level")) == "Низкий"]
    checklist_summary = _checklist_summary(checklist_results)

    confirmed_objects = []
    excluded_objects = []
    unresolved_objects = []
    if assembly_rows:
        for row in assembly_rows:
            name = _text(row, "Наименование", "Объект", "name", "value_text")
            include = bool(row.get("Включить в состав проекта", row.get("include", False)))
            decision = _text(row, "Решение Object Intelligence", "decision", "object_intelligence_decision").lower()
            compact = {
                "position": _text(row, "Позиция", "position", "position_gp"),
                "name": name,
                "status": _text(row, "Статус проектирования", "design_status", "status") or "Не определён",
                "source": _text(row, "Основной источник", "Канонический источник", "Основание включения", "canonical_source"),
            }
            if include:
                confirmed_objects.append(compact)
            elif decision in {"review", "", "unknown"}:
                unresolved_objects.append(compact)
            else:
                excluded_objects.append(compact)
    else:
        confirmed_objects = [{
            "position": _text(row, "position", "position_gp"),
            "name": _text(row, "name", "object_name", "value_text"),
            "status": _text(row, "design_status", "status") or "Подтверждён",
            "source": _text(row, "canonical_source", "source"),
        } for row in registry]

    recommendations: list[str] = []
    for risk in high_risks + medium_risks:
        text = _text(risk, "recommendation")
        if text and text not in recommendations:
            recommendations.append(text)
    for p in problems:
        text = f"Проверить показатель «{p['parameter']}» по объекту «{p['object']}» и согласовать сведения между разделами."
        if text not in recommendations:
            recommendations.append(text)
    recommendations = recommendations[:10]

    if high_risks:
        conclusion = f"Выявлено {len(high_risks)} вопрос(а) высокого риска. Рекомендуется устранить их до передачи документации на экспертизу."
    elif problems:
        conclusion = f"Выявлено {len(problems)} результат(а), требующих инженерной проверки и уточнения исходных данных."
    else:
        conclusion = "Критические межраздельные расхождения по доступным структурированным данным не выявлены. Требуется завершить ручную проверку применимых пунктов чек-листов."

    return {
        "project": project_name,
        "summary": {
            "documents": len(documents),
            "objects": len(confirmed_objects),
            "checks": len(comparisons),
            "confirmed": counts["ok"],
            "requires_attention": counts["high"] + counts["medium"],
            "high_priority": counts["high"],
            "medium_priority": counts["medium"],
            "completeness": "Подтверждена" if first.get("completeness_user_confirmed") else "Не подтверждена",
            "risks_high": len(high_risks),
            "risks_medium": len(medium_risks),
            "risks_low": len(low_risks),
            "checklist_total": checklist_summary.get("total", 0),
            "checklist_no": checklist_summary.get("no", 0),
            "checklist_review": checklist_summary.get("review", 0) + checklist_summary.get("partial", 0),
        },
        "conclusion": conclusion,
        "problems": problems,
        "risks": risks,
        "confirmed_objects": confirmed_objects,
        "excluded_objects": excluded_objects,
        "unresolved_objects": unresolved_objects,
        "checklist_results": checklist_results,
        "checklist_summary": checklist_summary,
        "recommendations": recommendations,
        "technical": {
            "documents": documents,
            "comparisons": comparisons,
            "registry": registry,
            "assembly_rows": assembly_rows,
        },
    }


def build_decision_report(documents: list[dict[str, Any]], comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    """Backward-compatible compact report model."""
    return build_structured_report("Проект", documents, comparisons)
