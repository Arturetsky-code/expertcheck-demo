from __future__ import annotations

from typing import Any

from .passport_engine import build_object_passports, passport_summary
from .project_understanding import build_project_object_model, understanding_quality


RECOVERY_VERSION = "18.6-project-knowledge-recovery-v1"


def build_project_knowledge_manifest(
    *,
    registry: list[dict[str, Any]],
    passports: list[dict[str, Any]],
    project_understanding: dict[str, Any],
    comparisons: list[dict[str, Any]],
    snapshot_id: str = "",
    source: str = "pipeline",
) -> dict[str, Any]:
    """Compact index of the heavy project-model components.

    The model deliberately references canonical fields instead of duplicating
    their full payloads; this keeps PostgreSQL/Streamlit memory bounded.
    """
    objects = list((project_understanding or {}).get("objects") or [])
    if objects:
        object_index = [{
            "object_id": row.get("object_id"),
            "name": row.get("name"),
            "position": row.get("position"),
            "object_type": row.get("object_type"),
            "property_count": int(row.get("property_count") or 0),
            "conflict_count": int(row.get("conflict_count") or 0),
        } for row in objects]
    else:
        object_index = [{
            "object_id": "",
            "name": row.get("Наименование объекта") or row.get("name"),
            "position": row.get("Позиция по ГП") or row.get("position"),
            "object_type": row.get("Тип объекта") or row.get("object_type_name"),
            "property_count": 0,
            "conflict_count": 0,
        } for row in registry]

    status_counts: dict[str, int] = {}
    for row in comparisons:
        status = str(row.get("status") or "НЕ ОПРЕДЕЛЕНО")
        status_counts[status] = status_counts.get(status, 0) + 1

    characteristic_count = sum(
        len(row.get("characteristics") or [])
        for row in passports
        if isinstance(row, dict)
    )
    return {
        "version": RECOVERY_VERSION,
        "source": source,
        "snapshot_id": snapshot_id,
        "components": {
            "trusted_registry": {"field": "consolidated_registry", "count": len(registry)},
            "passports": {"field": "object_passports", "count": len(passports)},
            "project_understanding": {"field": "project_understanding", "count": len(objects)},
            "cross_section": {"field": "result.comparisons", "count": len(comparisons)},
        },
        "object_index": object_index,
        "summary": {
            "objects": len(registry),
            "passports": len(passports),
            "characteristics": characteristic_count,
            "cross_section_checks": len(comparisons),
            "comparison_statuses": status_counts,
            "source_pdf_required": False,
        },
    }


def _rows(value: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in (value or []) if isinstance(row, dict)]


def _first(documents: list[dict[str, Any]]) -> dict[str, Any]:
    return documents[0] if documents and isinstance(documents[0], dict) else {}


def _embedded_quality_gate_inputs(first: dict[str, Any]) -> dict[str, Any]:
    snapshot = first.get("analysis_snapshot")
    if not isinstance(snapshot, dict):
        return {}
    inputs = snapshot.get("quality_gate_inputs")
    return dict(inputs) if isinstance(inputs, dict) else {}


def recover_project_knowledge(
    documents: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Restore deterministic project knowledge from the portable snapshot.

    18.4.x already stored trusted objects and raw cross-section comparisons
    inside analysis_snapshot.quality_gate_inputs. The old restore path did not
    lift them back into the engineer-facing model.
    """
    first = _first(documents)
    if not first:
        return {"version": RECOVERY_VERSION, "changed": False, "reason": "NO_DOCUMENT"}

    restored = bool(first.get("snapshot_restored"))
    if not restored and not force:
        return {"version": RECOVERY_VERSION, "changed": False, "reason": "NOT_SNAPSHOT"}

    inputs = _embedded_quality_gate_inputs(first)
    embedded_registry = _rows(inputs.get("object_registry"))
    embedded_comparisons = _rows(inputs.get("comparisons"))

    changed = False
    recovered: list[str] = []

    consolidated = _rows(first.get("consolidated_registry"))
    if (force or not consolidated) and embedded_registry:
        first["consolidated_registry"] = embedded_registry
        first["restored_trusted_registry"] = embedded_registry
        consolidated = embedded_registry
        changed = True
        recovered.append("trusted_object_registry")

    registry = consolidated or _rows(first.get("composition_baseline")) or embedded_registry

    if embedded_comparisons and (force or not comparisons):
        comparisons[:] = embedded_comparisons
        changed = True
        recovered.append("cross_section_comparisons")

    comparison_rows = list(comparisons or embedded_comparisons)

    passports = _rows(first.get("object_passports"))
    if registry and (force or not passports):
        passport_objects = build_object_passports(registry, findings, comparison_rows)
        passports = [item.to_dict() for item in passport_objects]
        first["object_passports"] = passports
        first["object_passport_summary"] = passport_summary(passport_objects)
        changed = True
        recovered.append("object_passports")

    model = first.get("project_understanding")
    if registry and (force or not isinstance(model, dict) or not model.get("objects")):
        model = build_project_object_model(registry, findings)
        first["project_understanding"] = model
        first["project_understanding_quality"] = understanding_quality(model)
        changed = True
        recovered.append("project_understanding")

    if registry:
        first["object_registry_summary"] = {
            **dict(first.get("object_registry_summary") or {}),
            "registry_positions": len(registry),
            "physical_objects": sum(
                max(1, int(float(row.get("Количество", 1) or 1)))
                if str(row.get("Количество", 1) or 1).replace(".", "", 1).isdigit()
                else 1
                for row in registry
            ),
            "restored_from_snapshot": True,
        }

    knowledge_model = build_project_knowledge_manifest(
        registry=registry,
        passports=passports,
        project_understanding=first.get("project_understanding") or {},
        comparisons=comparison_rows,
        snapshot_id=str((first.get("analysis_snapshot") or {}).get("snapshot_id") or ""),
        source="analysis_snapshot.quality_gate_inputs",
    )
    first["project_knowledge_model"] = knowledge_model
    first["project_knowledge_recovery"] = {
        "version": RECOVERY_VERSION,
        "changed": changed,
        "recovered": recovered,
        **knowledge_model["summary"],
    }

    return dict(first["project_knowledge_recovery"])
