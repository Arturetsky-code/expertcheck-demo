from pathlib import Path

from core20.normative_execution import NormativeExecutionEngine20
from core20.normative_foundation import NormativeKnowledgeFoundation20


ROOT=Path(__file__).resolve().parents[1]/"knowledge"


def _foundation():
    return NormativeKnowledgeFoundation20(ROOT)


def test_alpha8_bulk_verified_clause_pack_is_loaded():
    summary=_foundation().summary()
    assert summary["atomic_requirements_total"] >= 60
    assert summary["verified_clauses"] >= 30
    assert summary["automatic_contract_ready"] >= 30


def test_alpha8_executes_positive_evidence_with_address():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ1.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ1.pdf",
        "document_type":"ПЗУ",
        "page":7,
        "text":"Характеристика земельного участка, предоставленного для размещения объекта капитального строительства. "
               "Площадь земельного участка и условия размещения объекта приведены в настоящем разделе.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-A-LAND")
    assert row["kind"]=="VERIFIED_OK"
    assert row["evidence_document"]=="Раздел ПД №2_ПЗУ1.pdf"
    assert row["evidence_page"]==7
    assert row["evidence_fragment"]
    assert result["project_findings"]==0


def test_alpha8_missing_text_never_becomes_normative_finding():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":3,
        "text":"Общие сведения о проектируемом здании без доказательства проверяемого атомарного требования.",
    }]
    result=engine.run(documents,pages)
    assert result["contracts"] > 0
    assert result["project_findings"]==0
    assert all(row["kind"]!="PROJECT_FINDING" for row in result["rows"])
    assert any(row["kind"] in {"REVIEW_QUESTION","SYSTEM_LIMITATION"} for row in result["rows"])


def test_alpha8_conditional_clause_requires_applicability_proof():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":8,
        "text":"Приведено обоснование соответствия архитектурных решений требованиям энергетической эффективности.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B1-EFF")
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["reason_code"]=="NORMATIVE_APPLICABILITY_NOT_PROVEN"


def test_alpha8_production_conditional_clause_can_use_confirmed_project_profile():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{
        "Файл":"Раздел ПД №2_ПЗУ1.pdf",
        "Тип документа":"ПЗУ",
        "pp87_project_profile":{"profile":"Объект производственного назначения"},
    }]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ1.pdf",
        "document_type":"ПЗУ",
        "page":11,
        "text":"Выполнено зонирование территории объекта производственного назначения. "
               "Показана принципиальная схема размещения территориальных зон.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-H-ZONING")
    assert row["kind"]=="VERIFIED_OK"
    assert row["evidence_page"]==11
