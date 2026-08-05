from core.general_plan_engine import _clean_position, _records_from_lines
from core.object_semantics import object_candidate_evidence


def test_integer_and_decimal_positions_are_supported():
    records = _records_from_lines('1\nКарьер "Малеевский"')
    assert records == [("1", 'Карьер "Малеевский"')]
    records = _records_from_lines('3.1\nОтвал вскрышных пород № 1')
    assert records == [("3.1", "Отвал вскрышных пород № 1")]


def test_document_dates_are_not_genplan_positions():
    assert _clean_position("21.05.26") == ""
    assert _clean_position("4") == "4"
    assert _clean_position("4.13") == "4.13"


def test_named_general_plan_label_is_strong_but_not_official_explication():
    item = {
        "parameter_code": "OBJECT_CANDIDATE",
        "value_text": "Узел запорной арматуры №1",
        "object_hint": "Узел запорной арматуры №1",
        "general_plan_named_label": True,
        "general_plan_field": True,
        "structural_zone": "поле генерального плана",
    }
    strength, reasons = object_candidate_evidence(item)
    assert strength == 2
    assert any("выноска" in reason for reason in reasons)
