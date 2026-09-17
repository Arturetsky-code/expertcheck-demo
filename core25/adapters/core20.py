from __future__ import annotations

import re
from math import isfinite
from typing import Any

from core20.model import Evidence, Requirement
from core20.parameter_contracts import (
    compare_values as _compare_values,
    numeric as _numeric,
    unit as _unit,
)

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


def normalize_unit(value: Any) -> str:
    """Use the stable 20.0 engineering unit normalizer behind the 25.0 adapter boundary."""
    return _unit(value)


def numeric_value(value: Any) -> float | None:
    """Parse a numeric value through 20.0 but reject NaN/±inf at the 25.0 boundary."""
    parsed = _numeric(value)
    if parsed is None or not isfinite(parsed):
        return None
    return parsed


def compare_typed_values(values: list[float], required: float) -> tuple[str, float]:
    """Compare already owner/parameter-bound values with stable 20.0 tolerances."""
    return _compare_values(values, required)


def _topology_count(text: str, label: str) -> int | None:
    if label == "working":
        keywords = r"(?:рабоч\w*|в\s+работе)"
    else:
        keywords = r"(?:резерв\w*)"

    before = re.search(rf"(?<!\d)(\d{{1,2}})\s*(?:шт\.?\s*)?{keywords}", text, re.I)
    if before:
        return int(before.group(1))

    # Deliberately accept only a number immediately after the semantic label.
    # A wider gap can cross into the next topology clause, e.g.
    # "2 рабочих насоса и 1 резервный" and incorrectly bind the reserve count
    # to the working label.
    after = re.search(rf"{keywords}\s*(?:[:=\-–—]\s*)?(\d{{1,2}})(?!\d)", text, re.I)
    if after:
        return int(after.group(1))
    return None


def parse_reserve_topology(text: str) -> tuple[int, int] | None:
    """Parse working/reserve counts conservatively at the 25.0 adapter boundary.

    Core20's broader reverse pattern may cross from one clause into the next and
    overwrite an already-correct working count. Core25 fails closed instead of
    accepting an ambiguous topology.
    """
    normalized = " ".join(str(text or "").replace("ё", "е").casefold().split())
    working = _topology_count(normalized, "working")
    reserve = _topology_count(normalized, "reserve")
    if working is None or reserve is None:
        return None
    return working, reserve
