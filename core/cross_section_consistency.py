from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code, classify_object, parameter_applicability
from .object_identity import ObjectIdentityEngine

# Абсолютный допуск, относительный допуск, приоритет проверки.
TOLERANCES: dict[str, tuple[float, float, str]] = {
    "AREA_BUILD": (0.1, 0.001, "Высокий"),
    "AREA_TOTAL": (0.1, 0.001, "Высокий"),
    "VOLUME_BUILD": (1.0, 0.002, "Высокий"),
    "HEIGHT_BUILD": (0.05, 0.002, "Средний"),
    "FLOORS": (0.0, 0.0, "Высокий"),
    "CAPACITY": (0.01, 0.002, "Высокий"),
    "RES_VOLUME": (0.1, 0.001, "Высокий"),
    "POWER_KTP": (1.0, 0.002, "Высокий"),
    "POWER_INSTALLED": (1.0, 0.002, "Высокий"),
    "POWER_CALCULATED": (1.0, 0.002, "Высокий"),
    "PERSONNEL": (0.0, 0.0, "Средний"),
    "LENGTH": (0.1, 0.001, "Средний"),
    "QUANTITY": (0.0, 0.0, "Высокий"),
    "PRESSURE": (0.01, 0.005, "Высокий"),
    "TEMPERATURE": (1.0, 0.01, "Средний"),
    "DIAMETER": (1.0, 0.002, "Высокий"),
    "FLOW_RATE": (0.01, 0.005, "Высокий"),
    "VOLTAGE": (0.01, 0.002, "Высокий"),
    "DEPTH": (0.1, 0.001, "Средний"),
}

SECTION_FAMILIES = (
    ("ПЗ XML", ("пз xml", "xml")),
    ("ПЗУ", ("пзу", "генплан", "генеральн")),
    ("ПЗ", ("пз", "пояснитель")),
    ("АР", ("ар", "архитект")),
    ("КР", ("кр", "конструктив")),
    ("ТХ", ("тх", "технолог")),
    ("ИОС1", ("иос1", "электроснаб", "эс")),
    ("ИОС2", ("иос2", "водоснаб", "вк")),
    ("ИОС", ("иос",)),
    ("ПОС", ("пос",)),
    ("ПБ", ("пб", "пожар")),
    ("ООС", ("оос", "овос")),
)

# Разделы, в которых параметр обычно может подтверждаться. Это не требование
# комплектности: отсутствие раздела даёт диагностический статус, а не замечание.
EXPECTED_SECTION_HINTS: dict[str, tuple[str, ...]] = {
    "AREA_BUILD": ("ПЗ", "ПЗУ", "АР"),
    "AREA_TOTAL": ("ПЗ", "АР"),
    "VOLUME_BUILD": ("ПЗ", "АР"),
    "HEIGHT_BUILD": ("ПЗ", "АР", "КР"),
    "FLOORS": ("ПЗ", "АР"),
    "CAPACITY": ("ПЗ", "ТХ"),
    "RES_VOLUME": ("ПЗ", "ТХ", "ИОС2"),
    "POWER_KTP": ("ПЗ", "ТХ", "ИОС1"),
    "POWER_INSTALLED": ("ПЗ", "ТХ", "ИОС1"),
    "POWER_CALCULATED": ("ПЗ", "ТХ", "ИОС1"),
    "PERSONNEL": ("ПЗ", "ТХ"),
    "LENGTH": ("ПЗ", "ПЗУ", "ТХ"),
    "QUANTITY": ("ПЗ", "ПЗУ", "ТХ"),
    "PRESSURE": ("ПЗ", "ТХ", "ИОС"),
    "TEMPERATURE": ("ПЗ", "ТХ"),
    "DIAMETER": ("ПЗ", "ПЗУ", "ТХ", "ИОС"),
    "FLOW_RATE": ("ПЗ", "ТХ", "ИОС"),
    "VOLTAGE": ("ПЗ", "ТХ", "ИОС1"),
    "DEPTH": ("ПЗ", "ПЗУ", "ТХ", "КР"),
}


