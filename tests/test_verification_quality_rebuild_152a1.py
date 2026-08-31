import json
import tempfile
from pathlib import Path

from core.assignment_verification_kernel import verify_assignment_requirement
from core.atomic_requirement_graph import atomize_requirement
from core.atomic_verification_engine import verify_atomic_requirements
from core.checklist_engine import ChecklistEngine
from core.metric_semantics import (
    CAPACITY_NOMINAL_TOTAL,
    CAPACITY_OPERATING_SECTION,
    capacity_semantic_level,
)
from core.pz_complex_object_register import _find_properties
from core.requirement_contracts import build_contract
from core.table_semantic_scope import assess_table_semantic_scope


def test_shift_duration_atom_inherits_typed_parent_parameter_and_route():
    atoms = atomize_requirement({
        "requirement_id": "Q152-SHIFT",
        "requirement_text": "Продолжительность смены – 12 часов",
        "requirement_type": "VALUE_COMPARISON",
        "parameter_code": "SHIFT_DURATION",
        "required_value": 12,
        "unit": "ч",
    })
    assert len(atoms) == 1
    assert atoms[0]["parameter_code"] == "SHIFT_DURATION"
    assert atoms[0]["focus"] == "SHIFT_DURATION"
    assert atoms[0]["evidence_contract_v2"]["scope"] == "PROJECT_GLOBAL"
    assert atoms[0]["expected_sections"] == ["ТХ", "ПЗ"]


def test_shift_duration_closes_on_exact_directed_project_clause():
    atom = atomize_requirement({
        "requirement_id": "Q152-SHIFT-EVIDENCE",
        "requirement_text": "Продолжительность смены – 12 часов",
        "requirement_type": "VALUE_COMPARISON",
        "parameter_code": "SHIFT_DURATION", "required_value": 12, "unit": "ч",
        "directed_evidence_candidates": [{
            "evidence_kind": "DIRECTED_VALUE", "evidence_state": "verified_candidate",
            "document": "Раздел ПД №6_ТХ1.pdf", "page": 33,
            "parameter_code": "SHIFT_DURATION", "value": 12, "unit": "часов",
            "context": "Режим работы — две смены, продолжительность смены 12 часов.",
            "source_trace": "продолжительность смены 12 часов",
            "exact_clause": "продолжительность смены 12 часов",
            "physical_trace_level": "ROW_TRACE", "owner_match": True,
            "unit_compatible": True, "score": 100,
        }],
    })[0]
    result = verify_atomic_requirements(
        [atom], knowledge_root="knowledge",
        fact_graph={"facts": [], "passages": []}, page_corpus=[],
    )[0]
    assert result["verification_kind"] == "VERIFIED_OK"
    assert result["verification_evidence"][0]["document"] == "Раздел ПД №6_ТХ1.pdf"


def test_annual_capacity_unit_is_atomic_and_project_scoped():
    atom = atomize_requirement({
        "requirement_id": "Q152-ANNUAL",
        "requirement_text": "Производственная мощность 1 600 тыс. тонн в год",
        "requirement_type": "VALUE_COMPARISON",
        "parameter_code": "CAPACITY",
    })[0]
    assert atom["parameter_code"] == "CAPACITY"
    assert atom["required_value"] == 1600
    assert atom["unit"] == "тыс. т/год"
    assert atom["evidence_contract_v2"]["scope"] == "PROJECT_GLOBAL"


def test_administrative_customer_word_is_not_an_engineering_qualifier():
    requirement = {
        "requirement_text": (
            "Вывоз стоков выполнять силами Заказчика; сбор ливневых стоков "
            "предусмотреть самотеком."
        ),
        "requirement_type": "PRESENCE_REQUIREMENT",
    }
    qualifiers = build_contract(requirement)["critical_qualifiers"]
    assert "заказчик" not in qualifiers
    assert "самотек" in qualifiers


def test_capacity_semantics_distinguish_total_from_operating_throughput():
    assert capacity_semantic_level("суммарной производительностью 500 т/ч") == CAPACITY_NOMINAL_TOTAL
    assert capacity_semantic_level("часовая производительность отделения 334,86 т/ч") == CAPACITY_OPERATING_SECTION


