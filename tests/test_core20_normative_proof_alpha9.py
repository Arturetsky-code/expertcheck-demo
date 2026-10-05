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



def test_alpha9_graphic_requirement_with_no_text_evidence_routes_to_visual_proof():
    source = [{
        "requirement_id": "PP87-13-L1-FLOOR-PLANS",
        "check_kind": "SEMANTIC",
        "requirement": "Графическая часть АР должна содержать поэтажные планы с экспликацией помещений.",
        "kind": "REVIEW_QUESTION",
        "state": "Вопрос специалисту",
        "reason_code": "NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
        "reason": "Адресное положительное доказательство не найдено.",
        "sections": ["АР"],
        "retrieval_candidate_count": 0,
        "evidence_candidates": [],
    }]

    result = NormativeProofEngine20().run(source)
    row = result["rows"][0]

    assert row["retrieval_kind"] == "REVIEW_QUESTION"
    assert row["kind"] == "SYSTEM_LIMITATION"
    assert row["proof_type"] == "GRAPHIC_CONTENT"
    assert row["proof_state"] == "VISUAL_PROOF_REQUIRED"
    assert row["reason_code"] == "NORMATIVE_VISUAL_PROOF_REQUIRED"
    assert result["review_questions"] == 0
    assert result["system_limitations"] == 1
    assert result["proof_frontier"]["blocker_counts"]["VISUAL_PROOF_REQUIRED"] == 1
    assert result["proof_frontier"]["retained_fail_closed"]["total"] == 0


def test_alpha9_graphic_requirement_with_weak_text_candidate_routes_to_visual_proof():
    source = [{
        "requirement_id": "PP87-13-I-FACADES",
        "check_kind": "SEMANTIC",
        "requirement": "Графическая часть АР должна содержать отображение фасадов.",
        "kind": "REVIEW_QUESTION",
        "state": "Вопрос специалисту",
        "reason_code": "NORMATIVE_EVIDENCE_WEAK",
        "reason": "Найден адресный кандидат, но retrieval недостаточно сильный.",
        "sections": ["АР"],
        "retrieval_candidate_count": 4,
        "evidence_candidates": [
            {"document": "АР.pdf", "page": 1, "fragment": "Фасад 1"},
            {"document": "АР.pdf", "page": 2, "fragment": "Фасад 2"},
            {"document": "АР.pdf", "page": 3, "fragment": "Фасад 3"},
            {"document": "АР.pdf", "page": 4, "fragment": "Фасад 4"},
        ],
    }]

    result = NormativeProofEngine20().run(source)
    row = result["rows"][0]

    assert row["kind"] == "SYSTEM_LIMITATION"
    assert row["proof_state"] == "VISUAL_PROOF_REQUIRED"
    assert result["system_limitations"] == 1


def test_alpha9_graphic_requirement_with_unproven_applicability_stays_fail_closed():
    source = [{
        "requirement_id": "PP87-13-L2-SECTIONS",
        "check_kind": "SEMANTIC",
        "requirement": "Для применимого объекта графическая часть АР должна содержать характерные разрезы.",
        "kind": "REVIEW_QUESTION",
        "state": "Вопрос специалисту",
        "reason_code": "NORMATIVE_APPLICABILITY_NOT_PROVEN",
        "reason": "Условная применимость требования не доказана.",
        "sections": ["АР"],
        "retrieval_candidate_count": 0,
        "evidence_candidates": [],
    }]

    result = NormativeProofEngine20().run(source)
    row = result["rows"][0]

    assert row["kind"] == "REVIEW_QUESTION"
    assert row["proof_state"] == "RETAINED_FAIL_CLOSED"
    assert row["reason_code"] == "NORMATIVE_APPLICABILITY_NOT_PROVEN"
    assert result["review_questions"] == 1
    assert result["system_limitations"] == 0



