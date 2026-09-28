from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from pathlib import Path

from core.coverage_breakthrough import attach_coverage_executor_evidence
from core.directed_evidence import attach_directed_evidence
from core.page_evidence_store import is_assignment_source
from core.identification_attributes import enrich_identification_requirements, identity_context
from core25.runtime_bridge import run_assignment_runtime


_ARCHETYPE_BY_EXECUTOR = {
    "GENERIC_PRESENCE_EXECUTOR": "PRESENCE",
    "FENCING_COMPOSITE_EXECUTOR": "COMPOSITE_PRESENCE",
    "OPEN_CANOPY_DRAWING_EXECUTOR": "PRESENCE_PLUS_GRAPHIC_CONFIRMATION",
    "LIGHTING_COMPOSITE_EXECUTOR": "COMPOSITE_ENGINEERING",
    "LIGHTNING_GROUNDING_COMPOSITE_EXECUTOR": "COMPOSITE_ENGINEERING",
    "NEGATIVE_APPLICABILITY_EXECUTOR": "NEGATIVE_APPLICABILITY",
    "DESIGN_DETERMINED_EXECUTOR": "DESIGN_DETERMINED",
    "LANDSCAPING_DESIGN_DETERMINED_EXECUTOR": "DESIGN_DETERMINED_MULTI_EVIDENCE",
    "NORMATIVE_ASSERTION_EXECUTOR": "NORMATIVE_ASSERTION",
    "NORMATIVE_DESIGN_ADOPTION_EXECUTOR": "NORMATIVE_DESIGN_ADOPTION",
    "DYNAMIC_FOUNDATION_NORMATIVE_EXECUTOR": "NORMATIVE_CALCULATION_GRAPHIC",
    "EQUIPMENT_IDENTITY_AND_QUANTITY": "EQUIPMENT_IDENTITY_QUANTITY",
    "CAPACITY_AND_PROCESS_TOPOLOGY": "CAPACITY_PROCESS_TOPOLOGY",
    "IDENTIFICATION_ATTRIBUTE_COMPARISON_EXECUTOR": "IDENTIFICATION_ATTRIBUTE_COMPARISON",
    "CROSS_DOCUMENT_TRACE_EXECUTOR": "CROSS_DOCUMENT_TRACE",
}

_ARCHETYPE_BY_REASON = {
    "TYPED_VALUE_MATCH": "TYPED_VALUE_COMPARISON",
    "ASSIGNMENT_PRESENCE_CONFIRMED": "PRESENCE",
    "ASSIGNMENT_DESIGN_VALUE_CONFIRMED": "DESIGN_DETERMINED",
    "FACTUAL_NORMATIVE_ASSERTION_CONFIRMED": "NORMATIVE_ASSERTION",
    "NEGATIVE_APPLICABILITY_CONFIRMED": "NEGATIVE_APPLICABILITY",
    "ASSIGNMENT_NORMATIVE_DESIGN_ADOPTION_CONFIRMED": "NORMATIVE_DESIGN_ADOPTION",
    "ASSIGNMENT_DYNAMIC_FOUNDATION_NORMATIVE_CONFIRMED": "NORMATIVE_CALCULATION_GRAPHIC",
    "ASSIGNMENT_CROSS_DOCUMENT_TRACE_CONFIRMED": "CROSS_DOCUMENT_TRACE",
}


def _universal_archetype(row: dict) -> str:
    executor = str(row.get("coverage_executor") or "")
    reason = str(row.get("core25_reason_code") or "")
    return _ARCHETYPE_BY_EXECUTOR.get(executor) or _ARCHETYPE_BY_REASON.get(reason) or "UNCLASSIFIED_VERIFIED"


def _archetype_summary(rows: list[dict]) -> dict:
    verified = [row for row in rows if row.get("final_verification_kind") == "VERIFIED_OK"]
    counts = Counter(_universal_archetype(row) for row in verified)
    unclassified = int(counts.pop("UNCLASSIFIED_VERIFIED", 0))
    return {
        "universal_archetypes": len(counts),
        "verified_requirements_classified": sum(counts.values()),
        "verified_requirements_unclassified": unclassified,
        "archetypes": dict(sorted(counts.items())),
    }


def _categorical_archetype_summary(rows: list[dict]) -> dict:
    categorical = [
        row for row in rows
        if row.get("final_verification_kind") in {"VERIFIED_OK", "PROJECT_FINDING"}
    ]
    counts = Counter(_universal_archetype(row) for row in categorical)
    unclassified = int(counts.pop("UNCLASSIFIED_VERIFIED", 0))
    return {
        "universal_archetypes": len(counts),
        "categorical_requirements_classified": sum(counts.values()),
        "categorical_requirements_unclassified": unclassified,
        "archetypes": dict(sorted(counts.items())),
    }


