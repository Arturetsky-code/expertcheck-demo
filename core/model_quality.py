from __future__ import annotations

from collections import Counter
from typing import Any

from .dem import DigitalEngineeringModel
from .validation import ValidationIssue


def calculate_model_quality(model: DigitalEngineeringModel, issues: list[ValidationIssue]) -> dict[str, Any]:
    total_objects = len(model.objects)
    multi_source = sum(1 for obj in model.objects if len(obj.sources) >= 2)
    positioned = sum(1 for obj in model.objects if obj.genplan_position)
    values = [value for obj in model.objects for value in obj.values]
    reliable_values = sum(1 for value in values if value.confidence >= 0.75)

    object_confirmation = multi_source / total_objects if total_objects else 0.0
    position_coverage = positioned / total_objects if total_objects else 0.0
    value_reliability = reliable_values / len(values) if values else 0.0
    assignment_coverage = len(values) / (len(values) + len(model.unassigned_values)) if values or model.unassigned_values else 0.0

    penalties = Counter(issue.severity for issue in issues)
    penalty = min(0.25, penalties["error"] * 0.04 + penalties["warning"] * 0.012 + penalties["info"] * 0.002)
    raw = (
        object_confirmation * 0.30
        + position_coverage * 0.20
        + value_reliability * 0.25
        + assignment_coverage * 0.25
    )
    index = max(0.0, min(1.0, raw - penalty))
    return {
        "model_quality_index": round(index, 3),
        "object_confirmation": round(object_confirmation, 3),
        "position_coverage": round(position_coverage, 3),
        "value_reliability": round(value_reliability, 3),
        "assignment_coverage": round(assignment_coverage, 3),
        "objects": total_objects,
        "values": len(values),
        "unassigned_values": len(model.unassigned_values),
        "validation_issues": len(issues),
        "issue_breakdown": dict(penalties),
    }
