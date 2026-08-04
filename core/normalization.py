from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizedParameter:
    code: str
    name: str
    unit: str = ""
    confidence: float = 1.0


_PARAMETER_RULES: list[tuple[str, str, tuple[str, ...], str]] = [
    ("AREA_BUILD", "Площадь застройки", ("площадь застройки",), "м²"),
    ("AREA_TOTAL", "Общая площадь", ("общая площадь", "площадь общая"), "м²"),
    ("VOLUME_BUILD", "Строительный объём", ("строительный объем", "строительный объём"), "м³"),
    ("HEIGHT_BUILD", "Высота здания (сооружения)", ("высота здания", "высота сооружения", "высота объекта"), "м"),
    ("FLOORS", "Этажность", ("этажность", "количество этажей", "число этажей"), "эт."),
    ("CAPACITY", "Производительность", ("производительность", "проектная мощность"), ""),
    ("RES_VOLUME", "Объём резервуара", ("объем резервуара", "объём резервуара", "вместимость резервуара"), "м³"),
    ("POWER_KTP", "Мощность КТП", ("мощность ктп", "мощность трансформатора", "мощность трансформаторной подстанции"), "кВА"),
    ("POWER_INSTALLED", "Установленная мощность", ("установленная мощность",), "кВт"),
    ("POWER_CALCULATED", "Расчётная мощность", ("расчетная мощность", "расчётная мощность"), "кВт"),
    ("PERSONNEL", "Численность персонала", ("численность персонала", "количество работающих", "количество проживающих"), "чел."),
    ("LENGTH", "Протяжённость", ("протяженность", "протяжённость", "длина"), "м"),
    ("QUANTITY", "Количество", ("количество", "кол-во"), "шт."),
]

# ОКЕИ: используем только коды, для которых в тестовых XML значение однозначно.
_MEASURE_CODE_MAP: dict[str, str] = {
    "055": "м²",
    "113": "м³",
    "006": "м",
    "796": "шт.",
    "792": "чел.",
    "166": "кг",
    "168": "т",
    "214": "кВт",
    "227": "кВт",
}


def normalize_text(value: Any) -> str:
    text = str(value or "").lower().replace("ё", "е")
    text = text.replace("²", "2").replace("³", "3")
    text = re.sub(r"[\s\u00a0]+", " ", text)
    return text.strip(" .,:;–—-")


def canonical_parameter(raw_name: str) -> NormalizedParameter:
    normalized = normalize_text(raw_name)
    for code, name, aliases, unit in _PARAMETER_RULES:
        if any(alias.replace("ё", "е") in normalized for alias in aliases):
            return NormalizedParameter(code=code, name=name, unit=unit, confidence=1.0)
    return NormalizedParameter(code="XML_TEI", name=raw_name.strip() or "Показатель XML", confidence=0.55)


def normalize_measure(raw_measure: str, fallback: str = "") -> tuple[str, float]:
    measure = str(raw_measure or "").strip()
    if measure in _MEASURE_CODE_MAP:
        return _MEASURE_CODE_MAP[measure], 1.0
    low = normalize_text(measure)
    patterns = [
        (r"^(м2|кв\.? ?м)$", "м²"),
        (r"^(м3|куб\.? ?м)$", "м³"),
        (r"^(квт)$", "кВт"),
        (r"^(ква)$", "кВА"),
        (r"^(шт|ед)$", "шт."),
        (r"^(чел)$", "чел."),
        (r"^(м)$", "м"),
    ]
    for pattern, unit in patterns:
        if re.match(pattern, low, flags=re.I):
            return unit, 0.95
    return fallback or measure, 0.45 if measure else 0.0


def normalize_numeric(value: Any) -> float | None:
    try:
        return float(str(value).replace("\u00a0", "").replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