def test_alpha9_recoverable_near_miss_requires_semantic_proof():
    source = [{
        "requirement_id": "X-NEAR-MISS",
        "source": "384-ФЗ",
        "paragraph": "ст. 15, ч. 2",
        "sections": ["ALL"],
        "check_kind": "SEMANTIC",
        "requirement": "В исходных данных должен быть указан уровень ответственности объекта.",
        "kind": "REVIEW_QUESTION",
        "state": "Вопрос специалисту",
        "reason_code": "NORMATIVE_STRONG_NEAR_MISS_CANDIDATE",
        "reason": "Сильный token-level near-miss.",
        "evidence_document": "Задание.pdf",
        "evidence_page": 11,
        "evidence_fragment": "В задании определён уровень ответственности проектируемого объекта.",
        "retrieval_candidate_count": 1,
        "evidence_candidates": [{
            "evidence_id": "NORM-E-X-01",
            "document": "Задание.pdf",
            "page": 11,
            "section": "Задание на проектирование",
            "fragment": "В задании определён уровень ответственности проектируемого объекта.",
            "matched_keywords": ["задание", "уровень", "ответственности", "проектируемого"],
            "retrieval_keyword_score": 4,
            "retrieval_keyword_coverage": 0.8,
            "retrieval_admission": "STRONG_NEAR_MISS",
        }],
    }]

    result = NormativeProofEngine20().run(source)
    row = result["rows"][0]

    assert row["retrieval_kind"] == "REVIEW_QUESTION"
    assert row["retrieval_reason_code"] == "NORMATIVE_STRONG_NEAR_MISS_CANDIDATE"
    assert row["kind"] == "REVIEW_QUESTION"
    assert row["proof_state"] == "SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"] == "NORMATIVE_SEMANTIC_PROOF_REQUIRED"
    assert result["verified_ok"] == 0
    assert result["semantic_queue_total"] == 1
    assert result["semantic_queue"][0]["evidence"][0]["document"] == "Задание.pdf"
    assert result["proof_frontier"]["semantic_pending"]["by_retrieval_admission"] == {
        "STRONG_NEAR_MISS": 1
    }


def test_alpha9_weak_phrase_candidate_requires_semantic_proof_not_direct_verification():
    source = [{
        "requirement_id": "X-WEAK",
        "source": "СП",
        "paragraph": "1.1",
        "sections": ["ПЗУ"],
        "check_kind": "SEMANTIC",
        "requirement": "Должны быть обоснованы решения по инженерной защите.",
        "kind": "REVIEW_QUESTION",
        "state": "Вопрос специалисту",
        "reason_code": "NORMATIVE_EVIDENCE_WEAK",
        "reason": "Evidence найдено, но retrieval недостаточно сильный.",
        "evidence_document": "ПЗУ.pdf",
        "evidence_page": 8,
        "evidence_fragment": "Инженерная защита территории предусмотрена.",
        "retrieval_candidate_count": 1,
        "evidence_candidates": [{
            "evidence_id": "NORM-E-X-WEAK-01",
            "document": "ПЗУ.pdf",
            "page": 8,
            "section": "ПЗУ",
            "fragment": "Инженерная защита территории предусмотрена.",
            "matched_keywords": ["инженерная защита"],
            "retrieval_keyword_score": 1,
            "retrieval_keyword_coverage": 0.5,
        }],
    }]

    result = NormativeProofEngine20().run(source)
    row = result["rows"][0]

    assert row["proof_state"] == "SEMANTIC_PROOF_REQUIRED"
    assert row["kind"] == "REVIEW_QUESTION"
    assert result["verified_ok"] == 0
    assert result["semantic_queue_total"] == 1
    assert result["proof_frontier"]["semantic_pending"]["by_retrieval_admission"] == {
        "WEAK_RETRIEVAL": 1
    }



def test_alpha9_explicit_proof_type_overrides_lexical_set_markers():
    source = [{
        "requirement_id": "EXPLICIT-SEMANTIC",
        "check_kind": "SEMANTIC",
        "proof_type_hint": "SEMANTIC_REQUIREMENT",
        "requirement": "Для поверхностного комплекса должен быть приведён перечень мероприятий.",
        "kind": "VERIFIED_OK",
        "state": "Подтверждено",
        "evidence_document": "АР.pdf",
        "evidence_page": 12,
        "evidence_fragment": "Перечень мероприятий для поверхностного комплекса приведён.",
        "retrieval_candidate_count": 1,
        "evidence_candidates": [{
            "evidence_id": "E-1",
            "document": "АР.pdf",
            "page": 12,
            "section": "АР",
            "fragment": "Перечень мероприятий для поверхностного комплекса приведён.",
        }],
    }]

    result = NormativeProofEngine20().run(source)
    row = result["rows"][0]

    assert row["proof_type"] == "SEMANTIC_REQUIREMENT"
    assert row["proof_state"] == "SEMANTIC_PROOF_REQUIRED"
    assert result["semantic_queue_total"] == 1
    assert result["set_completeness_queue_total"] == 0



