from __future__ import annotations

from core.checklist_profiles import ChecklistProfileRegistry, normalize_profile_code


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
