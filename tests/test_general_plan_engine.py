from core.general_plan_engine import GeneralPlanRegisterEngine
from core.object_register_engine import build_registry


def test_dsk_general_plan_explication_is_extracted():
    path = "/mnt/data/Раздел ПД № 2_ПЗУ2.pdf"
    with open(path, "rb") as fh:
        entries, audit = GeneralPlanRegisterEngine().extract_pdf(fh.read(), "ПЗУ2.pdf")
    by_position = {item.position: item for item in entries}
    assert "4.1" in by_position
    assert "подпорная стена" in by_position["4.1"].name.lower()
    assert "4.2" in by_position
    assert by_position["4.2"].in_explication
    assert len(audit) > 0


def test_general_plan_only_object_is_kept_in_consolidated_registry():
    findings = [{
        "document": "ПЗУ2.pdf", "document_type": "ПЗУ2", "page": 3,
        "parameter_code": "OBJECT_CANDIDATE", "value_text": "Дополнительная площадка",
        "object_hint": "Дополнительная площадка", "value": 1, "confidence": 0.95,
        "genplan_position": "7.3", "general_plan_explication": True,
        "general_plan_field": True,
    }]
    rows, _ = build_registry(findings)
    assert len(rows) == 1
    assert rows[0]["В ПЗ"] is False
    assert rows[0]["В экспликации ГП"] is True
    assert "отсутствует в пз" in rows[0]["Статус"].lower()
