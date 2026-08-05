from __future__ import annotations

from collections import Counter
from typing import Any


def _group(status: Any) -> str:
    text = str(status or "").upper()
    if "РАСХОЖД" in text or "КОНФЛИКТ" in text:
        return "high"
    if "НЕДОСТАТОЧ" in text or "УТОЧ" in text or "НЕ ПОДТВЕРЖ" in text:
        return "medium"
    if "СОВПАД" in text or "ПОДТВЕРЖ" in text:
        return "ok"
    return "info"


def build_decision_report(documents: list[dict[str, Any]], comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    """Формирует короткий отчет для принятия решений, а не отладочную выгрузку."""
    first = documents[0] if documents else {}
    registry = list(first.get("consolidated_registry") or [])
    problems = []
    counts = Counter()
    for row in comparisons:
        level = _group(row.get("status"))
        counts[level] += 1
        if level not in {"high", "medium"}:
            continue
        problems.append({
            "object": row.get("object") or "Объект не определён",
            "parameter": row.get("parameter_name") or row.get("rule_name") or "Проверка",
            "status": row.get("status") or "Требует проверки",
            "priority": "Высокий" if level == "high" else "Средний",
            "values": row.get("document_values") or row.get("documents") or "",
            "explanation": row.get("explanation") or "Проверьте исходные значения и актуальность разделов.",
            "sources": row.get("sources") or "",
        })
    problems.sort(key=lambda x: (x["priority"] != "Высокий", x["object"], x["parameter"]))
    completeness = "Подтверждена" if first.get("completeness_user_confirmed") else "Не подтверждена"
    return {
        "summary": {
            "documents": len(documents),
            "objects": len(registry),
            "checks": len(comparisons),
            "confirmed": counts["ok"],
            "requires_attention": counts["high"] + counts["medium"],
            "high_priority": counts["high"],
            "medium_priority": counts["medium"],
            "completeness": completeness,
        },
        "problems": problems,
        "recommendations": [
            f"Проверить {p['parameter'].lower()} для объекта «{p['object']}»."
            for p in problems[:12]
        ],
    }
