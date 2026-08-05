from core.knowledge_engine import KnowledgeEngine
from core.universal_object_discovery import discover_object_candidates
from core.report_engine import build_decision_report


def test_oil_gas_profiles_are_loaded():
    engine = KnowledgeEngine()
    assert engine.classify("Дожимная насосная станция ДНС-1").code == "PUMP_STATION"
    assert engine.classify("Установка комплексной подготовки газа УКПГ").code == "OIL_TREATMENT_UNIT"
    assert engine.classify("Газопровод от куста скважин").code == "PIPELINE"
    assert "PRESSURE" in engine.expected_properties("COMPRESSOR_STATION")


def test_universal_discovery_requires_engineering_confirmation():
    findings = [
        {"parameter_code":"CAPACITY","object_hint":"Компрессорная станция КС-1","document_type":"ПЗ","document":"pz.pdf","page":10,"value":100,"confidence":0.9},
        {"parameter_code":"POWER_INSTALLED","object_hint":"Компрессорная станция КС-1","document_type":"ТХ","document":"tx.pdf","page":4,"value":500,"confidence":0.9},
    ]
    added, audit = discover_object_candidates(findings)
    assert len(added) == 1
    assert added[0]["object_type_code"] == "COMPRESSOR_STATION"
    assert any(row["decision"] == "принято" for row in audit)


def test_document_title_is_not_discovered_as_object():
    findings = [
        {"parameter_code":"CAPACITY","object_hint":"Технологические решения","document_type":"ТХ","document":"tx.pdf","page":1,"value":10,"confidence":0.9},
        {"parameter_code":"POWER_INSTALLED","object_hint":"Технологические решения","document_type":"ПЗ","document":"pz.pdf","page":2,"value":20,"confidence":0.9},
    ]
    added, _ = discover_object_candidates(findings)
    assert added == []


def test_decision_report_hides_confirmed_rows_from_problems():
    documents = [{"consolidated_registry":[{"Позиция":"1"},{"Позиция":"2"}]}]
    comparisons = [
        {"object":"КС","parameter_name":"Мощность","status":"СОВПАДАЕТ"},
        {"object":"КС","parameter_name":"Производительность","status":"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ","document_values":"ПЗ: 10; ТХ: 12"},
    ]
    report = build_decision_report(documents, comparisons)
    assert report["summary"]["objects"] == 2
    assert report["summary"]["requires_attention"] == 1
    assert len(report["problems"]) == 1
