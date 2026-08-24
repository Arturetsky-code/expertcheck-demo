from __future__ import annotations

from core.assignment_compliance import compare_requirements
from core.composition_registry import build_composition_baseline
from core.evidence_retrieval_cascade import retrieve_evidence
from core.project_evidence_database import build_project_evidence_database
from core.report_quality_gate import validate_review_plan
from core.requirement_contracts import build_contract
from studio.data import _compact_technical_frames


def _req(text: str, kind: str = "PRESENCE_REQUIREMENT", **extra):
    row = {
        "requirement_id": extra.pop("requirement_id", "ASSIGN-TEST"),
        "requirement_text": text,
        "requirement_type": kind,
        "object_name": extra.pop("object_name", ""),
        **extra,
    }
    row["evidence_contract_v2"] = build_contract(row)
    return row


def test_page_evidence_is_hard_filtered_by_expected_section():
    corpus = [
        {"document": "Раздел ПД №1_ПЗ.pdf", "document_type": "ПЗ", "page": 45, "text": "Расход воды 3 м3/ч."},
        {"document": "Раздел ПД №5_ИОС2.pdf", "document_type": "ИОС2", "page": 10, "text": "Расчётный расход воды и требуемый напор системы."},
    ]
    db = build_project_evidence_database(page_corpus=corpus)
    rows = retrieve_evidence({"title": "Расчётный расход и напор", "expected_sections": ["ИОС2"]}, db)
    assert rows
    assert {row["section"] for row in rows} == {"ИОС2"}
    assert all("№1_ПЗ" not in row["document"] for row in rows)


def test_composition_uses_authoritative_position_scope_and_deduplicates_shifted_name():
    pz = [
        {"parameter_code": "OBJECT_ENTRY", "pz_complex_object_register": True, "genplan_position": "4.1", "value_text": "Подпорная стена", "document": "ПЗ.pdf", "page": 40},
        {"parameter_code": "OBJECT_ENTRY", "pz_complex_object_register": True, "genplan_position": "4.18", "value_text": "Насосная станция", "document": "ПЗ.pdf", "page": 46},
    ]
    gp = [
        {"general_plan_explication": True, "genplan_position": "5", "value_text": "Соседняя площадка", "document": "ПЗУ2.pdf", "page": 4},
        {"general_plan_explication": True, "genplan_position": "9", "value_text": "EtherNet TX (медь) - EtherNet FX (оптика)", "document": "ТХ2.pdf", "page": 23},
        {"general_plan_explication": True, "genplan_position": "4.17", "value_text": "Насосная станция", "document": "ПЗУ2.pdf", "page": 5},
        {"general_plan_explication": True, "genplan_position": "4.19", "value_text": "КПП", "document": "ПЗУ2.pdf", "page": 5},
    ]
    rows, audit = build_composition_baseline(pz, gp)
    positions = {row["Позиция по ГП"] for row in rows}
    assert positions == {"4.1", "4.18", "4.19"}
    assert audit["scoped_out"] == 2
    assert audit["duplicate_position_conflicts"] == 1


def test_assignment_flood_protection_is_verified_from_profile_passage():
    requirement = _req("Предусмотреть мероприятия по защите проектируемой площадки от подтопления")
    corpus = [{
        "document": "Раздел ПД №2_ПЗУ1.pdf", "document_type": "ПЗУ", "page": 15,
        "text": "Для обеспечения защиты площадки от подтопления разработана система водоотведения. В состав входят нагорный канал и водопропускные трубы.",
    }]
    row = compare_requirements([requirement], [], [], corpus)[0]
    assert row["status"] == "Соответствует заданию"
    assert row["evidence_quality_state"] == "VERIFIED_ENGINEERING_EVIDENCE"
    assert row["verification_kernel"] == "FLOOD_PROTECTION"
    assert "ПЗУ1.pdf" in row["evidence"][0]