def test_alpha9_frontier_exposes_set_and_applicability_trace():
    source = [{
        "requirement_id": "SET-1",
        "source": "ПП №87",
        "paragraph": "п. 15",
        "check_kind": "STRUCTURE",
        "proof_type_hint": "SET_COMPLETENESS",
        "requirement": "Должен быть предусмотрен состав применимых подразделов.",
        "kind": "VERIFIED_OK",
        "state": "Подтверждено",
        "evidence_document": "ИОС1.pdf",
        "evidence_page": 1,
        "evidence_fragment": "Подраздел ИОС1.",
        "retrieval_candidate_count": 1,
        "evidence_candidates": [{
            "evidence_id": "E-SET-1",
            "document": "ИОС1.pdf",
            "page": 1,
            "section": "ИОС",
            "fragment": "Подраздел ИОС1.",
        }],
        "applicability_reason_code": "PROJECT_CORPUS_CONDITION_PROVEN",
        "applicability_trace": [{
            "document": "ПЗ.pdf",
            "page": 3,
            "section": "ПЗ",
            "matched_condition": "система электроснабжения",
            "fragment": "На объекте предусмотрена система электроснабжения.",
        }],
    }]

    result = NormativeProofEngine20().run(source)
    frontier = result["proof_frontier"]

    assert frontier["set_completeness"]["total"] == 1
    assert frontier["set_completeness"]["rows"][0]["requirement_id"] == "SET-1"
    assert frontier["applicability_trace"]["total"] == 1
    assert frontier["applicability_trace"]["rows"][0]["document"] == "ПЗ.pdf"
    assert result["set_completeness_queue_total"] == 1



def test_alpha9_complete_set_moves_to_semantic_proof_not_verified_ok():
    source=[{
        "requirement_id":"SET-COMPLETE",
        "source":"НТД",
        "paragraph":"1.1",
        "sections":["ПЗ"],
        "check_kind":"SEMANTIC",
        "proof_type_hint":"SET_COMPLETENESS",
        "requirement":"Должны быть предусмотрены первый и второй обязательные элементы.",
        "kind":"VERIFIED_OK",
        "state":"Подтверждено",
        "evidence_document":"ПЗ.pdf",
        "evidence_page":5,
        "evidence_fragment":"Первый обязательный элемент.",
        "retrieval_candidate_count":1,
        "evidence_candidates":[{
            "evidence_id":"R-1",
            "document":"ПЗ.pdf",
            "page":5,
            "section":"ПЗ",
            "fragment":"Первый обязательный элемент.",
        }],
        "set_completeness":{
            "configured":True,
            "mode":"ALL_REQUIRED",
            "promotion_policy":"SEMANTIC_AFTER_COMPLETE",
            "atomization_complete":True,
            "complete":True,
            "matched_count":2,
            "total_count":2,
            "missing_ids":[],
            "missing_labels":[],
            "evidence":[
                {
                    "evidence_id":"SET-1",
                    "document":"ПЗ.pdf",
                    "page":5,
                    "section":"ПЗ",
                    "fragment":"Первый обязательный элемент.",
                    "matched_terms":["первый обязательный элемент"],
                    "set_element_id":"first",
                    "set_element_label":"Первый элемент",
                },
                {
                    "evidence_id":"SET-2",
                    "document":"ПЗ.pdf",
                    "page":8,
                    "section":"ПЗ",
                    "fragment":"Второй обязательный элемент.",
                    "matched_terms":["второй обязательный элемент"],
                    "set_element_id":"second",
                    "set_element_label":"Второй элемент",
                },
            ],
        },
    }]

    result=NormativeProofEngine20().run(source)
    row=result["rows"][0]

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"]=="NORMATIVE_SET_COMPLETENESS_VERIFIED_SEMANTIC_REQUIRED"
    assert result["verified_ok"]==0
    assert result["set_completeness_queue_total"]==0
    assert result["semantic_queue_total"]==1
    assert len(result["semantic_queue"][0]["evidence"])==2
    assert {
        item["set_element_id"] for item in result["semantic_queue"][0]["evidence"]
    }=={"first","second"}


