from __future__ import annotations

from typing import Any

from core20.model import Evidence, Requirement

from ..contracts import Domain, Evidence25, Requirement25
from ..requirement_engine import normalize_assignment_requirement, normalize_scope, normalize_verification_kind


def _domain(value: Any) -> Domain:
    raw = " ".join(str(value or "").strip().casefold().replace("ё", "е").split())
    if raw in {"assignment", "задание", "задание на проектирование"}:
        return Domain.ASSIGNMENT
    if raw in {"normative", "нтд", "normative_requirement"}:
        return Domain.NORMATIVE
    if raw in {"checklist", "чек-лист", "чек лист"}:
        return Domain.CHECKLIST
    if raw in {"cross_section", "cross-section", "межраздельная сверка"}:
        return Domain.CROSS_SECTION
    raise ValueError(f"Unsupported core20 requirement domain: {value!r}")


def adapt_requirement(req: Requirement) -> Requirement25:
    metadata = dict(req.metadata or {})
    domain = _domain(req.domain)
    if domain is Domain.ASSIGNMENT:
        raw = {
            **metadata,
            "requirement_id": req.requirement_id,
            "requirement_text": req.text,
            "verification_kind": req.verification_kind,
            "target_object_id": req.target_object_id,
            "expected_parameter_code": req.expected_parameter_code,
            "expected_evidence_route": tuple(req.expected_evidence_route or ()),
            "source_document": metadata.get("source_document") or metadata.get("document") or "",
            "source_page": metadata.get("source_page") if metadata.get("source_page") is not None else metadata.get("page"),
            "source_fragment": metadata.get("source_fragment") or metadata.get("fragment") or req.text,
        }
        return normalize_assignment_requirement(raw)

    verification_kind = normalize_verification_kind(req.verification_kind)
    target_object_id = str(req.target_object_id or "").strip() or None
    scope = normalize_scope(
        metadata.get("scope") or metadata.get("requirement_scope"),
        target_object_id=target_object_id,
        verification_kind=verification_kind,
    )
    return Requirement25(
        requirement_id=req.requirement_id,
        domain=domain,
        text=req.text,
        scope=scope,
        verification_kind=verification_kind,
        target_object_id=target_object_id,
        parameter_code=str(req.expected_parameter_code or "").strip().upper(),
        required_value=metadata.get("required_value"),
        unit=str(metadata.get("unit") or metadata.get("required_unit") or "").strip(),
        expected_sections=tuple(str(x).strip() for x in (req.expected_evidence_route or ()) if str(x).strip()),
        source_document=str(metadata.get("source_document") or metadata.get("document") or "").strip(),
        source_page=metadata.get("source_page") if metadata.get("source_page") is not None else metadata.get("page"),
        source_fragment=str(metadata.get("source_fragment") or metadata.get("fragment") or req.text).strip(),
        metadata=metadata,
    )


def adapt_evidence(ev: Evidence) -> Evidence25:
    metadata = dict(ev.metadata or {})
    document = str(ev.document_name or ev.document_id or "").strip()
    source_kind = str(ev.source_kind or metadata.get("source_kind") or "").strip()
    source_role = str(metadata.get("source_role") or metadata.get("role") or "").strip()
    canonical = not bool(
        metadata.get("is_toc")
        or metadata.get("is_index")
        or metadata.get("heading_only")
        or source_kind.upper() in {"TABLE_OF_CONTENTS", "INDEX", "DOCUMENT_TITLE", "FILE_NAME_ONLY"}
    )
    return Evidence25(
        evidence_id=ev.evidence_id,
        document=document,
        document_name=document,
        section=str(ev.section or "").strip(),
        page=ev.page,
        table_id=str(ev.table_id or "").strip(),
        row_id=str(ev.row_id or "").strip(),
        fragment=str(ev.fragment or "").strip(),
        source_kind=source_kind,
        source_role=source_role,
        addressable=bool(ev.addressable),
        canonical=canonical,
        trusted=bool(ev.trusted),
        confidence=ev.confidence,
        metadata=metadata,
    )
