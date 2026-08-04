from core.passport_engine import build_object_passports, passport_summary


def test_passport_is_built_from_registry_and_groups_sources():
    registry = [{
        "Позиция по ГП": "2.1.1",
        "Родительская позиция": "2.1",
        "Наименование объекта": "Насосная станция золотосодержащих растворов",
        "Количество": 1,
        "Статус": "Подтверждено несколькими разделами",
    }]
    findings = [
        {"parameter_code": "OBJECT_ENTRY", "value_text": "Насосная станция золотосодержащих растворов", "object_hint": "Насосная станция золотосодержащих растворов", "genplan_position": "2.1.1", "document_type": "ПЗ"},
        {"parameter_code": "TOTAL_AREA", "parameter_name": "Общая площадь", "value_text": "147,7", "unit": "м²", "object_hint": "Насосная станция золотосодержащих растворов", "genplan_position": "2.1.1", "document_type": "ПЗ", "page": 10, "confidence": 0.95},
        {"parameter_code": "TOTAL_AREA", "parameter_name": "Общая площадь", "value_text": "147,7", "unit": "м²", "object_hint": "Насосная станция золотосодержащих растворов", "genplan_position": "2.1.1", "document_type": "АР1", "page": 3, "confidence": 0.94},
    ]
    passports = build_object_passports(registry, findings, [])
    assert len(passports) == 1
    passport = passports[0]
    assert passport.position == "2.1.1"
    assert passport.confirmation_matrix["ПЗ"] == "Подтверждено"
    assert passport.confirmation_matrix["АР"] == "Подтверждено"
    assert passport.characteristics[0].source_count == 2
    assert passport.passport_completeness > 0


def test_passport_summary():
    registry = [{"Позиция по ГП": "1.1", "Наименование объекта": "КТП", "Количество": 1}]
    passports = build_object_passports(registry, [], [])
    summary = passport_summary(passports)
    assert summary["passport_count"] == 1
    assert summary["average_completeness"] == 0.0