def _row_summary(row: dict) -> dict:
    return {
        "requirement_id": row.get("requirement_id"),
        "final_verification_kind": row.get("final_verification_kind"),
        "proof_state": row.get("proof_state"),
        "core25_reason_code": row.get("core25_reason_code"),
        "coverage_executor": row.get("coverage_executor"),
        "coverage_executor_status": row.get("coverage_executor_status"),
        "requirement_type": row.get("requirement_type"),
        "requirement_scope": row.get("requirement_scope"),
        "source_row": row.get("source_row"),
        "expected_sections": list(row.get("expected_sections") or []),
        "expected_objects_count": len(row.get("expected_objects") or []),
        "expected_objects_with_responsibility_class": sum(
            bool(item.get("responsibility_class"))
            for item in (row.get("expected_objects") or []) if isinstance(item, dict)
        ),
        "expected_objects_with_reliability_coefficient": sum(
            item.get("reliability_coefficient") is not None
            for item in (row.get("expected_objects") or []) if isinstance(item, dict)
        ),
        "has_appendix_reference": (
            "приложен" in str(row.get("requirement_text") or "").replace("ё", "е").casefold()
            or "приложен" in str(row.get("source_row_title") or "").replace("ё", "е").casefold()
        ),
        "set_contract_kind": (
            "IDENTIFICATION_ATTRIBUTES"
            if "идентификацион" in str(row.get("source_row_title") or "").replace("ё", "е").casefold()
            else "OBJECT_COMPOSITION"
            if "состав объект" in (
                str(row.get("source_row_title") or "") + " " + str(row.get("requirement_text") or "")
            ).replace("ё", "е").casefold()
            else ""
        ),
        "core25_admission_stage": row.get("core25_admission_stage"),
        "core25_raw_candidate_count": int(row.get("core25_raw_candidate_count") or 0),
        "core25_verified_candidate_count": int(row.get("core25_verified_candidate_count") or 0),
        "core25_qualified_evidence_count": int(row.get("core25_qualified_evidence_count") or 0),
        "core25_binding_counts": dict(row.get("core25_binding_counts") or {}),
        "core25_binding_reason_codes": dict(row.get("core25_binding_reason_codes") or {}),
        "candidate_kind_counts": dict(Counter(
            str(item.get("evidence_kind") or "")
            for item in (row.get("directed_evidence_candidates") or [])
            if isinstance(item, dict)
        )),
        "max_matched_terms": max(
            [len(item.get("matched_terms") or []) for item in (row.get("directed_evidence_candidates") or []) if isinstance(item, dict)] or [0]
        ),
        "max_matched_normative_refs": max(
            [len(item.get("matched_normative_refs") or []) for item in (row.get("directed_evidence_candidates") or []) if isinstance(item, dict)] or [0]
        ),
        "capacity_required_levels": sorted({
            str(item.get("capacity_required_level") or "")
            for item in (row.get("directed_evidence_candidates") or [])
            if isinstance(item, dict) and item.get("capacity_required_level")
        }),
        "capacity_observed_levels": sorted({
            str(item.get("capacity_observed_level") or "")
            for item in (row.get("directed_evidence_candidates") or [])
            if isinstance(item, dict) and item.get("capacity_observed_level")
        }),
        "capacity_level_compatible": any(
            item.get("capacity_level_compatible") is True
            for item in (row.get("directed_evidence_candidates") or [])
            if isinstance(item, dict)
        ),
        "capacity_verified_difference": any(
            item.get("capacity_verified_difference") is True
            for item in (row.get("directed_evidence_candidates") or [])
            if isinstance(item, dict)
        ),
        "capacity_exact_match": any(
            item.get("capacity_exact_match") is True
            for item in (row.get("directed_evidence_candidates") or [])
            if isinstance(item, dict)
        ),
        "capacity_summary_value_count": max(
            [int(item.get("capacity_summary_value_count") or 0) for item in (row.get("directed_evidence_candidates") or []) if isinstance(item, dict)] or [0]
        ),
        "capacity_candidate_value_count": max(
            [int(item.get("capacity_candidate_value_count") or 0) for item in (row.get("directed_evidence_candidates") or []) if isinstance(item, dict)] or [0]
        ),
        "capacity_line_count_present": any(
            item.get("capacity_line_count_present") is True
            for item in (row.get("directed_evidence_candidates") or [])
            if isinstance(item, dict)
        ),
        "identification_expected_attribute_fingerprints": [
            {
                "position": item.get("position") or item.get("genplan_position"),
                "responsibility_class": item.get("responsibility_class"),
                "reliability_coefficient": item.get("reliability_coefficient"),
                "addressable": bool(item.get("identification_attributes_addressable")),
            }
            for item in (row.get("expected_objects") or [])
            if (
                isinstance(item, dict)
                and (
                    item.get("responsibility_class")
                    or item.get("reliability_coefficient") is not None
                )
            )
        ],
        "identification_mismatch_fingerprints": [
            {
                "position": item.get("position"),
                "mismatch_fields": list(item.get("mismatch_fields") or []),
                "required_responsibility_class": item.get("required_responsibility_class"),
                "observed_responsibility_class": item.get("observed_responsibility_class"),
                "required_reliability_coefficient": item.get("required_reliability_coefficient"),
                "observed_reliability_coefficient": item.get("observed_reliability_coefficient"),
            }
            for item in (row.get("directed_evidence_candidates") or [])
            if (
                isinstance(item, dict)
                and str(item.get("evidence_kind") or "").upper() == "IDENTIFICATION_ATTRIBUTE_COMPARISON"
                and item.get("verified_difference") is True
            )
        ],
    }


def _identification_frontier(rows: list[dict]) -> list[dict]:
    selected = [
        row for row in rows
        if (
            str(row.get("requirement_type") or "").upper() == "SET_COMPARISON"
            or int(row.get("expected_objects_count") or 0) > 0
            or row.get("has_appendix_reference") is True
        )
    ]
    return [
        {
            "requirement_id": row.get("requirement_id"),
            "requirement_type": row.get("requirement_type"),
            "requirement_scope": row.get("requirement_scope"),
            "source_row": row.get("source_row"),
            "expected_objects_count": int(row.get("expected_objects_count") or 0),
            "expected_objects_with_responsibility_class": int(row.get("expected_objects_with_responsibility_class") or 0),
            "expected_objects_with_reliability_coefficient": int(row.get("expected_objects_with_reliability_coefficient") or 0),
            "has_appendix_reference": bool(row.get("has_appendix_reference")),
            "set_contract_kind": row.get("set_contract_kind") or "",
            "final_verification_kind": row.get("final_verification_kind"),
            "proof_state": row.get("proof_state"),
            "proof_reason": row.get("core25_reason_code"),
            "coverage_executor": row.get("coverage_executor"),
            "identification_expected_attribute_fingerprints": row.get("identification_expected_attribute_fingerprints") or [],
            "identification_mismatch_fingerprints": row.get("identification_mismatch_fingerprints") or [],
        }
        for row in selected
    ]


