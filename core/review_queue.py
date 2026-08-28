from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any, Iterable

from .normalization import normalize_text


LEVEL_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}


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
        key = tuple(normalize_text(value) for value in (domain, entity, route, reason, family))
        grouped[key].append(row)

    clusters: list[dict[str, Any]] = []
    for key, items in grouped.items():
        first = items[0]
        ids = list(dict.fromkeys(
            _value(item, "ID", "plan_id", "id") for item in items
            if _value(item, "ID", "plan_id", "id")
        ))
        levels = [_level(item) for item in items]
        max_level = max(levels, key=lambda value: LEVEL_RANK.get(value, 0), default="L0")
        digest = hashlib.sha1("|".join(key).encode("utf-8", "ignore")).hexdigest()[:10].upper()
        count = len(items)
        route = _value(first, "Ожидаемые разделы", "expected_sections", "scope") or "—"
        clusters.append({
            "ID группы": f"RQ-{digest}",
            "Приоритет": _priority(items),
            "Контур": _value(first, "Контур", "domain") or "Не определён",
            "Объект": _value(first, "Объект", "entity", "object") or "—",
            "Ожидаемые разделы": route,
            "Количество вопросов": count,
            "Максимальный уровень доказательства": max_level,
            "Типовая причина": _value(first, "Причина", "coverage_reason", "reason") or "Требуется предметное решение специалиста.",
            "Пример проверки": _value(first, "Проверка", "title", "question", "parameter") or "—",
            "Рекомендуемое действие": (
                f"Рассмотреть {count} связанных вопросов по маршруту {route} как один рабочий пакет; "
                "решение и доказательство фиксировать отдельно по каждому исходному вопросу."
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
