from pathlib import Path

from core20.normative_execution import NormativeExecutionEngine20
from core20.normative_foundation import NormativeKnowledgeFoundation20
from core20.normative_proof import NormativeProofEngine20


ROOT = Path(__file__).resolve().parents[1] / "knowledge"


def _foundation():
    return NormativeKnowledgeFoundation20(ROOT)


def test_alpha9_direct_presence_can_remain_verified_with_addressable_evidence():
    engine = NormativeExecutionEngine20(_foundation())
    documents = [{"Файл": "Раздел ПД №2_ПЗУ1.pdf", "Тип документа": "ПЗУ"}]
    pages = [{
        "document": "Раздел ПД №2_ПЗУ1.pdf",
        "document_type": "ПЗУ",
        "page": 7,
        "text": (
            "Характеристика земельного участка, предоставленного для размещения объекта капитального строительства. "
            "Площадь земельного участка и условия размещения объекта приведены в настоящем разделе."
        ),
    }]
    result = engine.run(documents, pages)
    row = next(x for x in result["rows"] if x["requirement_id"] == "PP87-12-A-LAND")
    assert row["retrieval_kind"] == "VERIFIED_OK"
    assert row["kind"] == "VERIFIED_OK"
    assert row["proof_type"] == "PRESENCE"
    assert row["proof_state"] == "ADDRESSABLE_PRESENCE_PROOF"
    assert row["evidence_page"] == 7


def test_alpha9_semantic_keyword_hit_is_not_normative_proof():
    engine = NormativeExecutionEngine20(_foundation())
    documents = [{"Файл": "Раздел ПД №2_ПЗУ1.pdf", "Тип документа": "ПЗУ"}]
    pages = [{
        "document": "Раздел ПД №2_ПЗУ1.pdf",
        "document_type": "ПЗУ",
        "page": 12,
        "text": (
            "Инженерной подготовке территории и инженерной защите посвящён отдельный подраздел. "
            "Упоминаются поверхностных и грунтовых вод условия площадки."
        ),
    }]
    result = engine.run(documents, pages)
    row = next(x for x in result["rows"] if x["requirement_id"] == "PP87-12-E-ENGINEERING-PREP")
    assert row["retrieval_kind"] == "VERIFIED_OK"
    assert row["kind"] == "REVIEW_QUESTION"
    assert row["proof_type"] == "SEMANTIC_REQUIREMENT"
    assert row["proof_state"] == "SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"] == "NORMATIVE_SEMANTIC_PROOF_REQUIRED"
    assert any(x["requirement_id"] == row["requirement_id"] for x in result["semantic_queue"])
    assert result["demoted_keyword_only"] >= 1
    assert result["demoted_keyword_only_initial"] == result["demoted_keyword_only"]
    assert result["demoted_keyword_only_remaining"] == result["demoted_keyword_only"]
    assert result["proof_frontier"]["blocker_counts"]["SEMANTIC_PENDING"] >= 1


def test_alpha9_graphic_clause_cannot_be_proven_from_text_layer():
    engine = NormativeExecutionEngine20(_foundation())
    documents = [{"Файл": "Раздел ПД №2_ПЗУ2.pdf", "Тип документа": "ПЗУ"}]
    pages = [{
        "document": "Раздел ПД №2_ПЗУ2.pdf",
        "document_type": "ПЗУ",
        "page": 18,
        "text": "Схема организации рельефа. План земляных масс.",
    }]
    result = engine.run(documents, pages)
    row = next(x for x in result["rows"] if x["requirement_id"] == "PP87-12-N-EARTHWORKS")
    assert row["retrieval_kind"] == "VERIFIED_OK"
    assert row["kind"] == "SYSTEM_LIMITATION"
    assert row["proof_type"] == "GRAPHIC_CONTENT"
    assert row["proof_state"] == "VISUAL_PROOF_REQUIRED"
    assert row["reason_code"] == "NORMATIVE_VISUAL_PROOF_REQUIRED"


def test_alpha9_proof_gate_never_invents_project_finding():
    source = [{
        "requirement_id": "T-SEMANTIC",
        "check_kind": "SEMANTIC",
        "requirement": "Должны быть обоснованы решения по инженерной защите территории.",
        "kind": "VERIFIED_OK",
        "state": "Подтверждено",
        "evidence_document": "ПЗУ.pdf",
        "evidence_page": 5,
        "evidence_fragment": "Инженерная защита территории предусмотрена.",
    }]
    result = NormativeProofEngine20().run(source)
    assert result["project_findings"] == 0
    assert result["verified_ok"] == 0
    assert result["review_questions"] == 1



def test_alpha9_frontier_diagnostics_split_semantic_and_retrieval_blockers():
    source = [
        {
            "requirement_id": "SEM-1",
            "document_id": "DOC-SEM",
            "source": "СП semantic",
            "paragraph": "5.1",
            "sections": ["ПЗУ"],
            "topic": "Инженерная защита",
            "check_kind": "SEMANTIC",
            "requirement": "Должны быть обоснованы решения по инженерной защите.",
            "kind": "VERIFIED_OK",
            "state": "Подтверждено",
            "evidence_document": "ПЗУ.pdf",
            "evidence_page": 5,
            "evidence_fragment": "Инженерная защита территории предусмотрена и обоснована.",
            "retrieval_candidate_count": 3,
            "evidence_candidates": [
                {"document": "ПЗУ.pdf", "page": 5, "fragment": "a"},
                {"document": "ПЗУ.pdf", "page": 6, "fragment": "b"},
                {"document": "ПЗУ.pdf", "page": 7, "fragment": "c"},
            ],
        },
        {
            "requirement_id": "RET-1",
            "document_id": "DOC-RET",
            "source": "СП retrieval",
            "paragraph": "7.2",
            "sections": ["АР"],
            "topic": "Сведения",
            "check_kind": "SEMANTIC",
            "requirement": "Должны быть приведены сведения.",
            "kind": "REVIEW_QUESTION",
            "state": "Вопрос специалисту",
            "reason_code": "NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
            "reason": "Адресное положительное доказательство не найдено.",
            "retrieval_candidate_count": 0,
            "evidence_candidates": [],
        },
    ]
    result = NormativeProofEngine20().run(source)
    frontier = result["proof_frontier"]

    assert frontier["semantic_pending"]["total"] == 1
    assert frontier["semantic_pending"]["by_source"] == {"СП semantic": 1}
    assert frontier["semantic_pending"]["by_section"] == {"ПЗУ": 1}
    assert frontier["semantic_pending"]["by_evidence_candidates"] == {"3": 1}
    assert frontier["semantic_pending"]["rows"][0]["requirement_id"] == "SEM-1"

    assert frontier["retained_fail_closed"]["total"] == 1
    assert frontier["retained_fail_closed"]["by_reason"] == {
        "NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND": 1
    }
    assert frontier["retained_fail_closed"]["by_source"] == {"СП retrieval": 1}
    assert frontier["retained_fail_closed"]["by_section"] == {"АР": 1}
    assert frontier["retained_fail_closed"]["rows"][0]["requirement_id"] == "RET-1"
