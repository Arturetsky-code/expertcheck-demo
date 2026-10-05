from __future__ import annotations

from core.checklist_profiles import ChecklistProfileRegistry, normalize_profile_code
from core.project_review_planner import build_review_plan


def test_profile_aliases_are_stage_safe():
    assert normalize_profile_code("ПД") == "PD"
    assert normalize_profile_code("РД") == "RD"
    assert normalize_profile_code("project_documentation") == "PD"
    assert normalize_profile_code("working_documentation") == "RD"


def test_pd_profile_loads_canonical_question_set():
    registry = ChecklistProfileRegistry("knowledge")
    rows = registry.load("PD")

    assert len(rows) == 571
    assert len({row["discipline"] for row in rows}) == 20
    assert rows[0]["checklist_profile"] == "PD"
    assert rows[0]["source_question_id"] == 1
    assert rows[-1]["source_question_id"] == 571
    assert all(row["priority"] in {1, 2, 3} for row in rows)


def test_rd_profile_loads_canonical_question_set():
    registry = ChecklistProfileRegistry("knowledge")
    rows = registry.load("РД")

    assert len(rows) == 296
    assert len({row["discipline"] for row in rows}) == 13
    assert rows[0]["checklist_profile"] == "RD"
    assert rows[0]["source_question_id"] == 1
    assert rows[-1]["source_question_id"] == 296
    assert all(row["priority"] in {1, 2, 3} for row in rows)


def test_same_numeric_question_id_is_unique_between_profiles():
    registry = ChecklistProfileRegistry("knowledge")
    pd_first = registry.load("PD")[0]
    rd_first = registry.load("RD")[0]

    assert pd_first["id"] == rd_first["id"] == 1
    assert pd_first["checklist_profile"] != rd_first["checklist_profile"]


def test_review_plan_preserves_profile_identity_priority_and_evidence_route():
    row = {
        "checklist_parent_id": "CHECK-PD-0001",
        "checklist_profile": "PD",
        "source_question_id": 1,
        "priority": 1,
        "question": "Определены границы проектирования",
        "criteria": "Решение должно быть подтверждено адресным проектным источником.",
        "expected_sections": ["ПЗ", "ТХ"],
        "verification_kind": "SYSTEM_LIMITATION",
        "final_verification_kind": "SYSTEM_LIMITATION",
    }

    plan = build_review_plan(checklist_results=[row])
    item = next(x for x in plan["items"] if x["domain_code"] == "checklist")

    assert item["plan_id"] == "CHECK-PD-0001"
    assert item["source_id"] == "CHECK-PD-0001"
    assert item["checklist_profile"] == "PD"
    assert item["checklist_priority"] == 1
    assert item["checklist_criteria"].startswith("Решение")
    assert item["expected_sections"] == ["ПЗ", "ТХ"]