def test_alpha9_incomplete_set_stays_set_proof_contract_required():
    source=[{
        "requirement_id":"SET-INCOMPLETE",
        "source":"НТД",
        "paragraph":"1.1",
        "sections":["ПЗ"],
        "check_kind":"SEMANTIC",
        "proof_type_hint":"SET_COMPLETENESS",
        "requirement":"Должны быть предусмотрены первый и второй обязательные элементы.",
        "kind":"VERIFIED_OK",
        "state":"Подтверждено",
        "evidence_document":"ПЗ.pdf",
        "evidence_page":5,
        "evidence_fragment":"Первый обязательный элемент.",
        "retrieval_candidate_count":1,
        "evidence_candidates":[{
            "evidence_id":"R-1",
            "document":"ПЗ.pdf",
            "page":5,
            "section":"ПЗ",
            "fragment":"Первый обязательный элемент.",
        }],
        "set_completeness":{
            "configured":True,
            "mode":"ALL_REQUIRED",
            "promotion_policy":"SEMANTIC_AFTER_COMPLETE",
            "atomization_complete":True,
            "complete":False,
            "matched_count":1,
            "total_count":2,
            "missing_ids":["second"],
            "missing_labels":["Второй элемент"],
            "evidence":[],
        },
    }]

    result=NormativeProofEngine20().run(source)
    row=result["rows"][0]

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SET_PROOF_CONTRACT_REQUIRED"
    assert row["reason_code"]=="NORMATIVE_SET_COMPLETENESS_NOT_PROVEN"
    assert "Второй элемент" in row["reason"]
    assert result["set_completeness_queue_total"]==1
    assert result["semantic_queue_total"]==0



def test_alpha9_graphic_contract_enters_visual_queue_with_preflight():
    source=[{
        "requirement_id":"VIS-1",
        "source":"ПП №87",
        "paragraph":"п. 13",
        "sections":["АР"],
        "topic":"Фасады",
        "check_kind":"SEMANTIC",
        "proof_type_hint":"GRAPHIC_CONTENT",
        "requirement":"Графическая часть АР должна содержать фасады.",
        "kind":"VERIFIED_OK",
        "state":"Подтверждено",
        "reason_code":"NORMATIVE_RETRIEVAL_CANDIDATE_CONFIRMED",
        "evidence_document":"АР.pdf",
        "evidence_page":5,
        "evidence_fragment":"Фасады.",
        "retrieval_candidate_count":1,
        "evidence_candidates":[{
            "evidence_id":"E-1",
            "document":"АР.pdf",
            "page":5,
            "section":"АР",
            "fragment":"Фасады.",
        }],
        "visual_preflight":{
            "configured":True,
            "visual_kind":"AR_FACADES",
            "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
            "ready_for_visual_review":True,
            "coverage_count":1,
            "total_count":1,
            "missing_labels":[],
            "elements":[{
                "id":"facade_views",
                "label":"Отображение фасадов",
                "matched_in_text_layer":True,
                "candidate_locations":[{"document":"АР.pdf","page":5,"section":"АР"}],
            }],
            "candidate_pages":[{
                "document":"АР.pdf",
                "page":5,
                "section":"АР",
                "marker_hits":["фасады"],
                "element_hits":["facade_views"],
                "element_hit_labels":["Отображение фасадов"],
                "score":3,
                "fragment":"Фасады.",
            }],
        },
    }]

    result=NormativeProofEngine20().run(source)
    row=result["rows"][0]

    assert row["kind"]=="SYSTEM_LIMITATION"
    assert row["proof_state"]=="VISUAL_PROOF_REQUIRED"
    assert result["verified_ok"]==0
    assert result["visual_queue_total"]==1
    packet=result["visual_queue"][0]
    assert packet["visual_kind"]=="AR_FACADES"
    assert packet["ready_for_visual_review"] is True
    assert packet["coverage_count"]==1
    assert packet["candidate_pages"][0]["page"]==5
    assert result["proof_frontier"]["visual_pending"]["total"]==1
    assert result["visual_item_queue_total"]==1
    assert result["visual_item_queue_addressed"]==1
    assert result["visual_item_queue_sheet_fallback"]==0
    assert result["visual_item_queue_unresolved"]==0
    assert result["visual_item_queue"][0]["element_id"]=="facade_views"
    assert result["visual_item_queue"][0]["localization_source"]=="ELEMENT_ADDRESS"



