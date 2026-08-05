from __future__ import annotations

from collections import defaultdict
from typing import Any

from .knowledge_engine import default_knowledge_engine
from .normalization import normalize_text
from .object_semantics import is_service_object_candidate, object_candidate_evidence


def discover_object_candidates(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Создает объектные кандидаты из инженерных характеристик.

    Это помогает проектам новых отраслей: если legacy-парсер не создал OBJECT_ENTRY,
    но один и тот же инженерный объект встречается в нескольких разделах вместе с ТЭП,
    он получает подтвержденного кандидата. Названия документов и служебные строки
    исключаются до группировки.
    """
    engine = default_knowledge_engine()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    audit: list[dict[str, Any]] = []
    for item in findings:
        code = str(item.get("parameter_code") or "")
        if code in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            continue
        name = str(item.get("object_hint") or item.get("semantic_anchor_name") or "").strip()
        if not name or name == "Не определён":
            continue
        probe = dict(item)
        probe["value_text"] = name
        service, reasons = is_service_object_candidate(probe)
        if service:
            audit.append({"name": name, "decision": "отклонено", "reasons": "; ".join(reasons)})
            continue
        profile = engine.classify(name)
        if profile.code == "GENERIC_OBJECT" or profile.confidence < 0.68:
            continue
        position = str(item.get("genplan_position") or "").strip()
        key = (position, normalize_text(name))
        grouped[key].append(item)

    added: list[dict[str, Any]] = []
    for (position, _), rows in grouped.items():
        sections = {str(x.get("document_type") or x.get("section") or "") for x in rows if x.get("document_type") or x.get("section")}
        profile = engine.classify(rows[0].get("object_hint") or rows[0].get("semantic_anchor_name"))
        strong_context = any(any(token in normalize_text(x.get("structural_zone") or x.get("table_type") or "") for token in ("тэп", "экспликац", "состав объекта")) for x in rows)
        accepted = bool(position) or len(sections) >= 2 or strong_context
        audit.append({
            "name": rows[0].get("object_hint") or rows[0].get("semantic_anchor_name"),
            "position": position,
            "profile": profile.name,
            "sections": ", ".join(sorted(sections)),
            "decision": "принято" if accepted else "отклонено",
            "reasons": "позиция/несколько разделов/инженерная таблица" if accepted else "один слабый источник",
        })
        if not accepted:
            continue
        source = max(rows, key=lambda x: float(x.get("core2_confidence") or x.get("confidence") or 0.0))
        added.append({
            "parameter_code": "OBJECT_CANDIDATE",
            "parameter_name": "Объект проекта",
            "value_text": str(source.get("object_hint") or source.get("semantic_anchor_name") or ""),
            "object_hint": str(source.get("object_hint") or source.get("semantic_anchor_name") or ""),
            "genplan_position": position,
            "document": str(source.get("document") or ""),
            "document_type": str(source.get("document_type") or source.get("section") or ""),
            "page": source.get("page"),
            "confidence": max(0.72, profile.confidence),
            "core2_confidence": max(0.72, profile.confidence),
            "match_method": "Universal Object Discovery: подтверждение по инженерным характеристикам",
            "structural_zone": "объект подтвержден ТЭП в нескольких источниках" if len(sections) >= 2 else "объектная строка инженерной таблицы",
            "record_kind": "project_object",
            "object_type_code": profile.code,
            "object_type_name": profile.name,
            "object_profile_properties": list(profile.properties),
        })
    return added, audit
