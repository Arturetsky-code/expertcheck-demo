from __future__ import annotations

from collections import Counter
from typing import Any


def _text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", []):
            return str(value)
    return ""


def _level(score: int) -> str:
    if score >= 70:
        return "Высокий"
    if score >= 40:
        return "Средний"
    if score > 0:
        return "Низкий"
    return "Недостаточно данных"


def _possible_remark(kind: str, object_name: str, parameter: str) -> str:
    obj = object_name or "объекту"
    if kind == "object_gap":
        return f"Не обеспечено соответствие состава проектируемых объектов между разделами проектной документации по позиции «{obj}»."
    if kind == "mismatch":
        return f"Не обеспечена согласованность технико-экономического показателя «{parameter}» по объекту «{obj}» между разделами проектной документации."
    if kind == "insufficient":
        return f"Не представлены достаточные и однозначные сведения по показателю «{parameter}» объекта «{obj}» для подтверждения принятого проектного решения."
    if kind == "checklist":
        return f"Не подтверждено выполнение контрольного требования по пункту «{parameter}»."
    return "Требуется дополнительная проверка согласованности и полноты проектных решений."


def build_expert_risks(
    comparisons: list[dict[str, Any]],
    object_rows: list[dict[str, Any]] | None = None,
    checklist_results: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    object_rows = object_rows or []
    checklist_results = checklist_results or []

    for index, row in enumerate(comparisons):
        status = _text(row, "status", "Статус", "result", "Результат").lower()
        if not any(token in status for token in ("расхожд", "конфликт", "недостат", "требует", "отсутств")):
            continue
        obj = _text(row, "object", "Объект", "object_name")
        parameter = _text(row, "parameter_name", "parameter", "Параметр", "parameter_code") or "показатель"
        priority = _text(row, "priority", "Приоритет") or "Средний"
        kind = "mismatch" if any(token in status for token in ("расхожд", "конфликт")) else "insufficient"
        score = int(row.get("engineering_risk_score") or 0)
        if not score:
            score = 52 if kind == "mismatch" else 34
            if priority.lower().startswith("выс"):
                score += 18
            elif priority.lower().startswith("низ"):
                score -= 8
        sources = row.get("sources") or row.get("Источники") or row.get("sections") or row.get("document_values") or ""
        explanation = _text(row, "explanation", "Пояснение")
        risks.append({
            "risk_id": _text(row, "comparison_id", "rule_id", "check_code") or f"R-CMP-{index+1:04d}",
            "level": _level(min(100, score)),
            "score": min(100, score),
            "category": "Межраздельная согласованность" if kind == "mismatch" else "Полнота и доказательность",
            "object": obj,
            "parameter": parameter,
            "finding": explanation or f"Результат проверки: {_text(row, 'status', 'Статус', 'result', 'Результат')}",
            "possible_remark": _possible_remark(kind, obj, parameter),
            "recommendation": "Проверить исходные страницы и унифицировать сведения во всех связанных разделах." if kind == "mismatch" else "Дополнить сведения либо подтвердить показатель однозначным источником с указанием объекта и страницы.",
            "sources": sources,
            "origin": "CrossCheck Engine",
        })

    for index, row in enumerate(object_rows):
        included = bool(row.get("Включить в состав проекта", row.get("include", False)))
        decision = _text(row, "Решение Object Intelligence", "object_intelligence_decision", "decision").lower()
        status = _text(row, "Статус проектирования", "design_status", "status").lower()
        name = _text(row, "Наименование", "Объект", "name", "value_text")
        if included and decision in {"review", "blocked", "context"}:
            score = 68 if decision == "blocked" else 48
            risks.append({
                "risk_id": f"R-OBJ-{index+1:04d}",
                "level": _level(score),
                "score": score,
                "category": "Состав проекта",
                "object": name,
                "parameter": "Принадлежность к составу проекта",
                "finding": f"Позиция включена пользователем, хотя автоматическое решение Core: {decision or 'не определено'}; статус: {status or 'не определён'}.",
                "possible_remark": _possible_remark("object_gap", name, ""),
                "recommendation": "Проверить официальный источник: состав сложного объекта, XML или экспликацию генплана.",
                "sources": row.get("Основание включения") or row.get("Канонический источник") or "",
                "origin": "Project Engine",
            })

    for index, row in enumerate(checklist_results):
        status = _text(row, "status", "Соответствие", "result").lower()
        if status not in {"нет", "частично", "требует проверки", "нет данных", "не соответствует"}:
            continue
        item_no = _text(row, "item_no", "Позиция", "position")
        question = _text(row, "question", "Вопрос", "Позиция по чек-листу")
        score = 58 if status in {"нет", "не соответствует"} else 32
        risks.append({
            "risk_id": f"R-CHK-{index+1:04d}",
            "level": _level(score),
            "score": score,
            "category": "Чек-лист раздела",
            "object": "",
            "parameter": f"{item_no} {question}".strip(),
            "finding": _text(row, "evidence", "Обоснование") or f"Результат пункта: {status}",
            "possible_remark": _possible_remark("checklist", "", f"{item_no} {question}".strip()),
            "recommendation": "Открыть доказательства по пункту, дополнить раздел и повторно запустить проверку чек-листа.",
            "sources": _text(row, "sources", "Источники"),
            "origin": "Checklist Engine",
        })

    # deterministic ordering and duplicate suppression
    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for risk in risks:
        key = (risk["category"], risk["object"].lower(), risk["parameter"].lower())
        current = unique.get(key)
        if current is None or int(risk["score"]) > int(current["score"]):
            unique[key] = risk
    return sorted(unique.values(), key=lambda item: (-int(item["score"]), item["category"], item["object"]))


def summarize_risks(risks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(item.get("level") or "Недостаточно данных") for item in risks)
    return {
        "total": len(risks),
        "high": counts.get("Высокий", 0),
        "medium": counts.get("Средний", 0),
        "low": counts.get("Низкий", 0),
        "categories": dict(Counter(str(item.get("category") or "Прочее") for item in risks)),
    }