def section_family(item: dict[str, Any]) -> str:
    raw = str(item.get("section") or item.get("document_type") or item.get("Раздел") or "").strip()
    low = normalize_text(raw)
    if item.get("source_kind") == "xml":
        return "ПЗ XML"
    for family, aliases in SECTION_FAMILIES:
        if any(alias in low for alias in aliases):
            return family
    return raw or "Не определён"


def numeric_value(item: dict[str, Any]) -> float | None:
    value = item.get("value_num", item.get("value"))
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _usable(item: dict[str, Any]) -> bool:
    code = canonical_parameter_code(item.get("parameter_code"))
    obj = str(item.get("semantic_anchor_name") or item.get("object_hint") or "").strip()
    confidence = float(item.get("core2_confidence") or item.get("confidence") or 0.0)
    position = str(item.get("genplan_position") or "").strip()
    binding = str(item.get("binding_status") or item.get("property_binding_status") or "").upper()
    strong_binding = binding in {"ROW_LOCKED", "POSITION_LOCKED", "EXACT_OBJECT"}
    # Без позиции или жёсткой привязки принимаются только сведения с высокой уверенностью.
    binding_ok = bool(position) or strong_binding or confidence >= 0.82
    return (
        code in TOLERANCES
        and numeric_value(item) is not None
        and bool(obj)
        and obj != "Не определён"
        and confidence >= 0.62
        and binding_ok
    )


def _object_key(item: dict[str, Any]) -> str:
    position = str(item.get("genplan_position") or "").strip()
    if position:
        return f"pos:{position}"
    return f"name:{normalize_text(item.get('object_hint'))}"


