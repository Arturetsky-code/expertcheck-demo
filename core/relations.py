from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .dem import DigitalEngineeringModel


@dataclass
class ObjectRelation:
    source_id: str
    target_id: str
    relation_type: str
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RelationEngine:
    """Строит только доказуемые связи. Отраслевые ожидания живут в Knowledge Packs."""

    def build(self, model: DigitalEngineeringModel) -> list[ObjectRelation]:
        relations: list[ObjectRelation] = []
        objects = model.objects
        for source in objects:
            source_name = source.name.lower()
            for target in objects:
                if source.object_id == target.object_id:
                    continue
                target_name = target.name.lower()
                # Иерархия позиции 4.2 -> 4.2.1 является доказуемой структурной связью.
                if source.genplan_position and target.genplan_position.startswith(source.genplan_position + "."):
                    relations.append(ObjectRelation(
                        source.object_id, target.object_id, "contains", 0.98,
                        "Дочерняя позиция по генплану.",
                    ))
                elif target.genplan_position and source.genplan_position.startswith(target.genplan_position + "."):
                    continue
                # Осторожная связь сооружение-компонент по явному вхождению полного названия.
                elif len(source_name) > 8 and source_name in target_name:
                    relations.append(ObjectRelation(
                        source.object_id, target.object_id, "related_name", 0.72,
                        "Наименование одного объекта входит в наименование другого.",
                    ))
        # Удаляем повторы.
        unique: dict[tuple[str, str, str], ObjectRelation] = {}
        for rel in relations:
            unique[(rel.source_id, rel.target_id, rel.relation_type)] = rel
        return list(unique.values())
