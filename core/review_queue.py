from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any, Iterable

from .normalization import normalize_text


LEVEL_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
MAX_CLUSTER_SIZE = 12
_TOPIC_STOPWORDS = {
    "проверить", "проверка", "наличие", "соответствие", "проектной", "документации",
    "раздел", "часть", "должен", "должна", "должны", "представлен", "приведен",
    "приведена", "указан", "выполнен", "предусмотрен", "требования", "содержать",
}


def _value(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _level(row: dict[str, Any]) -> str:
    raw = _value(row, "evidence_level", "Уровень доказательства").upper()
    match = re.search(r"L[0-5]", raw)
    return match.group(0) if match else "L0"


def _priority(items: list[dict[str, Any]]) -> str:
    level = max((LEVEL_RANK.get(_level(item), 0) for item in items), default=0)
    blob = normalize_text(" ".join(_value(item, "Причина", "coverage_reason", "reason") for item in items))
    domain = normalize_text(_value(items[0], "Контур", "domain")) if items else ""
    if level >= 4 or any(token in blob for token in ("противореч", "критическ", "конфликт")):
        return "Высокий"
    if level >= 2 or domain in {"задание на проектирование", "нтд", "межраздельная сверка"}:
        return "Средний"
    return "Низкий"


def _topic(row: dict[str, Any]) -> str:
    text = normalize_text(_value(row, "Проверка", "title", "question", "parameter"))
    topic_rules = (
        (("расчет", "расчёт", "баланс"), "Расчёты и балансы"),
        (("чертеж", "чертёж", "план", "схем", "разрез", "фасад"), "Графические материалы"),
        (("комплект", "состав", "содержание", "перечень", "ведомост"), "Состав и комплектность"),
        (("площад", "объем", "объём", "высот", "длин", "ширин", "мощност", "производительност"), "Числовые показатели"),
        (("пожар", "эвакуац", "безопасност", "охрана труда"), "Безопасность"),
        (("норматив", "гост", "сп ", "федеральн"), "Нормативные требования"),
        (("заземл", "молниезащ", "электроснаб", "кабель"), "Электротехнические решения"),
        (("водоснаб", "водоотвед", "канализац", "насосн"), "Водоснабжение и водоотведение"),
    )
    for markers, label in topic_rules:
        if any(marker in text for marker in markers):
            return label
    words = [
        word for word in re.findall(r"[a-zа-я0-9-]{4,}", text, re.I)
        if word not in _TOPIC_STOPWORDS and not word.isdigit()
    ]
    return " ".join(words[:3]).capitalize() or "Общая проверка"


def build_review_clusters(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse an auditable detail queue into actionable specialist work packages.

    Detailed questions are never removed.  Clusters are a navigation layer for
    the GIP/manager and must not be counted as completed checks.
    """
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for raw in rows or []:
        row = dict(raw)
        domain = _value(row, "Контур", "domain") or "Не определён"
        entity = _value(row, "Объект", "entity", "object") or "—"
        route = _value(row, "Ожидаемые разделы", "expected_sections", "scope") or "—"
        reason = _value(row, "Код причины", "coverage_reason_code", "Причина", "coverage_reason") or "Требуется решение специалиста"
        family = _value(row, "checker_family", "Семейство проверки") or "—"
        topic = _topic(row)
        key = tuple(normalize_text(value) for value in (domain, entity, route, reason, family, topic))
        grouped[key].append(row)

    clusters: list[dict[str, Any]] = []
    for key, grouped_items in grouped.items():
        for chunk_index, offset in enumerate(range(0, len(grouped_items), MAX_CLUSTER_SIZE), 1):
            items = grouped_items[offset:offset + MAX_CLUSTER_SIZE]
            first = items[0]
            ids = list(dict.fromkeys(
                _value(item, "ID", "plan_id", "id") for item in items
                if _value(item, "ID", "plan_id", "id")
            ))
            levels = [_level(item) for item in items]
            max_level = max(levels, key=lambda value: LEVEL_RANK.get(value, 0), default="L0")
            digest = hashlib.sha1(
                ("|".join(key) + f"|{chunk_index}").encode("utf-8", "ignore")
            ).hexdigest()[:10].upper()
            count = len(items)
            route = _value(first, "Ожидаемые разделы", "expected_sections", "scope") or "—"
            clusters.append({
                "ID группы": f"RQ-{digest}",
                "Приоритет": _priority(items),
                "Контур": _value(first, "Контур", "domain") or "Не определён",
                "Объект": _value(first, "Объект", "entity", "object") or "—",
                "Тема": _topic(first),
                "Ожидаемые разделы": route,
                "Количество вопросов": count,
                "Максимальный уровень доказательства": max_level,
                "Типовая причина": _value(first, "Причина", "coverage_reason", "reason") or "Требуется предметное решение специалиста.",
                "Пример проверки": _value(first, "Проверка", "title", "question", "parameter") or "—",
                "Рекомендуемое действие": (
                    f"Рассмотреть до {MAX_CLUSTER_SIZE} однородных вопросов темы «{_topic(first)}» "
                    f"по маршруту {route}; решение и доказательство фиксировать по каждому вопросу."
                ),
                "ID вопросов": " | ".join(ids[:12]) + (f" | ещё {len(ids)-12}" if len(ids) > 12 else ""),
            })

    priority_rank = {"Высокий": 0, "Средний": 1, "Низкий": 2}
    clusters.sort(key=lambda row: (
        priority_rank.get(str(row.get("Приоритет")), 9),
        -int(row.get("Количество вопросов") or 0),
        str(row.get("Контур") or ""),
        str(row.get("ID группы") or ""),
    ))
    return clusters
