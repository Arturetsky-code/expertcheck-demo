from __future__ import annotations

from typing import Any, Iterable


def summarize_object_registry(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    included = [r for r in rows if r.get("Включить")]
    blocked = [r for r in rows if r.get("Решение Object Intelligence") == "blocked" or r.get("Блокировка")]
    review = [r for r in rows if r.get("Решение Object Intelligence") == "review"]
    weak = [r for r in rows if int(r.get("Доверие Object Intelligence") or 0) < 70 and not r.get("Блокировка")]
    return {
        "total": len(rows),
        "included": len(included),
        "blocked": len(blocked),
        "review": len(review),
        "weak": len(weak),
    }


def answer_local_question(question: str, rows: Iterable[dict[str, Any]], comparisons: Iterable[dict[str, Any]]) -> str:
    q = (question or "").lower()
    rows = list(rows)
    comparisons = list(comparisons)
    if any(token in q for token in ("подозр", "лишн", "мусор", "файл")):
        suspects = [r for r in rows if r.get("Блокировка") or r.get("Решение Object Intelligence") in {"blocked", "review"}]
        if not suspects:
            return "Подозрительных позиций по текущим правилам не найдено."
        lines = ["Позиции, требующие внимания:"]
        for r in suspects[:20]:
            lines.append(f"• {r.get('Позиция по ГП') or '—'} {r.get('Наименование объекта')}: {r.get('Обоснование Object Intelligence') or r.get('Блокировка') or 'недостаточно доказательств'}")
        return "\n".join(lines)
    if any(token in q for token in ("почему", "источник", "доказатель")):
        return "Откройте объект в разделе «Объекты → Доказательства происхождения». Там показаны документ, страница, раздел/пункт, таблица, строка и причина включения или блокировки."
    if any(token in q for token in ("расхожд", "сверк", "тэп")):
        bad = [c for c in comparisons if any(t in str(c.get("status") or "").lower() for t in ("расхожд", "конфликт", "уточн"))]
        return f"Результатов, требующих внимания: {len(bad)}. Межраздельная сверка разрешается только после подтверждения объектного реестра."
    summary = summarize_object_registry(rows)
    return (
        f"Найдено кандидатов: {summary['total']}; предложено включить: {summary['included']}; "
        f"заблокировано: {summary['blocked']}; требуют ручного решения: {summary['review']}."
    )
