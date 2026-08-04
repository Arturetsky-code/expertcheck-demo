from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import re

OBJECT_CODES = {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _norm(value: Any) -> str:
    text = _clean(value).lower().replace("ё", "е")
    text = re.sub(r"^\s*\d+(?:\.\d+)*\s*[-–—.:]?\s*", "", text)
    text = re.sub(r"[^а-яa-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _source_section(item: dict[str, Any]) -> str:
    return _clean(item.get("document_type") or item.get("section") or item.get("Раздел") or "Не определён")


@dataclass
class DEMValue:
    parameter_code: str
    parameter_name: str
    value: Any
    value_text: str
    unit: str
    section: str
    document: str
    page: int | None
    confidence: float
    extraction_method: str
    table_type: str
    source_fragment: str
    genplan_position: str = ""


@dataclass
class DEMObject:
    object_id: str
    name: str
    genplan_position: str = ""
    aliases: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)
    values: list[DEMValue] = field(default_factory=list)
    quantity: int = 1
    object_class: str = "UNCLASSIFIED"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["aliases"] = sorted(self.aliases)
        result["sources"] = sorted(self.sources)
        return result


@dataclass
class DigitalEngineeringModel:
    project_name: str
    objects: list[DEMObject]
    unassigned_values: list[DEMValue]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "objects": [obj.to_dict() for obj in self.objects],
            "unassigned_values": [asdict(value) for value in self.unassigned_values],
            "metadata": self.metadata,
        }


def _object_key(position: str, name: str) -> str:
    if position:
        return f"GP:{position}"
    return f"NM:{_norm(name)}"


def _object_id(position: str, name: str, index: int) -> str:
    if position:
        return f"OBJ-GP-{position.replace('.', '-') }"
    slug = re.sub(r"[^a-zа-я0-9]+", "-", _norm(name))[:36].strip("-")
    return f"OBJ-{slug or index:>03}".replace(" ", "0")


def _to_value(item: dict[str, Any]) -> DEMValue:
    page = item.get("page")
    try:
        page = int(page) if page not in (None, "") else None
    except (TypeError, ValueError):
        page = None
    confidence = item.get("core2_confidence", item.get("confidence", 0.0))
    try:
        confidence = float(confidence or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return DEMValue(
        parameter_code=_clean(item.get("parameter_code")),
        parameter_name=_clean(item.get("parameter_name")),
        value=item.get("value"),
        value_text=_clean(item.get("value_text") or item.get("value")),
        unit=_clean(item.get("unit")),
        section=_source_section(item),
        document=_clean(item.get("document")),
        page=page,
        confidence=round(confidence, 3),
        extraction_method=_clean(item.get("match_method") or item.get("extraction_method")),
        table_type=_clean(item.get("table_type")),
        source_fragment=_clean(item.get("context") or item.get("source_fragment")),
        genplan_position=_clean(item.get("genplan_position")),
    )


def build_dem(findings: list[dict[str, Any]], project_name: str = "Новый проект") -> DigitalEngineeringModel:
    """Строит цифровую инженерную модель из результатов извлечения.

    Приоритет идентификации объекта: позиция по генплану -> semantic anchor ->
    нормализованное наименование. Непривязанные значения сохраняются отдельно и
    не используются как доказательство успешной проверки.
    """
    objects_by_key: dict[str, DEMObject] = {}

    # Сначала формируем опорный реестр объектов.
    for item in findings:
        if _clean(item.get("parameter_code")) not in OBJECT_CODES:
            continue
        name = _clean(item.get("object_hint") or item.get("value_text"))
        position = _clean(item.get("genplan_position"))
        if not name or name == "Не определён":
            continue
        key = _object_key(position, name)
        if key not in objects_by_key:
            objects_by_key[key] = DEMObject(
                object_id=_object_id(position, name, len(objects_by_key) + 1),
                name=name,
                genplan_position=position,
            )
        obj = objects_by_key[key]
        obj.aliases.add(name)
        obj.sources.add(_source_section(item))
        try:
            quantity = int(float(item.get("value") or 1))
            obj.quantity = max(obj.quantity, quantity)
        except (TypeError, ValueError):
            pass

    # Индексы для привязки характеристик.
    by_position = {obj.genplan_position: obj for obj in objects_by_key.values() if obj.genplan_position}
    by_name = {_norm(alias): obj for obj in objects_by_key.values() for alias in obj.aliases if _norm(alias)}

    unassigned: list[DEMValue] = []
    for item in findings:
        if _clean(item.get("parameter_code")) in OBJECT_CODES:
            continue
        value = _to_value(item)
        position = _clean(item.get("semantic_anchor_position") or item.get("genplan_position"))
        name = _clean(item.get("semantic_anchor_name") or item.get("object_hint"))
        obj = by_position.get(position) if position else None
        if obj is None and _norm(name):
            obj = by_name.get(_norm(name))
        if obj is None:
            unassigned.append(value)
            continue
        obj.values.append(value)
        obj.sources.add(value.section)
        if name:
            obj.aliases.add(name)

    objects = sorted(
        objects_by_key.values(),
        key=lambda x: ([int(p) if p.isdigit() else p for p in x.genplan_position.split(".")] if x.genplan_position else [9999], x.name),
    )
    metadata = {
        "object_count": len(objects),
        "physical_object_count": sum(max(1, obj.quantity) for obj in objects),
        "value_count": sum(len(obj.values) for obj in objects),
        "unassigned_value_count": len(unassigned),
    }
    return DigitalEngineeringModel(project_name=project_name, objects=objects, unassigned_values=unassigned, metadata=metadata)
