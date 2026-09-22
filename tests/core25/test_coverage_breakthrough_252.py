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


def test_unresolved_negative_requirement_is_safe_project_global_and_closes():
    req = {
        "requirement_id": "REQ-NEG-UNRESOLVED",
        "requirement_text": "Разработка отдельного раздела не требуется.",
        "requirement_type": "PROHIBITION_OR_NOT_REQUIRED",
        "requirement_scope": "UNRESOLVED",
        "directed_evidence_candidates": [{
            "evidence_state": "verified_candidate",
            "evidence_kind": "QUALIFIED_NEGATIVE_APPLICABILITY",
            "negative_assertion": True,
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 18,
            "context": "Разработка отдельного раздела не требуется.",
            "score": 97,
        }],
    }
    row = run_assignment_runtime([req])["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_admission_stage"] == "PROVEN"
    assert row["core25_binding_counts"]["BOUND"] == 1


def test_exact_requirement_owner_wins_over_duplicate_registry_alias_ids():
    req = {
        "requirement_id": "REQ-DSK-CAPACITY",
        "requirement_text": "Установить ДСК суммарной производительностью 500 т/ч.",
        "requirement_type": "VALUE_COMPARISON",
        "requirement_scope": "OBJECT_SPECIFIC",
        "object_id": "REQ-DSK-ID",
        "object_name": "ДСК",
        "parameter_code": "CAPACITY",
        "required_value": 500,
        "unit": "т/ч",
        "expected_sections": ["ТХ"],
        "directed_evidence_candidates": [{
            "evidence_state": "verified_candidate",
            "evidence_kind": "DIRECTED_VALUE",
            "document": "Раздел ПД №6_ТХ1.pdf",
            "document_type": "ТХ",
            "page": 20,
            "context": "ДСК принят суммарной производительностью 500 т/ч.",
            "object": "ДСК",
            "owner_match": True,
            "parameter_code": "CAPACITY",
            "value": 500,
            "unit": "т/ч",
            "unit_compatible": True,
            "score": 100,
        }],
    }
    row = run_assignment_runtime(
        [req],
        object_registry=[{"object_id": "REG-DSK-ID", "name": "ДСК"}],
    )["rows"][0]
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["core25_reason_code"] == "TYPED_VALUE_MATCH"
    assert row["core25_binding_reason_codes"]["OWNER_PARAMETER_BOUND"] == 1


def test_admission_diagnostics_distinguish_unverified_candidate():
    req = _base(
        "PRESENCE_REQUIREMENT",
        "Предусмотреть систему видеонаблюдения.",
        {
            "evidence_state": "candidate",
            "evidence_kind": "SOURCE_LOCKED_PASSAGE",
            "document": "Раздел ПД №1_ПЗ.pdf",
            "document_type": "ПЗ",
            "page": 30,
            "context": "Система видеонаблюдения рассматривается в проекте.",
            "score": 70,
        },
    )
    row = run_assignment_runtime([req])["rows"][0]
    assert row["core25_admission_stage"] == "CANDIDATE_NOT_VERIFIED"
    assert row["core25_raw_candidate_count"] == 1
    assert row["core25_verified_candidate_count"] == 0
    assert row["core25_qualified_evidence_count"] == 0


def test_pdf_hyphenation_repair_restores_equipment_owner_and_mixed_positive_is_not_prohibition():
    from core.assignment_compliance import (
        TYPE_PRESENCE,
        _object_name,
        _repair_pdf_hyphenation,
        _requirement_type,
    )

    equipment = _repair_pdf_hyphenation(
        "Подача руды в приёмный бункер осуществляется двумя погруз- чиками SHANTUI L76-С5 с объёмом ковша 4,5 м3"
    )
    owner = _object_name(equipment, "")
    assert owner.startswith("Погрузчик")
    assert "SHANTUI" in owner.upper()

    mixed = (
        "Выполнить электроснабжение согласно ТУ. "
        "Прокладку кабельных линий в земле не предусматривать."
    )
    assert _requirement_type(mixed, "Электроснабжение", "", None) == TYPE_PRESENCE


def test_short_presence_requirement_can_be_verified_when_all_terms_match():
    from core.assignment_verification_kernel import verify_assignment_requirement

    requirement = {
        "requirement_id": "REQ-SHORT-PRESENCE",
        "requirement_text": "Предусмотреть металлическое ограждение территории",
        "requirement_type": "PRESENCE_REQUIREMENT",
        "source_row_title": "Ограждение территории",
        "evidence_contract_v2": {
            "scope": "SITE_SPECIFIC",
            "expected_sections": ["ПЗУ"],
            "critical_qualifiers": ["металлическ"],
        },
    }
    result = verify_assignment_requirement(
        requirement,
        [{
            "document": "Раздел ПД №2_ПЗУ.pdf",
            "document_type": "ПЗУ",
            "page": 12,
            "text": "Проектом предусмотрено металлическое ограждение территории площадки.",
        }],
    )
    assert result is not None
    assert result["status"] == "Соответствует заданию"
    assert result["verification_evidence"][0]["evidence_state"] == "verified_candidate"


def test_support_wall_requirement_is_not_misbound_to_loader_or_dsk():
    from core.assignment_compliance import _object_name
    from core.requirement_contracts import build_contract

    text = (
        "Для формирования площадки временного хранения и перегрузки взорванной руды "
        "фронтальными погрузчиками в приёмные бункера ДСК предусмотреть подпорную стену."
    )
    owner = _object_name(text, "")
    assert owner == "Подпорная стена"

    req = {
        "requirement_text": text,
        "requirement_type": "PRESENCE_REQUIREMENT",
        "object_name": owner,
        "parameter_code": "",
        "source_row_title": "Технологические решения",
    }
    contract = build_contract(req)
    assert contract["scope"] == "SITE_SPECIFIC"
    assert contract["expected_sections"] == ["ПЗУ"]


def test_modular_building_and_canopy_requirements_get_profile_sections():
    from core.requirement_contracts import infer_expected_sections

    assert infer_expected_sections(
        {"requirement_text": "Характеристики блочно-модульных зданий принять по документации завода изготовителя."}
    ) == ["АР", "ПЗ"]
    assert infer_expected_sections(
        {"requirement_text": "Навес системы подачи извести выполнить открытым."}
    ) == ["АР", "ПЗ"]
