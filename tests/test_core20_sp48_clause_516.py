from pathlib import Path

from core20.normative_execution import NormativeExecutionEngine20
from core20.normative_foundation import NormativeKnowledgeFoundation20


ROOT = Path(__file__).resolve().parents[1] / "knowledge"
RID = "SP48-5.16-SUPPLY-TRANSPORT-TEP"


def _foundation():
    return NormativeKnowledgeFoundation20(ROOT)


def test_sp48_516_is_verified_strict_contract():
    foundation = _foundation()
    contract = next(row for row in foundation.contracts() if row["requirement_id"] == RID)
    summary = foundation.summary()

    assert contract["trust_state"] == "VERIFIED_CLAUSE"
    assert contract["automatic_contract_ready"] is True
    assert contract["document_id"] == "SP-48.13330.2019"
    assert contract["paragraph"] == "п. 5.16"
    assert contract["sections"] == ["ПОС"]
    assert contract["evidence_contract"]["proof_type"] == "SEMANTIC_REQUIREMENT"
    assert summary["automatic_contract_ready"] >= 67
    assert summary["triggered_only_contracts"] >= 2
    assert summary["default_active_contracts"] >= 65


def test_sp48_516_is_not_routed_when_pos_section_is_absent():
    routes = _foundation().project_routes([
        {"Файл": "Раздел ПД №1_ПЗ.pdf", "Тип документа": "ПЗ"},
        {"Файл": "Раздел ПД №3_АР.pdf", "Тип документа": "АР"},
    ])
    row = next(item for item in routes["rows"] if item["requirement_id"] == RID)

    assert row["project_relevant"] is False
    assert row["project_applicability_state"] == "NOT_ROUTED_BY_SECTION"


def test_sp48_516_routes_to_pos_and_requires_semantic_proof():
    engine = NormativeExecutionEngine20(_foundation())
    documents = [{"Файл": "Раздел ПД №7_ПОС.pdf", "Тип документа": "ПОС"}]
    pages = [{
        "document": "Раздел ПД №7_ПОС.pdf",
        "document_type": "ПОС",
        "page": 18,
        "text": (
            "Транспортная схема доставки основных строительных материалов принята после "
            "сравнения технико-экономических показателей двух вариантов поставки. "
            "Рассмотрены поставщики А и Б, расстояния доставки и транспортные затраты; "
            "по результатам сравнения выбран поставщик А."
        ),
    }]

    result = engine.run(documents, pages)
    row = next(item for item in result["rows"] if item["requirement_id"] == RID)

    assert row["retrieval_kind"] == "VERIFIED_OK"
    assert row["kind"] == "REVIEW_QUESTION"
    assert row["proof_type"] == "SEMANTIC_REQUIREMENT"
    assert row["proof_state"] == "SEMANTIC_PROOF_REQUIRED"
    assert row["evidence_document"] == "Раздел ПД №7_ПОС.pdf"
    assert row["evidence_page"] == 18
    assert row["evidence_candidates"]
    assert result["project_findings"] == 0
