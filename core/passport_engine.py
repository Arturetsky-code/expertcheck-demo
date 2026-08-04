from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable
import re

OBJECT_CODES = {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}
SOURCE_GROUPS = {
    "ПЗ": "ПЗ",
    "ПЗУ1": "ПЗУ", "ПЗУ2": "ПЗУ",
    "АР1": "АР", "АР2": "АР",
    "ТХ1": "ТХ", "ТХ2": "ТХ",
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _norm(value: Any) -> str:
    text = _clean(value).lower().replace("ё", "е")
    text = re.sub(r"^\s*\d+(?:\.\d+)*\s*[-–—.:]?\s*", "", text)
    text = re.sub(r"[^а-яa-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _section(value: Any) -> str:
    raw = _clean(value)
    return SOURCE_GROUPS.get(raw, raw or "Не определён")


@dataclass
class PassportCharacteristic:
    parameter_code: str
    parameter_name: str
    unit: str
    values_by_section: dict[str, list[str]]
    pages_by_section: dict[str, list[int]]
    confidence: float
    status: str
    evidence_count: int
    source_count: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["values_by_section"] = {
            key: "; ".join(values) for key, values in self.values_by_section.items()
        }
        data["pages_by_section"] = {
            key: ", ".join(str(page) for page in pages) for key, pages in self.pages_by_section.items()
        }
        return data


@dataclass
class ObjectPassport:
    position: str
    parent_position: str
    name: str
    quantity: int
    registry_status: str
    registry_sources: list[str]
    confirmation_matrix: dict[str, str]
    aliases: list[str]
    characteristics: list[PassportCharacteristic]
    linked_findings: int
    unlinked_findings: int
    passport_completeness: float

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["characteristics"] = [item.to_dict() for item in self.characteristics]
        return result


def _value_text(item: dict[str, Any]) -> str:
    value = _clean(item.get("value_text"))
    if value:
        return value
    raw = item.get("value")
    unit = _clean(item.get("unit"))
    return f"{raw} {unit}".strip() if raw not in (None, "") else ""


def _matches_object(item: dict[str, Any], position: str, name: str) -> bool:
    item_position = _clean(item.get("semantic_anchor_position") or item.get("genplan_position"))
    if position and item_position == position:
        return True
    item_name = _norm(item.get("semantic_anchor_name") or item.get("object_hint"))
    target = _norm(name)
    return bool(item_name and target and (item_name == target or item_name in target or target in item_name))


def _comparison_status(comparisons: Iterable[dict[str, Any]], position: str, name: str, parameter_code: str) -> str:
    target = _norm(name)
    for row in comparisons:
        row_name = _norm(row.get("object"))
        if row.get("parameter_code") != parameter_code:
            continue
        if row_name and target and (row_name == target or row_name in target or target in row_name):
            status = _clean(row.get("status"))
            if status:
                return status
    return ""


def build_object_passports(
    registry: Iterable[dict[str, Any]],
    findings: Iterable[dict[str, Any]],
    comparisons: Iterable[dict[str, Any]] | None = None,
) -> list[ObjectPassport]:
    """Строит паспорта строго от реестра объектов, а не от случайных текстовых находок."""
    findings_list = list(findings)
    comparisons_list = list(comparisons or [])
    passports: list[ObjectPassport] = []

    for record in registry:
        position = _clean(record.get("Позиция по ГП") or record.get("position"))
        parent = _clean(record.get("Родительская позиция") or record.get("parent_position"))
        name = _clean(record.get("Наименование объекта") or record.get("name"))
        quantity_raw = record.get("Количество", record.get("quantity", 1))
        try:
            quantity = max(1, int(float(quantity_raw or 1)))
        except (TypeError, ValueError):
            quantity = 1

        linked = [
            item for item in findings_list
            if item.get("parameter_code") not in OBJECT_CODES and _matches_object(item, position, name)
        ]
        object_mentions = [
            item for item in findings_list
            if item.get("parameter_code") in OBJECT_CODES and _matches_object(item, position, name)
        ]

        aliases = sorted({
            _clean(item.get("object_hint") or item.get("value_text"))
            for item in object_mentions
            if _clean(item.get("object_hint") or item.get("value_text"))
        })
        sections = sorted({_section(item.get("document_type")) for item in object_mentions + linked})
        confirmation_matrix = {
            section: ("Подтверждено" if section in sections else "Не найдено")
            for section in ["ПЗ", "ПЗУ", "АР", "ТХ", "ИОС", "ПОС", "ООС"]
        }

        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for item in linked:
            code = _clean(item.get("parameter_code"))
            pname = _clean(item.get("parameter_name"))
            if not code and not pname:
                continue
            grouped.setdefault((code, pname), []).append(item)

        characteristics: list[PassportCharacteristic] = []
        for (code, pname), rows in sorted(grouped.items(), key=lambda pair: pair[0][1]):
            values_by_section: dict[str, list[str]] = {}
            pages_by_section: dict[str, list[int]] = {}
            confidences: list[float] = []
            unit = ""
            for item in rows:
                section = _section(item.get("document_type"))
                text = _value_text(item)
                if text and text not in values_by_section.setdefault(section, []):
                    values_by_section[section].append(text)
                try:
                    page = int(item.get("page") or 0)
                except (TypeError, ValueError):
                    page = 0
                if page and page not in pages_by_section.setdefault(section, []):
                    pages_by_section[section].append(page)
                try:
                    confidences.append(float(item.get("core2_confidence", item.get("confidence", 0)) or 0))
                except (TypeError, ValueError):
                    pass
                unit = unit or _clean(item.get("unit"))

            comparison_status = _comparison_status(comparisons_list, position, name, code)
            if comparison_status:
                status = comparison_status
            elif len(values_by_section) >= 2:
                status = "ПОДТВЕРЖДЕНО НЕСКОЛЬКИМИ РАЗДЕЛАМИ"
            else:
                status = "НЕДОСТАТОЧНО ДАННЫХ"
            characteristics.append(PassportCharacteristic(
                parameter_code=code,
                parameter_name=pname or code,
                unit=unit,
                values_by_section=values_by_section,
                pages_by_section=pages_by_section,
                confidence=round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
                status=status,
                evidence_count=len(rows),
                source_count=len(values_by_section),
            ))

        confirmed_chars = sum(
            1 for item in characteristics
            if item.source_count >= 2 or item.status in {"СОВПАДАЕТ", "ПОДТВЕРЖДЕНО НЕСКОЛЬКИМИ РАЗДЕЛАМИ"}
        )
        source_factor = min(1.0, len(sections) / 3) if sections else 0.0
        char_factor = confirmed_chars / len(characteristics) if characteristics else 0.0
        completeness = round((0.55 * source_factor + 0.45 * char_factor) * 100, 1)

        passports.append(ObjectPassport(
            position=position,
            parent_position=parent,
            name=name,
            quantity=quantity,
            registry_status=_clean(record.get("Статус") or record.get("status")),
            registry_sources=sections,
            confirmation_matrix=confirmation_matrix,
            aliases=aliases,
            characteristics=characteristics,
            linked_findings=len(linked),
            unlinked_findings=0,
            passport_completeness=completeness,
        ))
    return passports


def passport_summary(passports: Iterable[ObjectPassport]) -> dict[str, Any]:
    items = list(passports)
    return {
        "passport_count": len(items),
        "complete_80_plus": sum(1 for item in items if item.passport_completeness >= 80),
        "requires_attention": sum(1 for item in items if item.passport_completeness < 50),
        "characteristic_count": sum(len(item.characteristics) for item in items),
        "average_completeness": round(sum(item.passport_completeness for item in items) / len(items), 1) if items else 0.0,
    }
