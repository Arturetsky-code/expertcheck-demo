from __future__ import annotations

from typing import Any

from .normalization import normalize_text


CAPACITY_PROJECT_DESIGN = "PROJECT_DESIGN_CAPACITY"
CAPACITY_NOMINAL_TOTAL = "NOMINAL_TOTAL_CAPACITY"
CAPACITY_OPERATING_SECTION = "OPERATING_SECTION_THROUGHPUT"
CAPACITY_LINE = "SINGLE_LINE_CAPACITY"


def capacity_semantic_level(*values: Any) -> str:
    """Classify the engineering meaning of a capacity value.

    Equal units are not enough for a safe comparison: an operating throughput
    of one department, a single-line rating and a total design capacity can all
    be expressed in t/h.  The classifier deliberately returns an empty value
    when the source does not state the level explicitly.
    """
    text = normalize_text(" ".join(str(value or "") for value in values)).lower()
    compact = text.replace(" ", "")
    if any(marker in text for marker in (
        "часовая производительность отделения", "производительность отделения",
        "эксплуатационная производительность", "фактическая производительность",
        "среднечасовая производительность", "технологический режим",
        "технологические режимы",
    )):
        return CAPACITY_OPERATING_SECTION
    if any(marker in text for marker in (
        "производительность линии", "мощность линии", "одной линии",
        "на одну линию", "единичная производительность",
    )):
        return CAPACITY_LINE
    if any(marker in text for marker in (
        "суммарная производительность", "суммарной производительностью",
        "общая производительность", "номинальная производительность",
        "паспортная производительность", "установленная производительность",
    )):
        return CAPACITY_NOMINAL_TOTAL
    if any(marker in text for marker in (
        "проектная производительность", "проектной производительностью",
        "проектная мощность", "мощность проекта", "производительность проекта",
        "мощность предприятия", "производительность предприятия",
        "производственная мощность", "годовая производительность", "годовая мощность",
        "тыс. тонн в год", "тыс тонн в год", "млн. тонн в год", "млн тонн в год",
    )) or any(marker in compact for marker in (
        "тыс.т/год", "тыст/год", "млн.т/год", "млнт/год",
    )):
        return CAPACITY_PROJECT_DESIGN
    return ""


def capacity_levels_equivalent(required_level: str, observed_level: str) -> bool:
    """Return True only when capacity levels are safe to compare."""
    required = str(required_level or "")
    observed = str(observed_level or "")
    if not required and not observed:
        return True
    return bool(required and observed and required == observed)


def capacity_level_label(level: str) -> str:
    return {
        CAPACITY_PROJECT_DESIGN: "проектная производительность всего проекта",
        CAPACITY_NOMINAL_TOTAL: "суммарная номинальная производительность",
        CAPACITY_OPERATING_SECTION: "часовая производительность отделения по режиму",
        CAPACITY_LINE: "производительность одной линии",
    }.get(str(level or ""), "неуточнённый уровень производительности")