def _safe_identification_layout_diagnostics(
    requirements: list[dict],
    assignment_corpus: list[dict],
) -> list[dict]:
    diagnostics: list[dict] = []
    generic = {"объект", "здание", "сооружение", "площадка", "комплекс", "система", "установка", "проектируемый", "проектируемая", "проектируемое", "поз"}
    for requirement in requirements or []:
        if not isinstance(requirement, dict):
            continue
        if str(requirement.get("requirement_type") or "").upper() != "SET_COMPARISON":
            continue
        title = str(requirement.get("source_row_title") or "").replace("ё", "е").casefold()
        if "идентификацион" not in title:
            continue
        for item in requirement.get("expected_objects") or []:
            if not isinstance(item, dict):
                continue
            position = str(item.get("position") or item.get("genplan_position") or "").strip()
            object_name = str(item.get("name") or item.get("object_name") or "").strip()
            source_page = item.get("page")
            if not position or not object_name:
                continue
            pages = [p for p in assignment_corpus if source_page in (None, "", 0) or p.get("page") == source_page] or list(assignment_corpus)
            position_hits = 0
            owner_page_match = False
            local_record_found = False
            for page in pages:
                raw = str(page.get("text") or "")
                position_hits += len(re.findall(rf"(?<![\\d.]){re.escape(position)}(?![\\d.])", raw.replace(",", ".")))
                normalized = " ".join(raw.replace("ё", "е").casefold().split())
                tokens = [tok for tok in re.findall(r"[a-zа-я0-9-]{4,}", object_name.replace("ё", "е").casefold()) if tok not in generic]
                if tokens:
                    hits = sum(tok in normalized for tok in tokens)
                    minimum = 1 if len(tokens) == 1 else 2
                    owner_page_match = owner_page_match or (hits >= minimum and hits / len(tokens) >= 0.60)
                if identity_context(raw, position=position, object_name=object_name):
                    local_record_found = True
                    break
            diagnostics.append({
                "position": position,
                "source_page": source_page,
                "exact_position_hits": position_hits,
                "owner_page_match": owner_page_match,
                "local_record_found": local_record_found,
                "enriched_responsibility_class": item.get("responsibility_class"),
                "enriched_reliability_coefficient": item.get("reliability_coefficient"),
            })
    return diagnostics

def _safe_identification_page_inventory(
    requirements: list[dict],
    assignment_corpus: list[dict],
) -> list[dict]:
    pages: dict[int, dict] = {}
    for requirement in requirements or []:
        if not isinstance(requirement, dict):
            continue
        if str(requirement.get("requirement_type") or "").upper() != "SET_COMPARISON":
            continue
        title = str(requirement.get("source_row_title") or "").replace("ё", "е").casefold()
        if "идентификацион" not in title:
            continue
        for item in requirement.get("expected_objects") or []:
            if not isinstance(item, dict):
                continue
            try:
                page_no = int(item.get("page"))
            except (TypeError, ValueError):
                continue
            row = pages.setdefault(page_no, {"page": page_no, "expected_positions": []})
            position = str(item.get("position") or item.get("genplan_position") or "").strip()
            if position:
                row["expected_positions"].append(position)

    corpus_by_page = {int(p.get("page")): str(p.get("text") or "") for p in assignment_corpus if p.get("page") is not None}
    result = []
    class_re = re.compile(r"(?<![A-Za-zА-Яа-яЁё0-9])к\s*с\s*[-–—]?\s*([1-3])(?=$|[^0-9])", re.I)
    gamma_re = re.compile(r"(?:γ|Γ|гамм[аы]?)(?:\s*[_\-]?\s*n)?\s*[=:]?\s*(0[.,]\d+|1(?:[.,]\d+)?)", re.I)
    gamma_word_re = re.compile(r"коэффициент\w*\s+(?:надежност|надёжност)\w*(?:\s+по\s+ответственност\w*)?.{0,80}?(0[.,]\d+|1(?:[.,]\d+)?)", re.I | re.S)
    for page_no, row in sorted(pages.items()):
        raw = corpus_by_page.get(page_no, "")
        classes = [f"КС-{m.group(1)}" for m in class_re.finditer(raw)]
        gamma_matches = list(gamma_re.finditer(raw)) or list(gamma_word_re.finditer(raw))
        gammas = []
        for match in gamma_matches:
            try:
                gammas.append(float(match.group(1).replace(",", ".")))
            except ValueError:
                pass
        result.append({
            "page": page_no,
            "expected_positions": row["expected_positions"],
            "expected_count": len(row["expected_positions"]),
            "responsibility_classes": classes,
            "responsibility_class_count": len(classes),
            "reliability_coefficients": gammas,
            "reliability_coefficient_count": len(gammas),
        })
    return result

def _safe_identification_project_inventory(
    requirements: list[dict],
    project_corpus: list[dict],
) -> list[dict]:
    expected: list[dict] = []
    for requirement in requirements or []:
        if not isinstance(requirement, dict):
            continue
        if str(requirement.get("requirement_type") or "").upper() != "SET_COMPARISON":
            continue
        title = str(requirement.get("source_row_title") or "").replace("ё", "е").casefold()
        if "идентификацион" not in title:
            continue
        expected.extend(dict(item) for item in requirement.get("expected_objects") or [] if isinstance(item, dict))
    if not expected:
        return []

    generic = {"объект", "здание", "сооружение", "площадка", "комплекс", "система", "установка", "проектируемый", "проектируемая", "проектируемое", "поз"}
    class_re = re.compile(r"(?<![A-Za-zА-Яа-яЁё0-9])к\s*с\s*[-–—]?\s*([1-3])(?=$|[^0-9])", re.I)
    gamma_re = re.compile(r"(?:γ|Γ|гамм[аы]?)(?:\s*[_\-]?\s*n)?\s*[=:]?\s*(0[.,]\d+|1(?:[.,]\d+)?)", re.I)
    gamma_word_re = re.compile(r"коэффициент\w*\s+(?:надежност|надёжност)\w*(?:\s+по\s+ответственност\w*)?.{0,80}?(0[.,]\d+|1(?:[.,]\d+)?)", re.I | re.S)
    result: list[dict] = []
    for page in project_corpus or []:
        raw = str(page.get("text") or "")
        normalized = " ".join(raw.replace("ё", "е").casefold().split())
        matched: list[tuple[int, str]] = []
        for item in expected:
            position = str(item.get("position") or item.get("genplan_position") or "").strip()
            name = str(item.get("name") or item.get("object_name") or "").strip()
            if not position or not name:
                continue
            pattern = re.compile(rf"(?<![\d.]){re.escape(position)}(?![\d.])")
            occurrences = list(pattern.finditer(raw.replace(",", ".")))
            if len(occurrences) != 1:
                continue
            tokens = [tok for tok in re.findall(r"[a-zа-я0-9-]{4,}", name.replace("ё", "е").casefold()) if tok not in generic]
            if not tokens:
                continue
            hits = sum(tok in normalized for tok in tokens)
            minimum = 1 if len(tokens) == 1 else 2
            if hits < minimum or hits / len(tokens) < 0.60:
                continue
            matched.append((occurrences[0].start(), position))
        if not matched:
            continue
        classes = [f"КС-{m.group(1)}" for m in class_re.finditer(raw)]
        gamma_matches = list(gamma_re.finditer(raw)) or list(gamma_word_re.finditer(raw))
        gammas = []
        for match in gamma_matches:
            try:
                gammas.append(float(match.group(1).replace(",", ".")))
            except ValueError:
                pass
        if not classes and not gammas:
            continue
        matched.sort()
        matched_positions = [position for _, position in matched]
        owner_order: list[tuple[int, str]] = []
        exact_owner_sequence_complete = True
        for position in matched_positions:
            item = next(
                (
                    row for row in expected
                    if str(row.get("position") or row.get("genplan_position") or "").strip() == position
                ),
                None,
            )
            name = str((item or {}).get("name") or (item or {}).get("object_name") or "").strip()
            normalized_name = " ".join(name.replace("ё", "е").casefold().split())
            occurrences = [
                match.start()
                for match in re.finditer(re.escape(normalized_name), normalized)
            ] if normalized_name else []
            if len(occurrences) != 1:
                exact_owner_sequence_complete = False
                break
            owner_order.append((occurrences[0], position))
        owner_order.sort()
        owner_order_consistent = bool(
            exact_owner_sequence_complete
            and [position for _, position in owner_order] == matched_positions
        )
        normalized_low = raw.replace("ё", "е").casefold()
        result.append({
            "document_type": page.get("document_type"),
            "page": page.get("page"),
            "has_identification_heading": "идентификацион" in normalized_low,
            "has_responsibility_heading": "ответственност" in normalized_low,
            "has_reliability_heading": ("надежност" in normalized_low or "надёжност" in raw.casefold()),
            "has_class_heading": ("класс сооружен" in normalized_low or "класс ответствен" in normalized_low),
            "matched_positions": matched_positions,
            "matched_position_count": len(matched),
            "exact_owner_sequence_complete": exact_owner_sequence_complete,
            "owner_order_consistent": owner_order_consistent,
            "responsibility_classes": classes,
            "responsibility_class_count": len(classes),
            "reliability_coefficients": gammas,
            "reliability_coefficient_count": len(gammas),
        })
    return result

