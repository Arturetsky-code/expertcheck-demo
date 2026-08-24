from __future__ import annotations

from collections import Counter
from typing import Any
from .global_finding_gate import classify_finding


def _group(status: Any) -> str:
    text = str(status or "").upper()
    if "РАСХОЖД" in text or "КОНФЛИКТ" in text or "НЕ СООТВЕТ" in text:
        return "high"
    if any(token in text for token in ("НЕДОСТАТОЧ", "УТОЧ", "НЕ ПОДТВЕРЖ", "ТРЕБУЕТ", "НЕТ ДАННЫХ", "ЧАСТИЧНО", "ПРЕДВАРИТ", "КАНДИДАТ")):
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
    finding_class_counts=Counter()
    system_limitations=[]
    review_questions=[]
    project_findings=[]
    for index, row in enumerate(comparisons):
        gate=classify_finding(row,source_kind="comparison")
        finding_class_counts[gate.get("finding_type") or "INFORMATIONAL"] += 1
        if gate.get("finding_type")=="SYSTEM_LIMITATION":
            system_limitations.append(dict(row, global_finding_reason=gate.get("reason")))
            continue
        if gate.get("finding_type")=="REVIEW_QUESTION":
            review_questions.append(dict(row, global_finding_reason=gate.get("reason")))
        if gate.get("finding_type")=="PROJECT_FINDING":
            project_findings.append(dict(row, global_finding_reason=gate.get("reason")))
        if not gate.get("report_eligible"):
            continue
        level = _group(row.get("status") or row.get("result"))
        counts[level] += 1
        if level not in {"high", "medium"}:
            level="medium"
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
    # Finding Continuity Gate: a verified internal conflict in Project Understanding
    # cannot silently disappear merely because a downstream comparison row was lost.
    pu=(first.get('project_understanding') or {}) if isinstance(first,dict) else {}
    existing_keys={(str(x.get('object') or '').lower(),str(x.get('parameter') or '').lower()) for x in problems}
    for obj in pu.get('objects') or []:
        for prop in obj.get('property_summary') or []:
            if not prop.get('value_conflict'): continue
            sections=list(prop.get('sections') or [])
            if len(sections)<2: continue
            key=(str(obj.get('name') or '').lower(),str(prop.get('parameter_name') or '').lower())
            if key in existing_keys: continue
            vals=' | '.join(str(v) for v in (prop.get('values') or []))
            problems.append({
                'id':f"PU-CONFLICT-{len(problems)+1:03d}", 'object':obj.get('name') or 'Объект не определён',
                'parameter':prop.get('parameter_name') or prop.get('parameter_code') or 'Показатель',
                'status':'РАСХОЖДЕНИЕ', 'priority':'Высокий', 'values':vals,
                'explanation':'Модель проекта содержит разные структурированные значения одного показателя из нескольких разделов. Требуется проверить и согласовать исходные данные.',
                'sources':', '.join(sections), 'finding_type':'PROJECT_FINDING', 'continuity_source':'PROJECT_UNDERSTANDING'
            })
            project_findings.append(problems[-1]); finding_class_counts['PROJECT_FINDING'] += 1; counts['high'] += 1
            existing_keys.add(key)

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
        for row in registry:
            name=_text(row,"name","object_name","value_text","Наименование объекта","Наименование")
            position=_text(row,"position","position_gp","Позиция","Позиция по ГП")
            if not (name or position):
                continue
            source=_text(row,"canonical_source","source","Источники","Основной источник","pz_document","general_plan_document")
            compact={
                "position":position,"name":name,
                "status":_text(row,"design_status","status","Статус") or ("Подтверждён" if source else "Требует подтверждения источника"),
                "source":source or "Источник не подтверждён",
            }
            (confirmed_objects if source else unresolved_objects).append(compact)

    # Object Confirmation Model: if the UI assembly has not yet persisted inclusion flags,
    # the conservative Project Understanding registry is still a valid model count.
    if not confirmed_objects and not unresolved_objects:
        pu=(first.get("project_understanding") or {}) if isinstance(first,dict) else {}
        for obj in pu.get("objects") or []:
            if not obj.get("name"): continue
            physical_source=str(obj.get('source_lineage_status') or '')=='VERIFIED_SOURCE'
            compact={
                "position":str(obj.get("position") or ""),"name":str(obj.get("name") or ""),
                "status":"Подтверждено источником" if physical_source else "Требует подтверждения источника",
                "source":str(obj.get("sources") or "Источник не подтверждён"),
            }
            (confirmed_objects if physical_source else unresolved_objects).append(compact)

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
            # ``objects`` remains the compatibility total; management reports
            # must use ``objects_confirmed`` and show unresolved separately.
            "objects": len(confirmed_objects)+len(unresolved_objects),
            "objects_confirmed":len(confirmed_objects),
            "objects_unresolved":len(unresolved_objects),
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
            "project_findings": finding_class_counts.get("PROJECT_FINDING",0),
            "review_questions": finding_class_counts.get("REVIEW_QUESTION",0),
            "system_limitations": finding_class_counts.get("SYSTEM_LIMITATION",0),
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
            "system_limitations": system_limitations,
            "review_questions": review_questions,
            "project_findings": project_findings,
        },
    }


def build_decision_report(documents: list[dict[str, Any]], comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    """Backward-compatible compact report model."""
    return build_structured_report("Проект", documents, comparisons)