def test_alpha9_visual_item_queue_falls_back_to_contract_sheet():
    source=[{
        "requirement_id":"VIS-FALLBACK",
        "source":"ПП №87",
        "paragraph":"п. 13",
        "sections":["АР"],
        "topic":"Поэтажные планы",
        "check_kind":"SEMANTIC",
        "proof_type_hint":"GRAPHIC_CONTENT",
        "requirement":"На плане должно быть показано технологическое оборудование.",
        "kind":"REVIEW_QUESTION",
        "state":"Вопрос специалисту",
        "reason_code":"NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
        "evidence_candidates":[],
        "visual_preflight":{
            "configured":True,
            "visual_kind":"AR_FLOOR_PLANS",
            "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
            "ready_for_visual_review":True,
            "selection_source":"DRAWING_INTELLIGENCE_V2",
            "coverage_count":0,
            "total_count":1,
            "structural_target_count":0,
            "structural_confirmed_count":0,
            "structural_review_required_count":0,
            "visual_review_required_count":1,
            "structural_proof_complete":False,
            "elements":[{
                "id":"equipment_layout",
                "label":"Размещение технологического оборудования",
                "verification_mode":"VISUAL_CONTENT",
                "matched_in_text_layer":False,
                "structural_confirmed":False,
                "visual_review_required":True,
                "proof_status":"VISUAL_NOT_LOCATED",
                "candidate_locations":[],
            }],
            "candidate_pages":[{
                "document":"АР2.pdf",
                "page":37,
                "section":"АР",
                "selection_source":"DRAWING_INTELLIGENCE_V2",
                "drawing_kinds":["floor_plan"],
                "sheet_title":"План",
            }],
        },
    }]

    result=NormativeProofEngine20().run(source)

    assert result["visual_item_queue_total"]==1
    assert result["visual_item_queue_addressed"]==0
    assert result["visual_item_queue_sheet_fallback"]==1
    assert result["visual_item_queue_unresolved"]==0
    item=result["visual_item_queue"][0]
    assert item["localization_source"]=="CONTRACT_SHEET_FALLBACK"
    assert item["candidate_pages"][0]["page"]==37
    assert item["status"]=="READY_VISUAL_REVIEW"



def test_alpha9_graphic_sheet_presence_can_close_from_trusted_structural_proof():
    source=[{
        "requirement_id":"VIS-FACADE-STRUCTURAL",
        "source":"ПП №87",
        "paragraph":"п. 13",
        "sections":["АР"],
        "topic":"Фасады",
        "check_kind":"SEMANTIC",
        "proof_type_hint":"GRAPHIC_CONTENT",
        "requirement":"Графическая часть АР должна содержать отображение фасадов.",
        "kind":"REVIEW_QUESTION",
        "state":"Вопрос специалисту",
        "reason_code":"NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
        "evidence_candidates":[],
        "visual_preflight":{
            "configured":True,
            "visual_kind":"AR_FACADES",
            "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
            "ready_for_visual_review":True,
            "selection_source":"DRAWING_INTELLIGENCE_V2",
            "coverage_count":1,
            "total_count":1,
            "structural_confirmed_count":1,
            "visual_review_required_count":0,
            "structural_proof_complete":True,
            "remaining_visual_labels":[],
            "elements":[{
                "id":"facade_views",
                "label":"Отображение фасадов",
                "verification_mode":"SHEET_PRESENCE",
                "matched_in_text_layer":True,
                "structural_confirmed":True,
                "visual_review_required":False,
                "proof_status":"STRUCTURAL_CONFIRMED",
                "candidate_locations":[{
                    "document":"АР2.pdf",
                    "page":22,
                    "selection_source":"DRAWING_INTELLIGENCE_V2",
                }],
            }],
            "candidate_pages":[{
                "document":"АР2.pdf",
                "page":22,
                "section":"АР",
                "selection_source":"DRAWING_INTELLIGENCE_V2",
                "drawing_kinds":["facade"],
                "sheet_title":"Фасады",
                "designation":"RAM-АР2-22",
                "fragment":"Фасады",
            }],
        },
    }]

    result=NormativeProofEngine20().run(source)
    row=result["rows"][0]

    assert row["kind"]=="VERIFIED_OK"
    assert row["state"]=="Подтверждено"
    assert row["proof_state"]=="DETERMINISTIC_GRAPHIC_STRUCTURE_PROOF"
    assert row["reason_code"]=="NORMATIVE_GRAPHIC_STRUCTURE_PROOF_CONFIRMED"
    assert row["evidence_document"]=="АР2.pdf"
    assert row["evidence_page"]==22
    assert result["verified_ok"]==1
    assert result["visual_queue_total"]==0