def _safe_negative_frontier(rows: list[dict], corpus: list[dict]) -> list[dict]:
    """Structure-only diagnostics for negative/applicability REVIEW rows."""
    from core.assignment_verification_kernel import (
        NEGATIVE_MARKERS,
        _norm,
        _significant_terms,
    )
    from core.page_evidence_store import section_matches

    generic = {
        "разработк", "требовани", "отсутству", "необходимо",
        "предусмат", "применяет", "требуется",
    }
    result = []
    for row in rows:
        if row.get("final_verification_kind") != "REVIEW_QUESTION":
            continue
        if str(row.get("requirement_type") or "").upper() != "PROHIBITION_OR_NOT_REQUIRED":
            continue

        title_terms = _significant_terms(str(row.get("source_row_title") or ""))
        body_terms = _significant_terms(str(row.get("requirement_text") or ""))
        terms = []
        for term in [*title_terms, *body_terms]:
            if any(term.startswith(x) for x in generic):
                continue
            if term not in terms:
                terms.append(term)

        contract = dict(row.get("evidence_contract_v2") or {})
        expected_sections = list(contract.get("expected_sections") or [])
        critical = [str(x) for x in contract.get("critical_qualifiers") or []]

        windows = []
        for page in corpus:
            if is_assignment_source(page):
                continue
            raw = str(page.get("text") or "")
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in raw.splitlines()
                if line.strip()
            ]
            clauses = []
            buffer = ""
            for line in lines:
                buffer = f"{buffer} {line}".strip() if buffer else line
                if re.search(r"[.!?;:]\s*$", line):
                    clauses.append(buffer)
                    buffer = ""
            if buffer:
                clauses.append(buffer)

            for clause in clauses:
                low = _norm(clause)
                if not any(marker in low for marker in NEGATIVE_MARKERS):
                    continue
                hits = [term for term in terms if term in low]
                title_hits = [term for term in title_terms if term in low]
                body_hits = [term for term in body_terms if term in low]
                qualifier_ok = all(_norm(item) in low for item in critical)
                windows.append({
                    "document_type": page.get("document_type"),
                    "hit_count": len(hits),
                    "coverage": round(len(set(hits)) / max(1, len(terms)), 3),
                    "title_coverage": round(len(set(title_hits)) / max(1, len(title_terms)), 3),
                    "body_coverage": round(len(set(body_hits)) / max(1, len(body_terms)), 3),
                    "qualifier_ok": qualifier_ok,
                    "expected_section_match": (
                        section_matches(page.get("document_type") or page.get("document"), expected_sections)
                        if expected_sections else False
                    ),
                })

        ranked = sorted(
            windows,
            key=lambda x: (
                x["hit_count"],
                x["qualifier_ok"],
                x["expected_section_match"],
                x["body_coverage"],
            ),
            reverse=True,
        )
        best = ranked[0] if ranked else {}
        result.append({
            "requirement_id": row.get("requirement_id"),
            "requirement_scope": row.get("requirement_scope"),
            "query_term_count": len(terms),
            "source_title_term_count": len(title_terms),
            "body_term_count": len(body_terms),
            "critical_qualifier_count": len(critical),
            "contract_expected_section_count": len(expected_sections),
            "negative_window_count": len(windows),
            "max_subject_hit_count": int(best.get("hit_count") or 0),
            "max_subject_coverage": float(best.get("coverage") or 0),
            "best_title_coverage": float(best.get("title_coverage") or 0),
            "best_body_coverage": float(best.get("body_coverage") or 0),
            "best_critical_qualifiers_satisfied": best.get("qualifier_ok") is True,
            "best_expected_section_match": best.get("expected_section_match") is True,
            "best_document_type": best.get("document_type"),
        })
    return result