def test_assignment_document_cannot_be_used_as_project_evidence():
    requirement = _req("Предусмотреть открытый навес системы подачи извести")
    corpus = [{
        "document": "Задание на проектирование.pdf", "document_type": "НЕОПРЕДЕЛЕН", "page": 4,
        "text": "Проектом предусмотреть открытый навес системы подачи извести.",
    }]
    row = compare_requirements([requirement], [], [], corpus)[0]
    assert row["status"] != "Соответствует заданию"
    assert not row.get("verification_evidence")
    db = build_project_evidence_database(facts=[{
        "document": "Задание на проектирование.pdf", "parameter_code": "OBJECT_ENTRY",
        "value": "Навес", "fact_admission_decision": "ADMIT",
    }])
    assert db["record_count"] == 0


def test_assignment_equipment_checker_confirms_register_mismatch():
    requirement = _req(
        "Подача руды осуществляется двумя погрузчиками SHANTUI L76-C5 с объёмом ковша 4,5 м3",
        "VALUE_COMPARISON", object_name="Погрузчик SHANTUI L76-C5", parameter_code="BUCKET_VOLUME", required_value=4.5, unit="м3",
    )
    corpus = [{
        "document": "Раздел ПД №6_ТХ1.pdf", "document_type": "ТХ", "page": 37,
        "text": "Проектом предусматривается фронтальный погрузчик ARKTOS L76-C5 – 4 шт.",
    }]
    row = compare_requirements([requirement], [], [], corpus)[0]
    assert row["status"] == "Выявлено отклонение"
    assert row["verification_kernel"] == "EQUIPMENT_IDENTITY_AND_QUANTITY"
    assert "количество" in row["decision_basis"]


def test_assignment_capacity_checker_compares_project_level_hourly_capacity():
    requirement = _req(
        "Установить ДСК суммарной производительностью 500 т/ч с двумя независимыми технологическими линиями",
        "VALUE_COMPARISON", object_name="ДСК", parameter_code="CAPACITY", required_value=500, unit="т/ч",
    )
    corpus = [{
        "document": "Раздел ПД №6_ТХ1.pdf", "document_type": "ТХ", "page": 34,
        "text": "Таблица 5.1.1 - Параметры и технологические режимы. Часовая производительность отделения, тонн/час 334,86. Количество линий, шт. 2.",
    }]
    row = compare_requirements([requirement], [], [], corpus)[0]
    assert row["status"] == "Выявлено отклонение"
    assert row["verification_kernel"] == "CAPACITY_AND_PROCESS_TOPOLOGY"
    assert row["difference"] == 165.14


def test_grounding_requirement_is_not_closed_by_site_lighting_evidence():
    requirement = _req("Для защиты людей предусмотреть заземляющее устройство и молниезащиту с молниеприёмниками")
    corpus = [{
        "document": "Раздел ПД №2_ПЗУ1.pdf", "document_type": "ПЗУ", "page": 27,
        "text": "Освещение территории предусмотрено светильниками на опорах и мачтами освещения.",
    }]
    row = compare_requirements([requirement], [], [], corpus)[0]
    assert row["status"] != "Соответствует заданию"
    assert row.get("verification_kernel") != "SITE_LIGHTING"


def test_wrong_section_checklist_evidence_fails_quality_gate():
    plan = {
        "domains": {
            code: {"total": 0, "verified_ok": 0, "project_findings": 0, "review_questions": 0, "system_limitations": 0, "informational": 0, "completed": 0, "automatic_coverage_pct": 0}
            for code in ("assignment", "normative", "checklist")
        },
        "items": [],
    }
    checklist = [{
        "item_no": "1.8.1", "automatic_section": "ИОС2",
        "deep_evidence_candidates": [{"document": "Раздел ПД №1_ПЗ.pdf", "section": "ПЗ", "page": 45}],
    }]
    result = validate_review_plan(plan, checklist_rows=checklist)
    assert result["status"] == "FAILED"
    assert result["wrong_section_evidence"] == 1


def test_technical_comparison_frame_maps_current_engine_schema():
    frames = _compact_technical_frames([], [], [{
        "comparison_id": "C-1", "object_name": "Компрессорная", "parameter_name": "Площадь застройки",
        "status": "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ", "document_values": "ПЗ: 54,3 | ПЗУ: 48,7",
    }], {"excluded_objects": [], "unresolved_objects": []})
    row = frames["Тех_сверки"].iloc[0]
    assert row["parameter"] == "Площадь застройки"
    assert row["values_by_section"] == "ПЗ: 54,3 | ПЗУ: 48,7"