def test_operating_throughput_cannot_be_a_total_capacity_finding():
    requirement = {
        "requirement_id": "Q152-CAPACITY",
        "requirement_text": "Установить ДСК суммарной производительностью 500 т/ч с двумя независимыми линиями",
        "requirement_type": "VALUE_COMPARISON",
        "object_name": "ДСК",
        "parameter_code": "CAPACITY",
        "required_value": 500,
        "unit": "т/ч",
    }
    requirement["evidence_contract_v2"] = build_contract(requirement)
    result = verify_assignment_requirement(requirement, [{
        "document": "Раздел ПД №6_ТХ1.pdf", "document_type": "ТХ", "page": 34,
        "text": (
            "Таблица 5.1.1 - Параметры и технологические режимы. "
            "Часовая производительность отделения, тонн/час 334,86. "
            "Количество линий, шт. 2."
        ),
    }])
    assert result["status"] == "Требует проверки"
    assert result["difference"] is None
    assert result["verification_kernel"] == "CAPACITY_AND_PROCESS_TOPOLOGY"
    assert "разные по смысловому уровню" in result["decision_basis"]


def test_project_annual_capacity_can_close_on_exact_addressable_fact():
    atom = atomize_requirement({
        "requirement_id": "Q152-PROJECT-CAPACITY",
        "requirement_text": "Производственная мощность 1 600 тыс. тонн в год",
        "requirement_type": "VALUE_COMPARISON",
        "parameter_code": "CAPACITY",
    })[0]
    fact = {
        "fact_id": "FACT-Q152", "property_code": "CAPACITY",
        "property_name": "Производительность", "value": 1600,
        "unit": "тыс.т/ год", "owner": "Оборудование дробильного комплекса",
        "document": "Раздел ПД №1_ПЗ.pdf", "page": 44, "section": "ПЗ",
        "source_trace": "Производительность 1600 тыс.т/ год",
        "physical_trace_level": "CELL_TRACE", "admitted": True,
        "evidence_quality_decision": "VERIFIED", "binding_status": "ROW_LOCKED",
    }
    result = verify_atomic_requirements(
        [atom], knowledge_root="knowledge",
        fact_graph={"facts": [fact], "passages": []}, page_corpus=[],
    )[0]
    assert result["verification_kind"] == "VERIFIED_OK"
    assert result["verification_evidence"][0]["page"] == 44


def test_equipment_cannot_own_building_footprint_even_when_row_locked():
    result = assess_table_semantic_scope({
        "parameter_code": "AREA_BUILD",
        "object_hint": "Оборудование дробильного комплекса",
        "binding_status": "ROW_LOCKED",
        "context": "Сведения о сложном объекте",
        "row_text": "Площадь застройки 43414,0 м2",
    })
    assert result["table_semantic_scope_decision"] == "HOLD"
    assert result["comparison_excluded"] is True
    assert "не может быть приписана" in result["comparison_exclusion_reason"]


def test_scope_annotation_preserves_prior_plausibility_exclusion():
    result = assess_table_semantic_scope({
        "parameter_code": "HEIGHT_BUILD", "object_hint": "Насосная станция",
        "binding_status": "ROW_LOCKED", "comparison_excluded": True,
        "comparison_exclusion_reason": "размерный конфликт 25 м",
    })
    assert result["comparison_excluded"] is True
    assert result["comparison_exclusion_reason"] == "размерный конфликт 25 м"


def test_pz_capacity_unit_recovers_year_split_after_slash():
    rows = _find_properties(
        "Производительность 1600 тыс.т/ год Площадь застройки 43414,0 м2",
        {"object_hint": "Оборудование дробильного комплекса"},
    )
    capacity = next(row for row in rows if row["parameter_code"] == "CAPACITY")
    assert capacity["value"] == 1600
    assert capacity["unit"].replace(" ", "") == "тыс.т/год"


def test_standalone_known_section_title_is_not_an_actionable_check():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "catalog.json"
        path.write_text(json.dumps([
            {"source_file": "КР.xlsx", "sheet": "КР", "item_no": "1", "question": "Конструктивные решения", "document_types": ["КР"]},
            {"source_file": "КР.xlsx", "sheet": "КР", "item_no": "2", "question": "Разбивочный план", "document_types": ["КР"]},
        ], ensure_ascii=False), encoding="utf-8")
        engine = ChecklistEngine(path)
        assert engine.items[0]["is_heading"] is True
        assert engine.items[1]["is_heading"] is False