def _safe_composite_frontier(rows: list[dict], corpus: list[dict]) -> list[dict]:
    """Structure-only condition matrices for deterministic composite REVIEW rows."""
    from core.assignment_verification_kernel import verify_assignment_requirement

    allowed = {
        "LIGHTING_COMPOSITE_EXECUTOR",
        "FENCING_COMPOSITE_EXECUTOR",
        "LIGHTNING_GROUNDING_COMPOSITE_EXECUTOR",
    }
    result = []
    for row in rows:
        if row.get("final_verification_kind") != "REVIEW_QUESTION":
            continue
        executor = str(row.get("coverage_executor") or "")
        if executor not in allowed:
            continue
        checked = verify_assignment_requirement(row, corpus)
        if not isinstance(checked, dict):
            continue
        matrix = [
            {
                "condition_id": str(item.get("condition_id") or ""),
                "proven": item.get("proven") is True,
            }
            for item in (checked.get("condition_matrix") or [])
            if isinstance(item, dict)
        ]
        summary = dict(checked.get("condition_summary") or {})
        result.append({
            "requirement_id": row.get("requirement_id"),
            "verification_kernel": checked.get("verification_kernel"),
            "status": checked.get("status"),
            "proven_count": int(summary.get("proven") or 0),
            "total_count": int(summary.get("total") or len(matrix) or 0),
            "condition_matrix": matrix,
        })
    return result


def _safe_trace_frontier(rows: list[dict], corpus: list[dict]) -> list[dict]:
    """Structure-only diagnostics for CROSS_DOCUMENT_TRACE review rows.

    This intentionally emits no requirement text, project text, filenames or
    page numbers.  It only reports whether the benchmark corpus contains both
    sides of a potential trace chain and whether they share the requirement
    vocabulary strongly enough to justify implementing a Core25 proof route.
    """
    from core.assignment_verification_kernel import _norm, _query_text, _significant_terms
    from core.page_evidence_store import is_assignment_source

    survey_markers = (
        "изыскан",
        "игди",
        "иги",
        "игми",
        "иэи",
        "инженерно-геодез",
        "инженерно-геолог",
        "инженерно-гидрометеор",
        "инженерно-эколог",
        "техническ отчет",
        "технический отчет",
    )
    project_markers = ("пз", "пзу", "кр", "ар", "тх", "иос")

    project_corpus = [p for p in corpus if not is_assignment_source(p)]
    result = []
    for row in rows:
        if row.get("final_verification_kind") != "REVIEW_QUESTION":
            continue
        if str(row.get("requirement_type") or "").upper() != "CROSS_DOCUMENT_TRACE":
            continue

        terms = _significant_terms(_query_text(row))
        page_diags = []
        for page in project_corpus:
            low = _norm(page.get("text") or "")
            doc_type = _norm(page.get("document_type") or "")
            document = _norm(page.get("document") or "")
            hits = [term for term in terms if term in low]
            if len(hits) < 2:
                continue
            source_like = any(marker in doc_type or marker in document for marker in survey_markers)
            design_like = (
                not source_like
                and any(marker == doc_type or doc_type.startswith(marker) for marker in project_markers)
            )
            page_diags.append({
                "document_type": page.get("document_type"),
                "term_hit_count": len(hits),
                "term_coverage": round(len(set(hits)) / max(1, len(terms)), 3),
                "source_survey_like": source_like,
                "project_design_like": design_like,
            })

        source_pages = [x for x in page_diags if x["source_survey_like"]]
        design_pages = [x for x in page_diags if x["project_design_like"]]
        result.append({
            "requirement_id": row.get("requirement_id"),
            "requirement_scope": row.get("requirement_scope"),
            "expected_section_count": len(row.get("expected_sections") or []),
            "query_term_count": len(terms),
            "coverage_executor": row.get("coverage_executor"),
            "admission_stage": row.get("core25_admission_stage"),
            "candidate_kind_counts": dict(Counter(
                str(item.get("evidence_kind") or "")
                for item in (row.get("directed_evidence_candidates") or [])
                if isinstance(item, dict)
            )),
            "source_survey_page_count": len(source_pages),
            "project_design_page_count": len(design_pages),
            "max_source_term_coverage": max([x["term_coverage"] for x in source_pages] or [0]),
            "max_design_term_coverage": max([x["term_coverage"] for x in design_pages] or [0]),
            "source_document_types": sorted({
                str(x.get("document_type") or "") for x in source_pages if x.get("document_type")
            }),
            "design_document_types": sorted({
                str(x.get("document_type") or "") for x in design_pages if x.get("document_type")
            }),
            "two_sided_trace_candidate": bool(source_pages and design_pages),
        })
    return result


def _safe_presence_frontier(rows: list[dict]) -> list[dict]:
    """Structure-only diagnostics for presence REVIEW rows.

    The output intentionally excludes requirement/project text and page/document
    names. It exposes only proof predicates needed to distinguish a missing
    section route from weak semantic evidence.
    """
    from core.assignment_verification_kernel import (
        DESIGN_MARKERS,
        _norm,
        _query_text,
        _significant_terms,
    )

    action_markers = (
        "предусмотреть",
        "выполнить",
        "разработать",
        "принять",
        "обеспечить",
        "установить",
        "предусматривается",
    )

    result = []
    for row in rows:
        if row.get("final_verification_kind") != "REVIEW_QUESTION":
            continue
        if str(row.get("requirement_type") or "").upper() != "PRESENCE_REQUIREMENT":
            continue

        contract = dict(row.get("evidence_contract_v2") or {})
        requirement_text = str(row.get("requirement_text") or "")
        query_terms = _significant_terms(_query_text(row))
        low_requirement = _norm(requirement_text)
        candidates = []
        for item in row.get("directed_evidence_candidates") or []:
            if not isinstance(item, dict):
                continue
            fragment = str(
                item.get("context")
                or item.get("exact_clause")
                or item.get("source_trace")
                or ""
            )
            low = _norm(fragment)
            matched_terms = list(item.get("matched_terms") or [])
            candidates.append({
                "evidence_kind": item.get("evidence_kind"),
                "evidence_state": item.get("evidence_state"),
                "document_type": item.get("document_type"),
                "matched_term_count": len(matched_terms),
                "query_term_count": len(query_terms),
                "full_term_coverage": round(len(set(matched_terms)) / max(1, len(query_terms)), 3),
                "semantic_coverage": item.get("semantic_coverage"),
                "critical_qualifiers_satisfied": item.get("critical_qualifiers_satisfied") is True,
                "owner_match": item.get("owner_match") is True,
                "has_design_marker": any(marker in low for marker in DESIGN_MARKERS),
                "has_parameter_value": item.get("value") is not None,
                "parameter_code": item.get("parameter_code") or "",
            })

        result.append({
            "requirement_id": row.get("requirement_id"),
            "requirement_scope": row.get("requirement_scope"),
            "expected_section_count": len(row.get("expected_sections") or []),
            "contract_expected_section_count": len(contract.get("expected_sections") or []),
            "critical_qualifier_count": len(contract.get("critical_qualifiers") or []),
            "query_term_count": len(query_terms),
            "requirement_action_marker": any(marker in low_requirement for marker in action_markers),
            "has_object_id": bool(row.get("object_id") or row.get("target_object_id")),
            "has_numeric_requirement_value": row.get("required_value") is not None,
            "coverage_executor": row.get("coverage_executor"),
            "admission_stage": row.get("core25_admission_stage"),
            "candidate_diagnostics": candidates,
        })
    return result


