from __future__ import annotations

from core25.contracts import DecisionState
from core25.runtime_bridge import run_assignment_runtime


def _value_requirement(*, object_name="", object_id="", scope="PROJECT_GLOBAL"):
    return {
        "requirement_id": "REQ-1",
        "requirement_text": "Продолжительность смены 12 часов" if not object_name else "Площадь здания проборазделки 89,9 м2",
        "requirement_type": "VALUE_COMPARISON",
        "requirement_scope": scope,
        "object_name": object_name,
        "object_id": object_id,
        "parameter_code": "SHIFT_DURATION" if not object_name else "AREA_TOTAL",
        "required_value": 12.0 if not object_name else 89.9,
        "unit": "час" if not object_name else "м2",
        "source_document": "Задание.pdf",
        "page": 3,
        "evidence_contract_v2": {
            "scope": scope,
            "expected_sections": ["ТХ"] if not object_name else ["АР"],
        },
        "directed_evidence_candidates": [],
    }


def test_runtime_bridge_promotes_verified_directed_value_through_core25():
    req = _value_requirement()
    req["directed_evidence_candidates"] = [{
        "evidence_state": "verified_candidate",
        "evidence_kind": "DIRECTED_VALUE",
        "document": "ТХ.pdf",
        "document_type": "ТХ",
        "page": 7,
        "parameter_code": "SHIFT_DURATION",
        "value": 12.0,
        "unit": "час",
        "context": "Режим работы. Продолжительность смены составляет 12 часов.",
        "owner_match": True,
        "unit_compatible": True,
    }]

    payload = run_assignment_runtime([req], object_registry=[])

    assert payload["engine"] == "core25"
    assert payload["summary"]["total"] == 1
    assert payload["summary"]["compliant"] == 1
    assert payload["results"][0].decision.state is DecisionState.COMPLIANT
    row = payload["rows"][0]
    assert row["status"] == "Соответствует заданию"
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["proof_id"]
    assert row["trace_id"]
    assert row["verification_evidence"][0]["document"] == "ТХ.pdf"
    assert row["verification_evidence"][0]["page"] == 7


def test_runtime_bridge_does_not_promote_candidate_without_proven_owner_match():
    req = _value_requirement(
        object_name="Здание проборазделки",
        object_id="OBJ-LAB",
        scope="OBJECT_SPECIFIC",
    )
    req["directed_evidence_candidates"] = [{
        "evidence_state": "verified_candidate",
        "evidence_kind": "DIRECTED_VALUE",
        "document": "АР.pdf",
        "document_type": "АР",
        "page": 12,
        "object": "Модуль обеспыливания",
        "parameter_code": "AREA_TOTAL",
        "value": 23.5,
        "unit": "м2",
        "context": "Модуль обеспыливания. Общая площадь составляет 23,5 м2.",
        "owner_match": False,
        "unit_compatible": True,
    }]

    payload = run_assignment_runtime([req], object_registry=[
        {"object_id": "OBJ-LAB", "name": "Здание проборазделки"},
        {"object_id": "OBJ-DUST", "name": "Модуль обеспыливания"},
    ])

    result = payload["results"][0]
    assert result.decision.state is DecisionState.REVIEW
    assert result.trace.proof.is_categorical is False
    assert payload["rows"][0]["status"] == "Требует проверки"


def test_runtime_bridge_routes_unsupported_requirement_to_review():
    req = {
        "requirement_id": "REQ-SEM",
        "requirement_text": "Обеспечить удобство эксплуатации",
        "requirement_type": "SEMANTIC_ENGINEERING",
        "requirement_scope": "UNRESOLVED",
        "source_document": "Задание.pdf",
        "page": 4,
    }

    payload = run_assignment_runtime([req], object_registry=[])

    assert payload["results"][0].decision.state is DecisionState.REVIEW
    assert payload["rows"][0]["final_verification_kind"] == "REVIEW_QUESTION"
