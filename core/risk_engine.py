from __future__ import annotations

from typing import Any


PRIORITY_WEIGHT = {"Высокий": 3, "Средний": 2, "Низкий": 1}


def calculate_engineering_risk(comparison: dict[str, Any]) -> dict[str, Any]:
    """Transparent engineering risk score; not a probability of receiving a remark."""
    result = str(comparison.get("result") or comparison.get("Результат") or "").lower()
    priority = str(comparison.get("priority") or comparison.get("Приоритет") or "Средний")
    evidence_projects = int(comparison.get("knowledge_project_count") or 0)
    evidence_remarks = int(comparison.get("knowledge_evidence_count") or 0)

    score = 0
    reasons: list[str] = []
    if "расхожд" in result or "несоответ" in result:
        score += 45
        reasons.append("выявлено межраздельное расхождение")
    elif "уточнен" in result or "недостат" in result:
        score += 20
        reasons.append("результат требует уточнения")

    score += PRIORITY_WEIGHT.get(priority, 2) * 8
    reasons.append(f"приоритет правила: {priority}")

    if evidence_projects >= 3:
        score += 20
        reasons.append(f"аналогичный класс риска подтверждён в {evidence_projects} проектах")
    elif evidence_projects >= 1:
        score += min(12, 4 * evidence_projects)
        reasons.append(f"есть подтверждения в {evidence_projects} проектах")

    if evidence_remarks >= 5:
        score += 8
        reasons.append(f"в базе знаний {evidence_remarks} связанных замечаний")

    score = min(100, score)
    if score >= 70:
        level = "Высокий"
    elif score >= 40:
        level = "Средний"
    elif score > 0:
        level = "Низкий"
    else:
        level = "Нет данных"
    return {"score": score, "level": level, "reasons": reasons}
