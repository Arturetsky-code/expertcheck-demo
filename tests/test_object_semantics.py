from core.object_semantics import (
    canonical_parameter_code,
    classify_object,
    expected_parameters,
    is_service_object_candidate,
    parameter_applicability,
)
from core.object_register_engine import build_registry
from core.cross_section_consistency import build_cross_section_checks


def test_filename_cannot_create_object():
    findings = [{
        "parameter_code": "OBJECT_CANDIDATE",
        "value_text": "Раздел ПД № 3_АР2.pdf",
        "object_hint": "Раздел ПД № 3_АР2.pdf",
        "document": "Раздел ПД № 3_АР2.pdf",
        "document_type": "АР2",
        "confidence": 0.99,
    }]
    registry, audit = build_registry(findings)
    assert registry == []
    assert audit[0]["decision"] == "отклонено"
    assert "файл" in audit[0]["reasons"].lower() or "служеб" in audit[0]["reasons"].lower()


def test_object_type_and_expected_parameters():
    decision = classify_object("Насосная станция противопожарного водоснабжения")
    assert decision.code == "PUMP_STATION"
    assert "CAPACITY" in expected_parameters(decision.code)
    assert parameter_applicability(decision.code, "FLOORS") == "conditional"


def test_legacy_power_codes_are_normalized_and_compared():
    assert canonical_parameter_code("POWER_INST") == "POWER_INSTALLED"
    base = {
        "object_hint": "Комплектная трансформаторная подстанция КТП-1250",
        "genplan_position": "4.10",
        "value_text": "1250",
        "unit": "кВА",
        "confidence": 0.95,
        "core2_confidence": 0.95,
        "parameter_name": "Установленная мощность",
    }
    rows = build_cross_section_checks([
        dict(base, parameter_code="POWER_INST", value=1250, value_num=1250, document_type="ПЗ", document="pz.pdf", page=2),
        dict(base, parameter_code="POWER_INSTALLED", value=1250, value_num=1250, document_type="ИОС1", document="ios.pdf", page=3),
    ])
    assert len(rows) == 1
    assert rows[0]["parameter_code"] == "POWER_INSTALLED"
    assert rows[0]["status"] == "СОВПАДАЕТ"


def test_floors_not_applied_to_reservoir():
    base = {
        "object_hint": "Противопожарный резервуар",
        "genplan_position": "4.5",
        "parameter_code": "FLOORS",
        "parameter_name": "Этажность",
        "unit": "эт.",
        "confidence": 0.95,
        "core2_confidence": 0.95,
    }
    rows = build_cross_section_checks([
        dict(base, value=1, value_num=1, document_type="ПЗ", document="pz.pdf", page=2),
        dict(base, value=1, value_num=1, document_type="АР1", document="ar.pdf", page=3),
    ])
    assert rows == []