def _safe_normative_frontier(rows: list[dict]) -> list[dict]:
    """Emit structure-only diagnostics for normative REVIEW rows.

    No requirement text, project fragment, document name, or page number is
    emitted.  The diagnostic only exposes boolean/counted proof predicates so
    a routing/admission defect can be distinguished from missing evidence.
    """
    from core.assignment_verification_kernel import (
        DESIGN_MARKERS,
        _norm,
        _normative_ids,
        _significant_terms,
    )

    action_markers = (
        "предусмотреть",
        "выполнить",
        "разработать",
        "должны соответствовать",
        "проектные решения",
    )
    adoption_markers = (
        "руководствоваться",
        "в соответствии",
        "в строгом соответствии",
        "выполня",
        "производств",
        "предусмотр",
    )

    result = []
    for row in rows:
        if row.get("final_verification_kind") != "REVIEW_QUESTION":
            continue
        if str(row.get("requirement_type") or "").upper() != "NORMATIVE_COMPLIANCE":
            continue

        text = str(row.get("requirement_text") or "")
        low_req = _norm(text)
        required_refs = _normative_ids(text)
        subject = re.split(r"\b(?:в соответствии с|согласно)\b", text, maxsplit=1, flags=re.I)[0]
        subject_terms = [term for term in _significant_terms(subject) if term != "соответст"]

        candidate_diags = []
        for item in row.get("directed_evidence_candidates") or []:
            if not isinstance(item, dict):
                continue
            fragment = str(
                item.get("context")
                or item.get("exact_clause")
                or item.get("source_trace")
                or ""
            )
            low = _norm(fragment)
            refs_on_page = [ref for ref in required_refs if ref in low]
            subject_hits = [term for term in subject_terms if term in low]
            candidate_diags.append({
                "evidence_kind": item.get("evidence_kind"),
                "evidence_state": item.get("evidence_state"),
                "document_type": item.get("document_type"),
                "required_ref_count_on_page": len(refs_on_page),
                "all_required_refs_on_page": bool(required_refs) and len(refs_on_page) == len(required_refs),
                "subject_term_count": len(subject_terms),
                "subject_hit_count": len(subject_hits),
                "subject_minimum_met": bool(subject_terms) and len(subject_hits) >= min(2, len(subject_terms)),
                "has_design_marker": any(marker in low for marker in DESIGN_MARKERS),
                "has_adoption_marker": any(marker in low for marker in adoption_markers),
                "owner_match": item.get("owner_match") is True,
                "matched_term_count": len(item.get("matched_terms") or []),
                "matched_normative_ref_count": len(item.get("matched_normative_refs") or []),
            })

        result.append({
            "requirement_id": row.get("requirement_id"),
            "requirement_scope": row.get("requirement_scope"),
            "expected_section_count": len(row.get("expected_sections") or []),
            "required_normative_ref_count": len(required_refs),
            "requirement_action_marker": any(marker in low_req for marker in action_markers),
            "subject_term_count": len(subject_terms),
            "coverage_executor": row.get("coverage_executor"),
            "admission_stage": row.get("core25_admission_stage"),
            "candidate_diagnostics": candidate_diags,
        })
    return result


def _review_frontier(rows: list[dict], limit: int = 60) -> list[dict]:
    review = [row for row in rows if row.get("final_verification_kind") == "REVIEW_QUESTION"]
    review.sort(
        key=lambda row: (
            int(row.get("core25_verified_candidate_count") or 0),
            int(row.get("core25_qualified_evidence_count") or 0),
            int(row.get("core25_raw_candidate_count") or 0),
            bool(row.get("coverage_executor")),
        ),
        reverse=True,
    )
    return [
        {
            "requirement_id": row.get("requirement_id"),
            "requirement_type": row.get("requirement_type"),
            "requirement_scope": row.get("requirement_scope"),
            "expected_sections": row.get("expected_sections") or [],
            "admission_stage": row.get("core25_admission_stage"),
            "raw_candidates": int(row.get("core25_raw_candidate_count") or 0),
            "verified_candidates": int(row.get("core25_verified_candidate_count") or 0),
            "qualified_evidence": int(row.get("core25_qualified_evidence_count") or 0),
            "coverage_executor": row.get("coverage_executor"),
            "coverage_executor_status": row.get("coverage_executor_status"),
            "proof_reason": row.get("core25_reason_code"),
            "binding_counts": row.get("core25_binding_counts") or {},
            "binding_reason_codes": row.get("core25_binding_reason_codes") or {},
            "candidate_kind_counts": row.get("candidate_kind_counts") or {},
            "max_matched_terms": int(row.get("max_matched_terms") or 0),
            "max_matched_normative_refs": int(row.get("max_matched_normative_refs") or 0),
            "capacity_required_levels": row.get("capacity_required_levels") or [],
            "capacity_observed_levels": row.get("capacity_observed_levels") or [],
            "capacity_level_compatible": bool(row.get("capacity_level_compatible")),
            "capacity_verified_difference": bool(row.get("capacity_verified_difference")),
            "capacity_exact_match": bool(row.get("capacity_exact_match")),
            "capacity_summary_value_count": int(row.get("capacity_summary_value_count") or 0),
            "capacity_candidate_value_count": int(row.get("capacity_candidate_value_count") or 0),
            "capacity_line_count_present": bool(row.get("capacity_line_count_present")),
        }
        for row in review[:limit]
    ]


