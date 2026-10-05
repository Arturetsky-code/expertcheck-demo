from __future__ import annotations

from core.atomic_verification_engine import (
    _checklist_expected_sections,
    _checklist_parent_identity,
    verify_checklist_rows,
)


def test_pd_rd_profile_identity_namespaces_same_question_number():
    pd_id, pd_profile = _checklist_parent_identity(
        {"id": 1, "checklist_profile": "ПД"}, 1
    )
    rd_id, rd_profile = _checklist_parent_identity(
        {"id": 1, "checklist_profile": "РД"}, 2
    )

    assert pd_id == "CHECK-PD-0001"
    assert rd_id == "CHECK-RD-0001"
    assert pd_profile == "PD"
    assert rd_profile == "RD"
    assert pd_id != rd_id


def test_legacy_checklist_identity_remains_sequence_based():
    parent_id, profile = _checklist_parent_identity({"id": "CL-0001"}, 7)

    assert parent_id == "CHECK-0007"
    assert profile == ""


def test_profile_expected_sections_keep_multiple_evidence_routes():
    row = {
        "id": 1,
        "checklist_profile": "PD",
        "expected_sections": ["ПЗУ", "ГП", "ПЗУ"],
    }

    assert _checklist_expected_sections(row) == ["ПЗУ", "ГП"]


def test_profile_metadata_reaches_atomic_checklist_evidence_contract():
    rows = [{
        "id": 1,
        "checklist_profile": "PD",
        "priority": 1,
        "question": "Проверить наличие значения производительности",
        "criteria": "Производительность должна быть подтверждена профильным проектным источником.",
        "expected_sections": ["ТХ", "ПЗ"],
        "compiled_rule": {
            "typed_check": "ENGINEERING_PARAMETER_PRESENCE",
            "verification_level": "L2_VALUE",
            "parameter_codes": ["CAPACITY"],
        },
        "typed_check": "ENGINEERING_PARAMETER_PRESENCE",
    }]

    result = verify_checklist_rows(
        rows,
        knowledge_root="knowledge",
        fact_graph={"facts": [], "passages": []},
        page_corpus=[],
    )

    assert rows[0]["checklist_parent_id"] == "CHECK-PD-0001"
    assert rows[0]["checklist_profile"] == "PD"
    assert result["atoms"]

    atom = result["atoms"][0]
    assert atom["checklist_parent_id"] == "CHECK-PD-0001"
    assert atom["checklist_profile"] == "PD"
    assert atom["checklist_priority"] == 1
    assert atom["checklist_criteria"].startswith("Производительность")
    assert atom["expected_sections"] == ["ТХ", "ПЗ"]
    assert atom["evidence_contract_v2"]["expected_sections"] == ["ТХ", "ПЗ"]
