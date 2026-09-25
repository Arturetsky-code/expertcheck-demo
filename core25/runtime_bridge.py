from __future__ import annotations

from hashlib import sha1
import re
from typing import Any, Iterable, Mapping

from .contracts import DecisionState, Evidence25, VerificationResult25
from .pipeline import verify_assignment


_DECISION_PUBLIC = {
    DecisionState.COMPLIANT: ("Соответствует заданию", "VERIFIED_OK", "L5"),
    DecisionState.NONCOMPLIANT: ("Выявлено отклонение", "PROJECT_FINDING", "L5"),
    DecisionState.REVIEW: ("Требует проверки", "REVIEW_QUESTION", "L0"),
    DecisionState.LIMITATION: ("Не проверено системой", "SYSTEM_LIMITATION", "L0"),
    DecisionState.NOT_APPLICABLE: ("Не применимо", "NOT_APPLICABLE", "L0"),
}

_SECTION_PATTERNS = (
    ("ПЗУ", ("пзу", "схема планировочной")),
    ("АР", ("_ар", "№3_ар", "архитектурн")),
    ("КР", ("_кр", "№4_кр", "конструктивн")),
    ("ТХ", ("_тх", "№6_тх", "технологическ")),
    ("ИОС1", ("иос1", "электроснабжен")),
    ("ИОС2", ("иос2", "водоснабжен", "водоотведен")),
    ("ПЗ", ("_пз.", "№1_пз", "пояснительн")),
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _runtime_requirement(raw: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(raw)
    contract = dict(item.get("evidence_contract_v2") or {})
    if contract.get("scope") and not item.get("requirement_scope"):
        item["requirement_scope"] = contract["scope"]
    if contract.get("expected_sections") and not item.get("expected_sections"):
        item["expected_sections"] = list(contract["expected_sections"])

    kind = _text(item.get("verification_kind") or item.get("requirement_type")).upper()
    aliases = {
        "VALUE_COMPARISON": "TYPED_VALUE",
        "PRESENCE_REQUIREMENT": "PRESENCE",
    }
    item["verification_kind"] = aliases.get(kind, kind)
    executor=_text(item.get("coverage_executor"))
    if executor == "NORMATIVE_DESIGN_ADOPTION_EXECUTOR":
        item["verification_kind"] = "NORMATIVE_DESIGN_ADOPTION"
    elif executor == "EQUIPMENT_IDENTITY_AND_QUANTITY":
        item["verification_kind"] = "EQUIPMENT_IDENTITY_COMPARISON"
    elif executor == "IDENTIFICATION_ATTRIBUTE_COMPARISON_EXECUTOR":
        item["verification_kind"] = "IDENTIFICATION_ATTRIBUTE_COMPARISON"
        item["requirement_scope"] = "PROJECT_GLOBAL"
    elif executor == "DYNAMIC_FOUNDATION_NORMATIVE_EXECUTOR":
        item["verification_kind"] = "DYNAMIC_FOUNDATION_NORMATIVE"
        if _text(item.get("requirement_scope")).upper() in {"", "UNRESOLVED"}:
            item["requirement_scope"] = "PROJECT_GLOBAL"
    return item


def _section(document: str, candidate: Mapping[str, Any]) -> str:
    direct = _text(candidate.get("document_type") or candidate.get("section"))
    if direct:
        return direct
    low = document.replace("ё", "е").casefold()
    for section, markers in _SECTION_PATTERNS:
        if any(marker.casefold() in low for marker in markers):
            return section
    return ""


def _evidence_id(requirement_id: str, candidate: Mapping[str, Any]) -> str:
    raw = "|".join(
        (
            requirement_id,
            _text(candidate.get("document")),
            _text(candidate.get("page")),
            _text(candidate.get("parameter_code")),
            _text(candidate.get("value")),
            _text(candidate.get("context") or candidate.get("exact_clause")),
        )
    )
    return "E25R-" + sha1(raw.encode("utf-8", "ignore")).hexdigest()[:16].upper()


def _candidate_evidence(requirement: Mapping[str, Any]) -> tuple[Evidence25, ...]:
    requirement_id = _text(requirement.get("requirement_id") or requirement.get("id"))
    scope = _text(
        requirement.get("requirement_scope")
        or (requirement.get("evidence_contract_v2") or {}).get("scope")
    ).upper()
    result: list[Evidence25] = []
    for candidate in requirement.get("directed_evidence_candidates") or ():
        if not isinstance(candidate, Mapping):
            continue
        if _text(candidate.get("evidence_state")).lower() != "verified_candidate":
            continue
        comparison_subject_match = bool(
            candidate.get("comparison_subject_match") is True
            and _text(candidate.get("evidence_kind")).upper() == "EQUIPMENT_REGISTER_COMPARISON"
        )
        if (
            scope in {"OBJECT_SPECIFIC", "EQUIPMENT_SPECIFIC"}
            and candidate.get("owner_match") is not True
            and not comparison_subject_match
        ):
            continue

        document = _text(candidate.get("document"))
        page = candidate.get("page")
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = None
        fragment = _text(
            candidate.get("context")
            or candidate.get("exact_clause")
            or candidate.get("source_trace")
        )
        result.append(
            Evidence25(
                evidence_id=_evidence_id(requirement_id, candidate),
                document=document,
                section=_section(document, candidate),
                page=page,
                fragment=fragment,
                source_kind=_text(candidate.get("source_kind")) or "PAGE_TEXT",
                addressable=bool(document and page and fragment),
                canonical=True,
                trusted=True,
                confidence=float(candidate.get("score") or 0) / 100.0,
                metadata={
                    "requirement_id": requirement_id,
                    "owner_name": _text(candidate.get("object")),
                    "parameter_code": _text(candidate.get("parameter_code")).upper(),
                    "value": candidate.get("value"),
                    "unit": _text(candidate.get("unit")),
                    "project_value": candidate.get("value"),
                    "project_unit": _text(candidate.get("unit")),
                    "owner_match": candidate.get("owner_match"),
                    "unit_compatible": candidate.get("unit_compatible"),
                    "legacy_evidence_kind": candidate.get("evidence_kind"),
                    "coverage_executor": candidate.get("coverage_executor"),
                    "comparison_subject_match": candidate.get("comparison_subject_match"),
                    "equipment_class": candidate.get("equipment_class"),
                    "verified_difference": candidate.get("verified_difference"),
                    "mismatch_fields": tuple(candidate.get("mismatch_fields") or ()),
                    "task_brand": candidate.get("task_brand"),
                    "project_brand": candidate.get("project_brand"),
                    "brand_similarity": candidate.get("brand_similarity"),
                    "same_model": candidate.get("same_model"),
                    "task_models": tuple(candidate.get("task_models") or ()),
                    "project_models": tuple(candidate.get("project_models") or ()),
                    "task_quantity": candidate.get("task_quantity"),
                    "project_quantity": candidate.get("project_quantity"),
                    "position": candidate.get("position"),
                    "exact_position_match": candidate.get("exact_position_match"),
                    "required_responsibility_class": candidate.get("required_responsibility_class"),
                    "observed_responsibility_class": candidate.get("observed_responsibility_class"),
                    "required_reliability_coefficient": candidate.get("required_reliability_coefficient"),
                    "observed_reliability_coefficient": candidate.get("observed_reliability_coefficient"),
                    "negative_assertion": candidate.get("negative_assertion"),
                    "matched_normative_refs": tuple(candidate.get("matched_normative_refs") or ()),
                    "required_normative_refs": tuple(candidate.get("required_normative_refs") or ()),
                    "matched_terms": tuple(candidate.get("matched_terms") or ()),
                    "proof_slot": candidate.get("proof_slot"),
                    "normative_design_adoption": candidate.get("normative_design_adoption"),
                    "dynamic_foundation_normative": candidate.get("dynamic_foundation_normative"),
                    "foundation_solution": candidate.get("foundation_solution"),
                    "specialized_norm_adoption": candidate.get("specialized_norm_adoption"),
                    "dynamic_calculation": candidate.get("dynamic_calculation"),
                    "dynamic_foundation_drawing": candidate.get("dynamic_foundation_drawing"),
                    "limit_value": candidate.get("limit_value"),
                    "limit_unit": candidate.get("limit_unit"),
                    "concept": candidate.get("concept"),
                    "design_determined_subject": candidate.get("design_determined_subject"),
                    "structured_project_fact": candidate.get("structured_project_fact"),
                    "drawing_fact_code": candidate.get("drawing_fact_code"),
                    "drawing_owner_name": candidate.get("drawing_owner_name"),
                    "drawing_owner_binding": candidate.get("drawing_owner_binding"),
                    "drawing_required_position": candidate.get("drawing_required_position"),
                    "drawing_facade_views": tuple(candidate.get("drawing_facade_views") or ()),
                    "drawing_facade_view_count": candidate.get("drawing_facade_view_count"),
                    "drawing_roof_proven": candidate.get("drawing_roof_proven"),
                    "drawing_structural_frame_corroborated": candidate.get("drawing_structural_frame_corroborated"),
                    "drawing_enclosure_conflict": candidate.get("drawing_enclosure_conflict"),
                    "drawing_corroborating_document": candidate.get("drawing_corroborating_document"),
                    "drawing_corroborating_page": candidate.get("drawing_corroborating_page"),
                    "observed_value": candidate.get("observed_value"),
                    "observed_unit": candidate.get("observed_unit"),
                    "condition_id": candidate.get("condition_id"),
                    "condition_label": candidate.get("condition_label"),
                },
            )
        )
    return tuple(result)


def _known_objects(requirements: Iterable[Mapping[str, Any]], object_registry: Iterable[Mapping[str, Any]]) -> dict[str, tuple[str, ...]]:
    aliases: dict[str, list[str]] = {}

    def add(object_id: Any, *names: Any) -> None:
        oid = _text(object_id)
        if not oid:
            return
        bucket = aliases.setdefault(oid, [])
        for value in names:
            name = _text(value)
            if name and name not in bucket:
                bucket.append(name)

    for raw in requirements:
        add(
            raw.get("object_id") or raw.get("target_object_id"),
            raw.get("object_name") or raw.get("target_object"),
        )
    for raw in object_registry or ():
        add(
            raw.get("object_id") or raw.get("id") or raw.get("Ключ"),
            raw.get("name") or raw.get("object_name") or raw.get("Наименование объекта"),
            raw.get("alias"),
        )
    return {key: tuple(values) for key, values in aliases.items()}


def _public_row(raw: Mapping[str, Any], result: VerificationResult25) -> dict[str, Any]:
    status, final_kind, evidence_level = _DECISION_PUBLIC[result.decision.state]
    evidence_by_id = {item.evidence_id: item for item in result.trace.evidence}
    proof_evidence = [
        evidence_by_id[item]
        for item in result.trace.proof.evidence_ids
        if item in evidence_by_id
    ]
    verification_evidence = [
        {
            "evidence_id": item.evidence_id,
            "document": item.resolved_document,
            "page": item.page,
            "fragment": item.fragment,
            "source_kind": item.source_kind,
        }
        for item in proof_evidence
    ]
    rendered = [
        f"{item['document']}, стр. {item['page']}: {item['fragment']}"
        for item in verification_evidence
    ]
    row = dict(raw)
    row.update(
        {
            "requirement_id": result.requirement.requirement_id,
            "requirement_text": result.requirement.text,
            "status": status,
            "final_verification_kind": final_kind,
            "verification_kind": final_kind,
            "evidence_level": evidence_level,
            "decision_basis": result.decision.reason_code or result.trace.proof.reason_code,
            "evidence": rendered,
            "verification_evidence": verification_evidence,
            "proof_id": result.trace.proof.proof_id,
            "trace_id": result.trace.trace_id,
            "proof_state": result.trace.proof.state.value,
            "core25_decision": result.decision.state.value,
            "core25_reason_code": result.trace.proof.reason_code,
            "core25_engine_version": "25.2-alpha2-evidence-admission",
            "core25_integrity_gate_state": "PASSED",
            "match_confidence": 1.0 if result.decision.is_categorical else 0.0,
        }
    )
    return row


def run_assignment_runtime(
    requirements: Iterable[Mapping[str, Any]],
    *,
    object_registry: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    raw_requirements = [dict(item) for item in requirements or () if isinstance(item, Mapping)]
    known_objects = _known_objects(raw_requirements, object_registry or ())
    results: list[VerificationResult25] = []
    admission_audits: list[dict[str, Any]] = []

    for raw in raw_requirements:
        requirement = _runtime_requirement(raw)
        raw_candidates = [
            dict(item) for item in raw.get("directed_evidence_candidates") or ()
            if isinstance(item, Mapping)
        ]
        evidence = _candidate_evidence(requirement)
        current = verify_assignment((requirement,), evidence, known_objects)
        result = current[0]
        results.append(result)

        verified_candidates = sum(
            _text(item.get("evidence_state")).lower() == "verified_candidate"
            for item in raw_candidates
        )
        qualified_count = len(result.trace.evidence)
        binding_counts: dict[str, int] = {}
        binding_reasons: dict[str, int] = {}
        for binding in result.trace.bindings:
            state = binding.state.value
            binding_counts[state] = binding_counts.get(state, 0) + 1
            code = _text(binding.reason_code) or "UNSPECIFIED"
            binding_reasons[code] = binding_reasons.get(code, 0) + 1
        bound_count = binding_counts.get("BOUND", 0)

        if result.trace.proof.is_categorical:
            stage = "PROVEN"
        elif not raw_candidates:
            stage = "NO_CANDIDATE"
        elif not verified_candidates:
            stage = "CANDIDATE_NOT_VERIFIED"
        elif not qualified_count:
            stage = "CANONICAL_OR_SECTION_FILTER"
        elif not bound_count:
            stage = "BINDING_BLOCKED"
        else:
            stage = "PROOF_BLOCKED"

        admission_audits.append({
            "stage": stage,
            "raw_candidates": len(raw_candidates),
            "verified_candidates": verified_candidates,
            "qualified_evidence": qualified_count,
            "binding_counts": binding_counts,
            "binding_reason_codes": binding_reasons,
            "proof_reason_code": result.trace.proof.reason_code,
        })

    rows = []
    for raw, result, audit in zip(raw_requirements, results, admission_audits):
        row = _public_row(raw, result)
        row.update({
            "core25_admission_stage": audit["stage"],
            "core25_raw_candidate_count": audit["raw_candidates"],
            "core25_verified_candidate_count": audit["verified_candidates"],
            "core25_qualified_evidence_count": audit["qualified_evidence"],
            "core25_binding_counts": dict(audit["binding_counts"]),
            "core25_binding_reason_codes": dict(audit["binding_reason_codes"]),
        })
        rows.append(row)
    summary = {
        "total": len(rows),
        "compliant": sum(row["final_verification_kind"] == "VERIFIED_OK" for row in rows),
        "deviation": sum(row["final_verification_kind"] == "PROJECT_FINDING" for row in rows),
        "unconfirmed": sum(row["final_verification_kind"] == "REVIEW_QUESTION" for row in rows),
        "semantic": 0,
        "not_checked": sum(row["final_verification_kind"] == "SYSTEM_LIMITATION" for row in rows),
    }
    categorical = summary["compliant"] + summary["deviation"]
    summary["evidence_coverage_pct"] = round(100.0 * categorical / max(1, summary["total"]), 1)
    summary["engine"] = "core25"
    summary["engine_version"] = "25.2-alpha2-evidence-admission"

    return {
        "engine": "core25",
        "engine_version": "25.2-alpha2-evidence-admission",
        "results": tuple(results),
        "rows": rows,
        "summary": summary,
    }



def public_assignment_payload(document: Mapping[str, Any] | None):
    """Select the public Assignment surface.

    New 25.0 analyses are fail-closed: if the runtime payload exists, its rows
    and summary are authoritative even when the bridge recorded an error.
    Legacy snapshots without a 25.0 payload remain readable.
    """
    source = dict(document or {})
    if "assignment_core25_runtime" in source:
        runtime = dict(source.get("assignment_core25_runtime") or {})
        runtime.setdefault("engine", "core25")
        rows = list(source.get("assignment_core25_compliance") or [])
        summary = dict(source.get("assignment_core25_summary") or {})
        if runtime.get("error") and not summary.get("error"):
            summary["error"] = runtime["error"]
        return rows, summary, runtime

    return (
        list(source.get("assignment_compliance") or []),
        dict(source.get("assignment_compliance_summary") or {}),
        {"engine": "legacy_snapshot", "engine_version": "", "error": ""},
    )
