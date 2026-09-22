from __future__ import annotations

from typing import Any, Mapping

from .contracts import Domain, Requirement25, Scope


_OBJECT_KIND_MARKERS = ("OBJECT", "EQUIPMENT", "ОБЪЕКТ", "ОБОРУДОВАН")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _upper(value: Any) -> str:
    return _text(value).upper()


def _tuple_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        item = value.strip()
        return (item,) if item else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    item = str(value).strip()
    return (item,) if item else ()


def normalize_scope(
    value: Any,
    *,
    target_object_id: Any = None,
    verification_kind: Any = None,
) -> Scope:
    raw = _upper(value)
    if raw in {
        "PROJECT_GLOBAL", "PROJECT", "GLOBAL", "ПРОЕКТ",
        "SITE_SPECIFIC", "SYSTEM_SPECIFIC", "DOCUMENT_SPECIFIC",
    }:
        # Core25 ownership semantics distinguish project-global vs exact object
        # ownership. Site/system/document scopes do not require an exact object id
        # and are therefore treated as global for binding while their original
        # scope remains available in requirement metadata.
        return Scope.PROJECT_GLOBAL
    if raw in {
        "OBJECT_SPECIFIC", "EQUIPMENT_SPECIFIC", "OBJECT", "EQUIPMENT",
        "ОБЪЕКТ", "ОБОРУДОВАНИЕ",
    }:
        return Scope.OBJECT_SPECIFIC
    if _text(target_object_id):
        return Scope.OBJECT_SPECIFIC
    kind = _upper(verification_kind)
    if any(marker in kind for marker in _OBJECT_KIND_MARKERS):
        return Scope.OBJECT_SPECIFIC
    return Scope.UNRESOLVED


def normalize_verification_kind(value: Any) -> str:
    raw = _upper(value)
    aliases = {
        "VALUE": "TYPED_VALUE",
        "NUMERIC_VALUE": "TYPED_VALUE",
        "NUMBER": "TYPED_VALUE",
        "TABLE_VALUE": "TABLE_CELL_VALUE",
        "TOPOLOGY": "RESERVE_TOPOLOGY",
        "VALUE_COMPARISON": "TYPED_VALUE",
        "PRESENCE_REQUIREMENT": "PRESENCE",
        "SEMANTIC_ENGINEERING": "PRESENCE",
        "DESIGN_DETERMINED": "PRESENCE",
        "PROHIBITION_OR_NOT_REQUIRED": "NEGATIVE_ASSERTION",
        "APPLICABILITY_DECLARATION": "NEGATIVE_ASSERTION",
        "NORMATIVE_COMPLIANCE": "NORMATIVE_ASSERTION",
        "NORMATIVE_CLAUSE": "NORMATIVE_ASSERTION",
        "SOURCE_TRACEABILITY": "TRACEABILITY",
        "CROSS_DOCUMENT_TRACE": "TRACEABILITY",
        "SET_COMPARISON": "SET_COMPARISON",
    }
    return aliases.get(raw, raw)


def normalize_assignment_requirement(raw: Mapping[str, Any]) -> Requirement25:
    requirement_id = _text(raw.get("requirement_id") or raw.get("id"))
    text = _text(raw.get("requirement_text") or raw.get("text"))
    verification_kind = normalize_verification_kind(
        raw.get("verification_kind") or raw.get("requirement_type") or raw.get("type")
    )
    target_object_id = _text(
        raw.get("target_object_id") or raw.get("object_id") or raw.get("target_object")
    ) or None
    scope = normalize_scope(
        raw.get("requirement_scope") or raw.get("scope"),
        target_object_id=target_object_id,
        verification_kind=verification_kind,
    )
    parameter_code = _upper(raw.get("parameter_code") or raw.get("expected_parameter_code"))
    expected_sections = _tuple_strings(
        raw.get("expected_sections") or raw.get("expected_evidence_route")
    )
    source_document = _text(raw.get("source_document") or raw.get("document") or raw.get("document_name"))
    source_page = raw.get("source_page") if raw.get("source_page") is not None else raw.get("page")
    try:
        source_page = int(source_page) if source_page is not None else None
    except (TypeError, ValueError):
        source_page = None

    source_fragment = _text(raw.get("source_fragment") or raw.get("fragment") or text)
    required_value = raw.get("required_value")
    unit = _text(raw.get("unit") or raw.get("required_unit"))

    return Requirement25(
        requirement_id=requirement_id,
        domain=Domain.ASSIGNMENT,
        text=text,
        scope=scope,
        verification_kind=verification_kind,
        target_object_id=target_object_id,
        parameter_code=parameter_code,
        required_value=required_value,
        unit=unit,
        expected_sections=expected_sections,
        source_document=source_document,
        source_page=source_page,
        source_fragment=source_fragment,
        metadata=dict(raw),
    )