def _merge_name_groups(items: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Объединяет безпозиционные записи только при однозначном сильном сходстве."""
    positioned: dict[str, list[dict[str, Any]]] = defaultdict(list)
    loose: list[dict[str, Any]] = []
    for item in items:
        position = str(item.get("genplan_position") or "").strip()
        if position:
            positioned[position].append(item)
        else:
            loose.append(item)

    groups = list(positioned.values())
    identity = ObjectIdentityEngine()
    for item in loose:
        name = str(item.get("object_hint") or "")
        matches: list[tuple[float, int]] = []
        for idx, group in enumerate(groups):
            anchor = group[0]
            decision = identity.compare(name, str(anchor.get("object_hint") or ""), "", str(anchor.get("genplan_position") or ""))
            if decision.score >= 0.86:
                matches.append((decision.score, idx))
        matches.sort(reverse=True)
        if matches and (len(matches) == 1 or matches[0][0] - matches[1][0] >= 0.08):
            groups[matches[0][1]].append(item)
            continue
        # Сопоставление с другими безпозиционными группами.
        chosen = None
        for idx, group in enumerate(groups):
            if str(group[0].get("genplan_position") or ""):
                continue
            decision = identity.compare(name, str(group[0].get("object_hint") or ""))
            if decision.score >= 0.9:
                chosen = idx
                break
        if chosen is None:
            groups.append([item])
        else:
            groups[chosen].append(item)
    return groups


def _dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str, float, str], dict[str, Any]] = {}
    for item in items:
        value = numeric_value(item)
        if value is None:
            continue
        key = (
            section_family(item),
            str(item.get("document") or ""),
            round(value, 8),
            str(item.get("unit") or ""),
        )
        score = float(item.get("core2_confidence") or item.get("confidence") or 0.0)
        current = best.get(key)
        current_score = float((current or {}).get("core2_confidence") or (current or {}).get("confidence") or 0.0)
        if current is None or score > current_score:
            best[key] = item
    return list(best.values())


def _same(a: float, b: float, code: str) -> bool:
    abs_tol, rel_tol, _ = TOLERANCES[code]
    return math.isclose(a, b, abs_tol=abs_tol, rel_tol=rel_tol)


def _representative_name(items: list[dict[str, Any]]) -> str:
    ranked = sorted(
        items,
        key=lambda x: (
            bool(x.get("genplan_position")),
            section_family(x) in {"ПЗ", "ПЗ XML", "ПЗУ"},
            float(x.get("core2_confidence") or x.get("confidence") or 0.0),
            len(str(x.get("object_hint") or "")),
        ),
        reverse=True,
    )
    return str(ranked[0].get("object_hint") or "Не определён") if ranked else "Не определён"


def build_cross_section_checks(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Сверяет характеристики одного объекта сразу по всем разделам.

    В отличие от legacy-сравнения, движок:
    - объединяет части одного раздела в семейства;
    - учитывает точную позицию как главный идентификатор;
    - выявляет внутренний конфликт значений внутри одного раздела;
    - показывает неподтверждённые характеристики без объявления их ошибкой;
    - не выбирает автоматически "правильный" источник.
    """
    usable = [item for item in findings if _usable(item)]
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in usable:
        code = canonical_parameter_code(item.get("parameter_code"))
        item["parameter_code"] = code
        by_code[code].append(item)

    rows: list[dict[str, Any]] = []
    for code, code_items in by_code.items():
        for object_items in _merge_name_groups(code_items):
            object_items = _dedupe(object_items)
            if not object_items:
                continue
            by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for item in object_items:
                by_section[section_family(item)].append(item)

            all_values = [numeric_value(item) for item in object_items]
            values = [v for v in all_values if v is not None]
            if not values:
                continue

            internal_conflicts: list[str] = []
            section_values: dict[str, float] = {}
            section_evidence: dict[str, list[float]] = {}
            for section, section_items in by_section.items():
                vals = [numeric_value(x) for x in section_items]
                vals = [v for v in vals if v is not None]
                section_evidence[section] = vals
                if len(vals) > 1 and any(not _same(vals[0], v, code) for v in vals[1:]):
                    internal_conflicts.append(section)
                # Берём наиболее уверенную запись только для представления, не как истину.
                best_item = max(section_items, key=lambda x: float(x.get("core2_confidence") or x.get("confidence") or 0.0))
                best_value = numeric_value(best_item)
                if best_value is not None:
                    section_values[section] = best_value

            independent_sections = len(section_values)
            comparable_values = list(section_values.values())
            cross_mismatch = len(comparable_values) >= 2 and any(
                not _same(comparable_values[0], value, code) for value in comparable_values[1:]
            )
            strong_evidence_count = sum(1 for x in object_items if str(x.get('binding_status') or x.get('property_binding_status') or '').upper() in {'ROW_LOCKED','POSITION_LOCKED','EXACT_OBJECT'} or x.get('genplan_position') or float(x.get('core2_confidence') or x.get('confidence') or 0.0) >= 0.82)
            if internal_conflicts and strong_evidence_count >= 2:
                status = "КОНФЛИКТ ВНУТРИ РАЗДЕЛА"
            elif cross_mismatch and strong_evidence_count >= 2:
                status = "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ"
            elif cross_mismatch:
                status = "НЕДОСТАТОЧНО ДАННЫХ"
            elif independent_sections >= 2:
                status = "СОВПАДАЕТ"
            else:
                status = "НЕДОСТАТОЧНО ДАННЫХ"

            name = _representative_name(object_items)
            object_type = classify_object(name).code
            applicability = parameter_applicability(object_type, code)
            if applicability == "not_applicable":
                continue
            position = next((str(x.get("genplan_position") or "") for x in object_items if x.get("genplan_position")), "")
            parameter_name = str(next((x.get("parameter_name") for x in object_items if x.get("parameter_name")), code))
            unit = str(next((x.get("unit") for x in object_items if x.get("unit")), ""))
            abs_tol, rel_tol, priority = TOLERANCES[code]
            expected = EXPECTED_SECTION_HINTS.get(code, ())
            missing_hints = [section for section in expected if section not in section_values]
            source_parts = [f"{section}: {value:g} {unit}".strip() for section, value in sorted(section_values.items())]
            evidence_parts = []
            for item in sorted(object_items, key=lambda x: (section_family(x), str(x.get("document") or ""), int(x.get("page") or 0))):
                evidence_parts.append(
                    f"{section_family(item)} — {item.get('document')}, стр. {item.get('page') or '-'}: "
                    f"{numeric_value(item):g} {item.get('unit') or unit}".strip()
                )

            check_id = re.sub(r"[^A-Za-zА-Яа-я0-9]+", "-", f"{position}-{name}").strip("-")[:38]
            explanation_bits = [f"Сопоставлено независимых разделов: {independent_sections}."]
            if internal_conflicts:
                explanation_bits.append("Разные значения найдены внутри: " + ", ".join(internal_conflicts) + ".")
            if missing_hints:
                explanation_bits.append("Не найдено ожидаемое подтверждение в: " + ", ".join(missing_hints) + ".")
            if status == "СОВПАДАЕТ":
                explanation_bits.append("Значения находятся в пределах установленного допуска.")
            elif status == "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ":
                explanation_bits.append("Значения разных разделов выходят за установленный допуск.")
            elif status == "НЕДОСТАТОЧНО ДАННЫХ":
                explanation_bits.append("Характеристика найдена только в одном независимом разделе; вывод о согласованности невозможен.")

            rows.append({
                "check_code": f"CORE-XSEC-{code}-{check_id}",
                "object": name,
                "genplan_position": position,
                "parameter_code": code,
                "parameter_name": parameter_name,
                "object_type_code": object_type,
                "parameter_applicability": applicability,
                "unit": unit,
                "priority": priority,
                "rule_name": "Межраздельная согласованность характеристик",
                "category": "Межраздельная сверка",
                "check_type": "Сводная межраздельная проверка",
                "rationale": "Одинаковая характеристика одного объекта должна быть согласована во всех разделах, где она приводится.",
                "expected_documents": ", ".join(expected),
                "missing_expected_documents": ", ".join(missing_hints),
                "tolerance": f"абс. {abs_tol:g}; отн. {rel_tol:.3%}",
                "evidence_level": "Высокий" if independent_sections >= 3 else "Средний" if independent_sections >= 2 else "Низкий",
                "evidence_count": len(object_items),
                "independent_section_count": independent_sections,
                "rejected_count": 0,
                "status": status,
                "min_value": min(values),
                "max_value": max(values),
                "difference": max(values) - min(values),
                "documents": ", ".join(sorted(section_values)),
                "document_values": " | ".join(source_parts),
                "sources": " | ".join(evidence_parts),
                "internal_conflict_sections": ", ".join(internal_conflicts),
                "comment": (
                    "Проверить и синхронизировать значения в исходных разделах."
                    if status in {"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ", "КОНФЛИКТ ВНУТРИ РАЗДЕЛА"}
                    else "Дополнительная корректировка по данной проверке не требуется."
                    if status == "СОВПАДАЕТ"
                    else "Требуется подтверждение характеристики в другом разделе."
                ),
                "explanation": " ".join(explanation_bits),
                "rule_source": "core/cross-section",
                "knowledge_rule_code": "CORE-XSEC-001",
                "knowledge_rule_name": "Межраздельная согласованность характеристик",
            })

    status_order = {
        "КОНФЛИКТ ВНУТРИ РАЗДЕЛА": 0,
        "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ": 1,
        "НЕДОСТАТОЧНО ДАННЫХ": 2,
        "СОВПАДАЕТ": 3,
    }
    rows.sort(key=lambda row: (status_order.get(str(row.get("status")), 9), str(row.get("object")), str(row.get("parameter_name"))))
    return rows
