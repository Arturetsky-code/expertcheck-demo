from __future__ import annotations

from core25.runtime_bridge import run_assignment_runtime


def _base(requirement_type: str, text: str, evidence: dict) -> dict:
    return {
        "requirement_id": "REQ-1",
        "requirement_text": text,
        "requirement_type": requirement_type,
        "requirement_scope": "DOCUMENT_SPECIFIC",
        "expected_sections": ["ПЗ"],
        "directed_evidence_candidates": [evidence],
    }


def test_negative_applicability_can_close_through_core25():
    req = _base(
        "PROHIBITION_OR_NOT_REQUIRED",
        "Разработка отдельного решения не требуется.",
        {
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_NEGATIVE_APPLICABILITY",
            "negative_assertion": True,
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 18,
            "context": "Для данного объекта разработка отдельного решения не требуется.",
            "score": 96,
        },
    )
    payload = run_assignment_runtime([req])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["proof_state"] == "PROVEN_MATCH"
    assert row["core25_reason_code"] == "NEGATIVE_APPLICABILITY_CONFIRMED"
    assert row["verification_evidence"][0]["page"] == 18


def test_factual_normative_assertion_can_close_but_reference_only_cannot():
    verified = _base(
        "NORMATIVE_COMPLIANCE",
        "Климатический район принять по СП 131.13330.2020.",
        {
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_NORMATIVE_ASSERTION",
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 21,
            "context": "По СП 131.13330.2020 площадка относится к климатическому району IВ.",
            "matched_normative_refs": ["сп 131.13330.2020"],
            "matched_terms": ["климатическ", "район"],
            "score": 95,
        },
    )
    payload = run_assignment_runtime([verified])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_reason_code"] == "FACTUAL_NORMATIVE_ASSERTION_CONFIRMED"

    weak = dict(verified)
    weak["requirement_id"] = "REQ-2"
    weak["directed_evidence_candidates"] = [{
        **verified["directed_evidence_candidates"][0],
        "evidence_kind": "NORMATIVE_REFERENCE_CANDIDATE",
        "matched_terms": [],
    }]
    payload = run_assignment_runtime([weak])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "REVIEW_QUESTION"
    assert row["proof_state"] == "INSUFFICIENT"


def test_site_presence_scope_is_not_forced_to_unbound():
    req = {
        "requirement_id": "REQ-FENCE",
        "requirement_text": "Предусмотреть металлическое ограждение части площадки ДСК.",
        "requirement_type": "PRESENCE_REQUIREMENT",
        "requirement_scope": "SITE_SPECIFIC",
        "expected_sections": ["ПЗУ"],
        "directed_evidence_candidates": [{
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_PROJECT_PASSAGE",
            "document": "Раздел ПД №2_ПЗУ.pdf",
            "document_type": "ПЗУ",
            "page": 27,
            "context": "Территория площадки ДСК ограждается металлическими панелями по столбам.",
            "score": 94,
        }],
    }
    payload = run_assignment_runtime([req])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_reason_code"] == "ASSIGNMENT_PRESENCE_CONFIRMED"


def test_unverified_candidate_never_becomes_core25_proof():
    req = _base(
        "PROHIBITION_OR_NOT_REQUIRED",
        "Разработка отдельного решения не требуется.",
        {
            "evidence_state": "candidate",
            "evidence_kind": "QUALIFIED_NEGATIVE_APPLICABILITY",
            "negative_assertion": True,
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 18,
            "context": "Разработка отдельного решения не требуется.",
            "score": 96,
        },
    )
    payload = run_assignment_runtime([req])
    row = payload["rows"][0]
    assert row["final_verification_kind"] == "REVIEW_QUESTION"