def _private_review_frontier(rows: list[dict], limit: int = 8) -> list[dict]:
    review = [row for row in rows if row.get("final_verification_kind") == "REVIEW_QUESTION"]
    review.sort(
        key=lambda row: (
            int(row.get("core25_verified_candidate_count") or 0),
            int(row.get("core25_qualified_evidence_count") or 0),
            int(row.get("core25_raw_candidate_count") or 0),
            bool(row.get("coverage_executor")),
        ),
        reverse=True,
    )
    result = []
    for row in review[:limit]:
        candidates = []
        for item in row.get("directed_evidence_candidates") or []:
            if not isinstance(item, dict):
                continue
            candidates.append({
                "evidence_state": item.get("evidence_state"),
                "evidence_kind": item.get("evidence_kind"),
                "document": item.get("document"),
                "document_type": item.get("document_type"),
                "page": item.get("page"),
                "context": item.get("context") or item.get("exact_clause") or item.get("source_trace"),
                "score": item.get("score"),
                "object": item.get("object"),
                "owner_match": item.get("owner_match"),
                "parameter_code": item.get("parameter_code"),
                "value": item.get("value"),
                "unit": item.get("unit"),
                "matched_terms": item.get("matched_terms") or [],
                "matched_normative_refs": item.get("matched_normative_refs") or [],
                "condition_id": item.get("condition_id"),
                "condition_label": item.get("condition_label"),
            })
        result.append({
            "requirement_id": row.get("requirement_id"),
            "requirement_text": row.get("requirement_text"),
            "source_row_title": row.get("source_row_title"),
            "requirement_type": row.get("requirement_type"),
            "requirement_scope": row.get("requirement_scope"),
            "expected_sections": row.get("expected_sections") or [],
            "evidence_contract_v2": row.get("evidence_contract_v2") or {},
            "coverage_executor": row.get("coverage_executor"),
            "coverage_executor_status": row.get("coverage_executor_status"),
            "core25_reason_code": row.get("core25_reason_code"),
            "core25_admission_stage": row.get("core25_admission_stage"),
            "core25_binding_counts": row.get("core25_binding_counts") or {},
            "core25_binding_reason_codes": row.get("core25_binding_reason_codes") or {},
            "candidates": candidates,
        })
    return result



def _apply_baseline_manifest(fixture: dict, manifest: dict | None) -> tuple[list[dict], dict]:
    rows = [dict(row) for row in (fixture.get("baseline_rows") or [])]
    meta = {
        "baseline_label": fixture.get("baseline_label"),
        "baseline_source_sha": fixture.get("baseline_source_sha"),
        "proven_deviations": int(fixture.get("proven_deviations") or 0),
    }
    if not manifest:
        return rows, meta

    by_id = {str(row.get("requirement_id") or ""): row for row in rows}
    for override in manifest.get("row_overrides") or []:
        requirement_id = str(override.get("requirement_id") or "")
        if not requirement_id or requirement_id not in by_id:
            raise ValueError(f"Unknown Test78 baseline override requirement: {requirement_id or '<empty>'}")
        allowed = {
            "final_verification_kind", "proof_state", "core25_reason_code", "coverage_executor"
        }
        for key, value in override.items():
            if key in allowed:
                by_id[requirement_id][key] = value

    if manifest.get("baseline_label"):
        meta["baseline_label"] = manifest["baseline_label"]
    if manifest.get("baseline_source_sha"):
        meta["baseline_source_sha"] = manifest["baseline_source_sha"]
    if manifest.get("proven_deviations") is not None:
        meta["proven_deviations"] = int(manifest["proven_deviations"])
    return rows, meta

def _counts(rows: list[dict], proven_deviations: int) -> dict:
    kinds = Counter(row.get("final_verification_kind") for row in rows)
    verified = int(kinds.get("VERIFIED_OK", 0))
    project_findings = int(kinds.get("PROJECT_FINDING", 0))
    review = int(kinds.get("REVIEW_QUESTION", 0))
    external_deviations = int(proven_deviations)
    return {
        "requirements": len(rows),
        "VERIFIED_OK": verified,
        "PROJECT_FINDING": project_findings,
        "REVIEW_QUESTION": review,
        "external_proven_deviations": external_deviations,
        "proven_deviations": project_findings + external_deviations,
        "strict_categorical_if_deviations_unchanged": (
            verified + project_findings + external_deviations
        ),
    }


def run(fixture: dict, baseline_manifest: dict | None = None) -> dict:
    requirements = copy.deepcopy(list(fixture.get("requirements") or []))
    corpus = list(fixture.get("page_corpus") or [])
    assignment_corpus = [page for page in corpus if is_assignment_source(page)]
    project_corpus = [page for page in corpus if not is_assignment_source(page)]
    identification_enrichment = enrich_identification_requirements(requirements, assignment_corpus)

    attach_directed_evidence(requirements, project_corpus)
    coverage = attach_coverage_executor_evidence(requirements, project_corpus)
    runtime = run_assignment_runtime(requirements, object_registry=[])
    runtime_rows = list(runtime.get("rows") or [])
    current_rows = [_row_summary(row) for row in runtime_rows]

    baseline_rows, baseline_meta = _apply_baseline_manifest(fixture, baseline_manifest)
    before = {row["requirement_id"]: row for row in baseline_rows}
    after = {row["requirement_id"]: row for row in current_rows}
    before_ids = set(before)
    after_ids = set(after)

    missing_ids = sorted(before_ids - after_ids)
    added_ids = sorted(after_ids - before_ids)
    changed = []
    for requirement_id in sorted(before_ids & after_ids):
        b = before[requirement_id]
        a = after[requirement_id]
        if b.get("final_verification_kind") == a.get("final_verification_kind"):
            continue
        changed.append({
            "requirement_id": requirement_id,
            "before_kind": b.get("final_verification_kind"),
            "after_kind": a.get("final_verification_kind"),
            "before_proof": b.get("proof_state"),
            "after_proof": a.get("proof_state"),
            "before_reason": b.get("core25_reason_code"),
            "after_reason": a.get("core25_reason_code"),
            "before_executor": b.get("coverage_executor"),
            "after_executor": a.get("coverage_executor"),
        })

    gains = [
        row for row in changed
        if row["before_kind"] != "VERIFIED_OK" and row["after_kind"] == "VERIFIED_OK"
    ]
    regressions = [
        row for row in changed
        if row["before_kind"] == "VERIFIED_OK" and row["after_kind"] != "VERIFIED_OK"
    ]
    other_changes = [row for row in changed if row not in gains and row not in regressions]

    if missing_ids or added_ids:
        classification = "REQUIREMENT_SET_CHANGED"
    elif regressions:
        classification = "REGRESSION"
    elif len(changed) == 0:
        classification = "NO_CHANGE"
    elif len(gains) == 1 and len(changed) == 1:
        classification = "SINGLE_GAIN"
    elif len(changed) > 1:
        classification = "MULTI_CHANGE_AUDIT_REQUIRED"
    else:
        classification = "CHANGE_AUDIT_REQUIRED"

    proven_deviations = int(baseline_meta["proven_deviations"])
    return {
        "schema_version": 1,
        "benchmark": fixture.get("benchmark") or "Test78",
        "baseline_label": baseline_meta.get("baseline_label"),
        "baseline_source_sha": baseline_meta.get("baseline_source_sha"),
        "classification": classification,
        "baseline": _counts(baseline_rows, proven_deviations),
        "current": _counts(current_rows, proven_deviations),
        "requirement_set": {"missing_ids": missing_ids, "added_ids": added_ids},
        "changed_requirements": changed,
        "gains": gains,
        "regressions": regressions,
        "other_changes": other_changes,
        "review_frontier": _review_frontier(current_rows),
        "negative_frontier_diagnostics": _safe_negative_frontier(runtime_rows, corpus),
        "composite_frontier_diagnostics": _safe_composite_frontier(runtime_rows, corpus),
        "trace_frontier_diagnostics": _safe_trace_frontier(runtime_rows, corpus),
        "presence_frontier_diagnostics": _safe_presence_frontier(runtime_rows),
        "normative_frontier_diagnostics": _safe_normative_frontier(runtime_rows),
        "identification_frontier": _identification_frontier(current_rows),
        "identification_enrichment": identification_enrichment,
        "identification_layout_diagnostics": _safe_identification_layout_diagnostics(requirements, assignment_corpus),
        "identification_page_inventory": _safe_identification_page_inventory(requirements, assignment_corpus),
        "identification_project_inventory": _safe_identification_project_inventory(requirements, project_corpus),
        "_private_review_frontier": _private_review_frontier(runtime_rows),
        "archetype_coverage": {
            "baseline": _archetype_summary(baseline_rows),
            "current": _archetype_summary(current_rows),
        },
        "categorical_archetype_coverage": {
            "baseline": _categorical_archetype_summary(baseline_rows),
            "current": _categorical_archetype_summary(current_rows),
        },
        "coverage_summary": {
            "executor_hits": coverage.get("executor_hits"),
            "with_candidates": coverage.get("with_candidates"),
            "verified_candidates": coverage.get("verified_candidates"),
            "executors": coverage.get("executors") or {},
        },
    }


