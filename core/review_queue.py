from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any, Iterable

from .normalization import normalize_text


LEVEL_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
MAX_CLUSTER_SIZE = 40
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


def _reason_code(row: dict[str, Any]) -> str:
    direct = _value(row, "Код причины", "coverage_reason_code")
    if direct:
        return direct.upper()
    blob = normalize_text(_value(row, "Причина", "coverage_reason", "reason"))
    rules = (
        (("не найден адресн", "нет адресн"), "NO_ADDRESSABLE_EVIDENCE"),
        (("объект", "привяз"), "ENTITY_BINDING"),
        (("квалификатор",), "CRITICAL_QUALIFIER"),
        (("одного проектного решения", "разных фрагмент"), "SAME_CLAUSE"),
        (("модальност",), "WRONG_MODALITY"),
        (("единиц",), "UNIT_COMPATIBILITY"),
        (("независим", "семантич"), "INDEPENDENT_CONFIRMATION"),
        (("раздел-владел", "owner"), "OWNER_ROUTE"),
        (("critic", "контрольн"), "INDEPENDENT_CONFIRMATION"),
    )
    for markers, code in rules:
        if all(marker in blob for marker in markers):
            return code
    return "SPECIALIST_JUDGEMENT"


def _route_signature(row: dict[str, Any]) -> str:
    value = row.get("Ожидаемые разделы")
    if value in (None, ""):
        value = row.get("expected_sections") or row.get("expected_evidence_route") or row.get("scope")
    if isinstance(value, (list, tuple, set)):
        parts = [str(item).strip() for item in value if str(item).strip()]
    else:
        parts = [part.strip() for part in re.split(r"[|,;/]+", str(value or "")) if part.strip()]
    normalized = sorted(dict.fromkeys(normalize_text(part) for part in parts if normalize_text(part)))
    return " + ".join(normalized) or "—"


def _action_for_reason(code: str, topic: str, route: str) -> str:
    actions = {
        "NO_ADDRESSABLE_EVIDENCE": f"Проверить наличие адресного доказательства по маршруту {route}.",
        "ENTITY_BINDING": "Подтвердить, к какому объекту относится найденное проектное решение.",
        "CRITICAL_QUALIFIER": "Проверить обязательный инженерный квалификатор в одном адресном фрагменте.",
        "SAME_CLAUSE": "Подтвердить, что обязательные слоты образуют одно проектное решение.",
        "WRONG_MODALITY": "Проверить требуемый тип доказательства: текст, таблицу, чертёж или расчёт.",
        "UNIT_COMPATIBILITY": "Проверить единицы и допустимость прямого сопоставления значений.",
        "INDEPENDENT_CONFIRMATION": "Выполнить независимое подтверждение уже найденного L3/L4-доказательства.",
        "OWNER_ROUTE": "Уточнить профильный раздел-владелец и контрольный раздел.",
        "SPECIALIST_JUDGEMENT": f"Рассмотреть однородные вопросы темы «{topic}» и зафиксировать решение.",
    }
    return actions.get(code, actions["SPECIALIST_JUDGEMENT"])


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
    """Compress detailed specialist questions into auditable work packages.

    Raw questions are never removed. 18.7 deliberately groups across objects
    when the engineering action is identical: the operator resolves one
    evidence problem family while retaining every underlying ID/object.
    """
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for raw in rows or []:
        row = dict(raw)
        domain = _value(row, "Контур", "domain") or "Не определён"
        route = _route_signature(row)
        reason_code = _reason_code(row)
        family = _value(row, "Семейство проверки", "checker_family") or "—"
        topic = _topic(row)
        key = tuple(normalize_text(value) for value in (
            domain, route, reason_code, family, topic,
        ))
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
            objects = list(dict.fromkeys(
                _value(item, "Объект", "entity", "object") for item in items
                if _value(item, "Объект", "entity", "object") not in {"", "—"}
            ))
            levels = [_level(item) for item in items]
            max_level = max(levels, key=lambda value: LEVEL_RANK.get(value, 0), default="L0")
            digest = hashlib.sha1(
                ("|".join(key) + f"|{chunk_index}").encode("utf-8", "ignore")
            ).hexdigest()[:10].upper()
            route = _route_signature(first)
            topic = _topic(first)
            reason_code = _reason_code(first)
            clusters.append({
                "ID группы": f"RQ-{digest}",
                "Приоритет": _priority(items),
                "Контур": _value(first, "Контур", "domain") or "Не определён",
                "Тема": topic,
                "Код причины": reason_code,
                "Ожидаемые разделы": route,
                "Количество вопросов": len(items),
                "Количество объектов": len(objects),
                "Объекты": " | ".join(objects[:8]) + (f" | ещё {len(objects)-8}" if len(objects) > 8 else ""),
                "Максимальный уровень доказательства": max_level,
                "Типовая причина": _value(first, "Причина", "coverage_reason", "reason") or "Требуется предметное решение специалиста.",
                "Пример проверки": _value(first, "Проверка", "title", "question", "parameter") or "—",
                "Рекомендуемое действие": _action_for_reason(reason_code, topic, route),
                "ID вопросов": " | ".join(ids[:20]) + (f" | ещё {len(ids)-20}" if len(ids) > 20 else ""),
            })

    priority_rank = {"Высокий": 0, "Средний": 1, "Низкий": 2}
    clusters.sort(key=lambda row: (
        priority_rank.get(str(row.get("Приоритет")), 9),
        -int(row.get("Количество вопросов") or 0),
        str(row.get("Контур") or ""),
        str(row.get("ID группы") or ""),
    ))
    return clusters

