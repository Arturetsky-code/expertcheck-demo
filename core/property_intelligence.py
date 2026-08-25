from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code


@dataclass(frozen=True)
class NormalizedEngineeringValue:
    code: str
    value: float
    unit: str
    scope: str = "default"
    semantic_label: str = ""


# Canonical units used by CrossCheck Engine. Multipliers convert source values to canonical units.
_UNIT_FACTORS: dict[str, dict[str, tuple[str, float]]] = {
    "AREA_BUILD": {"м2": ("м²", 1.0), "м²": ("м²", 1.0), "га": ("м²", 10000.0)},
    "AREA_TOTAL": {"м2": ("м²", 1.0), "м²": ("м²", 1.0), "га": ("м²", 10000.0)},
    "VOLUME_BUILD": {"м3": ("м³", 1.0), "м³": ("м³", 1.0), "тыс.м3": ("м³", 1000.0), "тыс м3": ("м³", 1000.0)},
    "VOLUME": {"м3": ("м³", 1.0), "м³": ("м³", 1.0), "тыс.м3": ("м³", 1000.0), "тыс м3": ("м³", 1000.0)},
    "RES_VOLUME": {"м3": ("м³", 1.0), "м³": ("м³", 1.0), "л": ("м³", 0.001)},
    "HEIGHT_BUILD": {"мм": ("м", 0.001), "см": ("м", 0.01), "м": ("м", 1.0)},
    "LENGTH": {"мм": ("м", 0.001), "м": ("м", 1.0), "км": ("м", 1000.0)},
    "WIDTH": {"мм": ("м", 0.001), "см": ("м", 0.01), "м": ("м", 1.0)},
    "DEPTH": {"мм": ("м", 0.001), "м": ("м", 1.0), "км": ("м", 1000.0)},
    "DIAMETER": {"мм": ("мм", 1.0), "см": ("мм", 10.0), "м": ("мм", 1000.0)},
    "POWER_KTP": {"ва": ("кВА", 0.001), "ква": ("кВА", 1.0), "мва": ("кВА", 1000.0)},
    "POWER_INSTALLED": {"вт": ("кВт", 0.001), "квт": ("кВт", 1.0), "мвт": ("кВт", 1000.0)},
    "POWER_CALCULATED": {"вт": ("кВт", 0.001), "квт": ("кВт", 1.0), "мвт": ("кВт", 1000.0)},
    "MOISTURE": {"%": ("%", 1.0)},
    "BULK_DENSITY": {"т/м3": ("т/м³", 1.0), "т/м³": ("т/м³", 1.0), "кг/м3": ("т/м³", 0.001), "кг/м³": ("т/м³", 0.001)},
    "VOLTAGE": {"в": ("кВ", 0.001), "кв": ("кВ", 1.0)},
    "PRESSURE": {"па": ("МПа", 0.000001), "кпа": ("МПа", 0.001), "мпа": ("МПа", 1.0), "бар": ("МПа", 0.1)},
    "FLOW_RATE": {"л/с": ("м³/ч", 3.6), "м3/ч": ("м³/ч", 1.0), "м³/ч": ("м³/ч", 1.0), "м3/сут": ("м³/ч", 1/24), "м³/сут": ("м³/ч", 1/24)},
}

_PARAMETER_NAMES = {
    "AREA_BUILD": "Площадь застройки",
    "AREA_TOTAL": "Общая площадь",
    "VOLUME_BUILD": "Строительный объём",
    "VOLUME": "Объём",
    "RES_VOLUME": "Объём/вместимость резервуара",
    "HEIGHT_BUILD": "Высота",
    "FLOORS": "Этажность",
    "CAPACITY": "Производительность/пропускная способность",
    "POWER_KTP": "Мощность КТП/трансформатора",
    "POWER_INSTALLED": "Установленная мощность",
    "POWER_CALCULATED": "Расчётная/максимальная мощность",
    "MOISTURE": "Влажность материала",
    "BULK_DENSITY": "Насыпная плотность",
    "FLOW_RATE": "Расход",
    "PRESSURE": "Давление",
    "DIAMETER": "Диаметр",
    "LENGTH": "Протяжённость",
    "WIDTH": "Ширина",
    "DEPTH": "Глубина",
    "VOLTAGE": "Напряжение",
    "QUANTITY": "Количество",
    "PERSONNEL": "Численность персонала",
    "TEMPERATURE": "Температура",
    "LINE_COUNT": "Количество линий",
}


def parameter_display_name(code: Any) -> str:
    canonical = canonical_parameter_code(code)
    return _PARAMETER_NAMES.get(canonical, canonical or "Показатель")


def _unit_key(unit: Any) -> str:
    text = str(unit or "").strip().lower().replace(" ", "")
    text = text.replace("³", "3").replace("²", "2")
    return text


def infer_value_scope(item: dict[str, Any], code: Any) -> str:
    """Distinguishes values that must not be compared directly (e.g. one tank vs total group volume)."""
    canonical = canonical_parameter_code(code)
    context = normalize_text(" ".join(str(item.get(k) or "") for k in (
        "parameter_name", "context", "table_title", "column_header", "row_text", "value_text"
    )))
    if canonical in {"RES_VOLUME", "VOLUME", "QUANTITY"}:
        if any(token in context for token in ("общий объем", "общий объём", "суммарн", "всего", "общая вместимость")):
            return "total"
        if any(token in context for token in ("каждого", "одного резервуара", "единичн", "на 1", "1 шт")):
            return "per_unit"
    if canonical in {"POWER_INSTALLED", "POWER_CALCULATED", "POWER_KTP"}:
        if any(token in context for token in ("суммарн", "общая мощность", "общая установленная")):
            return "total"
        if any(token in context for token in ("одного", "каждого", "единичная")):
            return "per_unit"
    if canonical == "CAPACITY":
        if any(token in context for token in ("суммарн", "общая производительность", "по комплексу")):
            return "total"
        if any(token in context for token in ("одной линии", "каждой линии", "единичн")):
            return "per_unit"
    if canonical == "AREA_TOTAL":
        if any(token in context for token in ("экспликация помещений", "площадь помещений", "сумма площадей помещений", "итого помещений")):
            return "room_area_sum"
        if any(token in context for token in ("общая площадь здания", "общая площадь объекта", "общая площадь, м")):
            return "building_total_area"
    if canonical == "AREA_BUILD":
        if any(token in context for token in ("площадь территории", "площадь площадки", "площадь земельного участка")):
            return "site_area"
        if "площадь застройки" in context:
            return "building_footprint"
    if canonical == "LENGTH":
        if "протяженность ограж" in context or "протяжённость ограж" in context:
            return "fence_length"
        if "эстакад" in context:
            return "trestle_length"
    return "default"


def normalize_engineering_value(item: dict[str, Any]) -> NormalizedEngineeringValue | None:
    code = canonical_parameter_code(item.get("parameter_code"))
    raw = item.get("value_num", item.get("value"))
    try:
        value = float(str(raw).replace("\u00a0", "").replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    unit = str(item.get("unit") or "").strip()
    factors = _UNIT_FACTORS.get(code, {})
    factor = factors.get(_unit_key(unit))
    if factor:
        canonical_unit, multiplier = factor
        value *= multiplier
        unit = canonical_unit
    return NormalizedEngineeringValue(
        code=code,
        value=value,
        unit=unit,
        scope=infer_value_scope(item, code),
        semantic_label=parameter_display_name(code),
    )