def markdown(result: dict) -> str:
    b = result["baseline"]
    c = result["current"]
    lines = [
        "# Test78 deterministic A/B",
        "",
        f"- Classification: **{result['classification']}**",
        f"- Baseline: **{b['VERIFIED_OK']} VERIFIED_OK / {b['REVIEW_QUESTION']} REVIEW**",
        f"- Current: **{c['VERIFIED_OK']} VERIFIED_OK / {c['REVIEW_QUESTION']} REVIEW**",
        f"- Strict categorical (if the separately audited deviations are unchanged): **{c['strict_categorical_if_deviations_unchanged']}/56**",
        f"- Changed requirements: **{len(result['changed_requirements'])}**",
        f"- Universal archetypes (current VERIFIED_OK): **{result['archetype_coverage']['current']['universal_archetypes']}**",
        f"- VERIFIED_OK not yet mapped to a universal archetype: **{result['archetype_coverage']['current']['verified_requirements_unclassified']}**",
        f"- Universal archetypes (all categorical results): **{result['categorical_archetype_coverage']['current']['universal_archetypes']}**",
        "",
    ]
    if result["changed_requirements"]:
        lines.extend(["## Changed requirement IDs", ""])
        for row in result["changed_requirements"]:
            lines.append(
                f"- `{row['requirement_id']}`: `{row['before_kind']}` → `{row['after_kind']}` "
                f"({row.get('after_reason') or '—'}; {row.get('after_executor') or '—'})"
            )
        lines.append("")
    if result["requirement_set"]["missing_ids"] or result["requirement_set"]["added_ids"]:
        lines.extend([
            "## Requirement-set drift",
            "",
            f"- Missing IDs: {', '.join(result['requirement_set']['missing_ids']) or 'none'}",
            f"- Added IDs: {', '.join(result['requirement_set']['added_ids']) or 'none'}",
            "",
        ])
    lines.extend([
        "> Fixed 56-requirement denominator; project page text is never emitted to logs or output artifacts.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out-dir", default="benchmark_out")
    parser.add_argument("--private-out", default="")
    parser.add_argument(
        "--baseline-manifest",
        default="knowledge/benchmarks/test78_baseline_overrides.json",
    )
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    baseline_path = Path(args.baseline_manifest) if args.baseline_manifest else None
    baseline_manifest = (
        json.loads(baseline_path.read_text(encoding="utf-8"))
        if baseline_path and baseline_path.exists()
        else None
    )
    result = run(fixture, baseline_manifest=baseline_manifest)
    private_frontier = result.pop("_private_review_frontier", [])
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "test78_ab.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "test78_ab.md").write_text(markdown(result), encoding="utf-8")
    if args.private_out:
        private_path = Path(args.private_out)
        private_path.parent.mkdir(parents=True, exist_ok=True)
        private_path.write_text(
            json.dumps({
                "schema_version": 1,
                "benchmark": result.get("benchmark"),
                "baseline_source_sha": result.get("baseline_source_sha"),
                "frontier": private_frontier,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(json.dumps({
        "classification": result["classification"],
        "baseline": result["baseline"],
        "current": result["current"],
        "changed_ids": [row["requirement_id"] for row in result["changed_requirements"]],
        "archetype_coverage": result["archetype_coverage"]["current"],
        "categorical_archetype_coverage": result["categorical_archetype_coverage"]["current"],
        "review_frontier": result["review_frontier"],
        "negative_frontier_diagnostics": result["negative_frontier_diagnostics"],
        "composite_frontier_diagnostics": result["composite_frontier_diagnostics"],
        "trace_frontier_diagnostics": result["trace_frontier_diagnostics"],
        "presence_frontier_diagnostics": result["presence_frontier_diagnostics"],
        "normative_frontier_diagnostics": result["normative_frontier_diagnostics"],
        "identification_frontier": result["identification_frontier"],
        "identification_enrichment": result["identification_enrichment"],
        "identification_layout_diagnostics": result["identification_layout_diagnostics"],
        "identification_page_inventory": result["identification_page_inventory"],
        "identification_project_inventory": result["identification_project_inventory"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