def test_alpha9_structural_graphic_proof_cannot_override_unproven_applicability():
    source=[{
        "requirement_id":"VIS-CONDITIONAL",
        "check_kind":"SEMANTIC",
        "proof_type_hint":"GRAPHIC_CONTENT",
        "requirement":"Для применимого объекта должен быть графический лист.",
        "kind":"REVIEW_QUESTION",
        "state":"Вопрос специалисту",
        "reason_code":"NORMATIVE_APPLICABILITY_NOT_PROVEN",
        "reason":"Условная применимость требования не доказана.",
        "sections":["АР"],
        "evidence_candidates":[],
        "visual_preflight":{
            "configured":True,
            "structural_proof_complete":True,
            "candidate_pages":[{
                "document":"АР.pdf",
                "page":2,
                "selection_source":"DRAWING_INTELLIGENCE_V2",
                "sheet_title":"Разрез",
            }],
        },
    }]

    result=NormativeProofEngine20().run(source)
    row=result["rows"][0]

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="RETAINED_FAIL_CLOSED"
    assert row["reason_code"]=="NORMATIVE_APPLICABILITY_NOT_PROVEN"
    assert result["verified_ok"]==0



def test_alpha9_explicit_presence_check_kind_bypasses_semantic_queue():
    source=[{
        "requirement_id":"PRESENCE-EXPLICIT",
        "source":"НТД",
        "paragraph":"1.1",
        "sections":["ПЗ"],
        "check_kind":"PRESENCE",
        "requirement":"Сведения должны быть указаны в проектной документации.",
        "kind":"VERIFIED_OK",
        "state":"Подтверждено",
        "reason_code":"NORMATIVE_RETRIEVAL_CANDIDATE_CONFIRMED",
        "evidence_document":"ПЗ.pdf",
        "evidence_page":7,
        "evidence_fragment":"Категория помещения В1 указана в проектной документации.",
        "retrieval_candidate_count":1,
        "evidence_candidates":[{
            "evidence_id":"E-PRESENCE-1",
            "document":"ПЗ.pdf",
            "page":7,
            "section":"ПЗ",
            "fragment":"Категория помещения В1 указана в проектной документации.",
        }],
    }]

    result=NormativeProofEngine20().run(source)
    row=result["rows"][0]

    assert row["proof_type"]=="PRESENCE"
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="ADDRESSABLE_PRESENCE_PROOF"
    assert result["semantic_queue_total"]==0


def test_alpha9_explicit_presence_does_not_promote_weak_retrieval():
    source=[{
        "requirement_id":"PRESENCE-WEAK",
        "source":"НТД",
        "paragraph":"1.1",
        "sections":["ПЗ"],
        "check_kind":"PRESENCE",
        "requirement":"Сведения должны быть указаны в проектной документации.",
        "kind":"REVIEW_QUESTION",
        "state":"Вопрос специалисту",
        "reason_code":"NORMATIVE_EVIDENCE_WEAK",
        "evidence_document":"ПЗ.pdf",
        "evidence_page":7,
        "evidence_fragment":"Категория.",
        "retrieval_candidate_count":1,
        "evidence_candidates":[{
            "evidence_id":"E-PRESENCE-WEAK",
            "document":"ПЗ.pdf",
            "page":7,
            "section":"ПЗ",
            "fragment":"Категория.",
        }],
    }]

    result=NormativeProofEngine20().run(source)
    row=result["rows"][0]

    assert row["proof_type"]=="PRESENCE"
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert result["verified_ok"]==0



