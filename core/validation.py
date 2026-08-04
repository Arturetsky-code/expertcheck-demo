from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .dem import DigitalEngineeringModel


@dataclass
class ValidationIssue:
    code: str
    severity: str
    object_id: str
    object_name: str
    message: str
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ValidationEngine:
    """Проверяет качество DEM, но не подменяет инженерные правила экспертизы."""

    def validate(self, model: DigitalEngineeringModel) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        seen_positions: dict[str, str] = {}
        for obj in model.objects:
            if not obj.genplan_position:
                issues.append(ValidationIssue(
                    "DEM-OBJ-001", "warning", obj.object_id, obj.name,
                    "Для объекта не определена позиция по генплану.",
                    "Проверьте перечень объектов и экспликацию ПЗУ.",
                ))
            elif obj.genplan_position in seen_positions:
                issues.append(ValidationIssue(
                    "DEM-OBJ-002", "error", obj.object_id, obj.name,
                    "Позиция по генплану используется более чем одним объектом.",
                    f"Ранее назначена объекту {seen_positions[obj.genplan_position]}.",
                ))
            else:
                seen_positions[obj.genplan_position] = obj.name

            if len(obj.sources) < 2:
                issues.append(ValidationIssue(
                    "DEM-OBJ-003", "info", obj.object_id, obj.name,
                    "Объект подтверждён только одним разделом.",
                    ", ".join(sorted(obj.sources)),
                ))

            for value in obj.values:
                if not value.unit and isinstance(value.value, (int, float)):
                    issues.append(ValidationIssue(
                        "DEM-VAL-001", "warning", obj.object_id, obj.name,
                        f"Для характеристики «{value.parameter_name}» не определена единица измерения.",
                        f"{value.document}, стр. {value.page or '—'}",
                    ))
                if value.confidence < 0.55:
                    issues.append(ValidationIssue(
                        "DEM-VAL-002", "info", obj.object_id, obj.name,
                        f"Низкая уверенность извлечения характеристики «{value.parameter_name}».",
                        f"Уверенность: {value.confidence:.0%}",
                    ))

        if model.unassigned_values:
            issues.append(ValidationIssue(
                "DEM-MOD-001", "warning", "PROJECT", model.project_name,
                "Часть характеристик не связана с объектами модели.",
                f"Непривязанных значений: {len(model.unassigned_values)}.",
            ))
        return issues