def test_alpha9_complete_set_can_promote_deterministically_when_contract_allows():
    source=[{
        "requirement_id":"SET-DETERMINISTIC",
        "source":"ПП №87",
        "paragraph":"п. 12",
        "sections":["ПЗУ"],
        "check_kind":"SEMANTIC",
        "proof_type_hint":"SET_COMPLETENESS",
        "requirement":"Должны быть приведены характеристики и технические показатели.",
        "kind":"VERIFIED_OK",
        "state":"Подтверждено",
        "evidence_document":"ПЗУ.pdf",
        "evidence_page":5,
        "evidence_fragment":"Характеристики транспортных коммуникаций.",
        "retrieval_candidate_count":2,
        "evidence_candidates":[{
            "evidence_id":"R-1",
            "document":"ПЗУ.pdf",
            "page":5,
            "section":"ПЗУ",
            "fragment":"Характеристики транспортных коммуникаций.",
        },{
            "evidence_id":"R-2",
            "document":"ПЗУ.pdf",
            "page":6,
            "section":"ПЗУ",
            "fragment":"Технический показатель ширины проезда — 6,0 м.",
        }],
        "set_completeness":{
            "configured":True,
            "mode":"ALL_REQUIRED",
            "promotion_policy":"DETERMINISTIC_AFTER_COMPLETE",
            "atomization_complete":True,
            "complete":True,
            "matched_count":2,
            "total_count":2,
            "missing_ids":[],
            "missing_labels":[],
            "evidence":[
                {
                    "evidence_id":"SET-CHAR",
                    "document":"ПЗУ.pdf",
                    "page":5,
                    "section":"ПЗУ",
                    "fragment":"Характеристики транспортных коммуникаций.",
                    "matched_terms":["характеристики"],
                    "set_element_id":"transport_characteristics",
                    "set_element_label":"Характеристики транспортных коммуникаций",
                },
                {
                    "evidence_id":"SET-TEP",
                    "document":"ПЗУ.pdf",
                    "page":6,
                    "section":"ПЗУ",
                    "fragment":"Технический показатель ширины проезда — 6,0 м.",
                    "matched_terms":["технические показатели"],
                    "set_element_id":"transport_technical_indicators",
                    "set_element_label":"Технические показатели транспортных коммуникаций",
                },
            ],
        },
    }]

    result=NormativeProofEngine20().run(source)
    row=result["rows"][0]

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["reason_code"]=="NORMATIVE_SET_COMPLETENESS_PROOF_CONFIRMED"
    assert result["semantic_queue_total"]==0
    assert result["set_completeness_queue_total"]==0



def test_alpha9_fz384_responsibility_level_is_deterministic_presence():
    foundation=_foundation()
    contracts={row["requirement_id"]:row for row in foundation.contracts()}
    contract=contracts["FZ384-4-7-RESP-LEVEL"]

    assert contract["check_kind"]=="PRESENCE"
    assert contract["evidence_contract"]["execution_mode"]=="POSITIVE_PRESENCE_ONLY"

    engine=NormativeExecutionEngine20(foundation)
    documents=[
        {"Файл":"ПЗ.pdf","Тип документа":"ПЗ"},
        {"Файл":"КР.pdf","Тип документа":"КР"},
    ]
    pages=[{
        "document":"ПЗ.pdf",
        "document_type":"ПЗ",
        "page":6,
        "text":"Для проектируемого здания установлен нормальный уровень ответственности.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FZ384-4-7-RESP-LEVEL")

    assert row["retrieval_kind"]=="VERIFIED_OK"
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_type"]=="PRESENCE"
    assert row["proof_state"]=="ADDRESSABLE_PRESENCE_PROOF"
    assert row["reason_code"]=="NORMATIVE_PRESENCE_PROOF_CONFIRMED"
    assert not any(
        packet["requirement_id"]=="FZ384-4-7-RESP-LEVEL"
        for packet in result["semantic_queue"]
    )


def test_alpha9_fz384_responsibility_level_never_invents_negative_without_evidence():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"ПЗ.pdf","Тип документа":"ПЗ"}]
    pages=[{
        "document":"ПЗ.pdf",
        "document_type":"ПЗ",
        "page":6,
        "text":"Общие сведения о проектируемом объекте.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FZ384-4-7-RESP-LEVEL")

    assert row["kind"]!="PROJECT_FINDING"
    assert row["kind"] in {"REVIEW_QUESTION","SYSTEM_LIMITATION"}
