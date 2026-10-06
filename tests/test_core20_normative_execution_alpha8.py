from pathlib import Path

from core20.normative_execution import (
    NormativeExecutionEngine20,
    _candidate_payloads,
    _near_miss_candidates,
    _strong_near_miss_evidence,
    _set_completeness_evaluation,
    _set_element_match,
    _keyword_span_diagnostic,
    _general_plan_visual_kinds_from_text,
    _visual_preflight_evaluation,
    _rank_candidates,
)
from core20.normative_foundation import NormativeKnowledgeFoundation20
from core20.normative_proof import NormativeProofEngine20


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


def test_alpha8_energy_efficiency_clause_passes_applicability_but_requires_semantic_proof():
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
    assert row["applicability_reason_code"]=="PROJECT_CORPUS_CONDITION_PROVEN"
    assert row["applicability_trace"]
    assert row["proof_type"]=="SET_COMPLETENESS"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"]=="NORMATIVE_SET_DETERMINISTIC_FAST_PATH_NOT_PROVEN"


def test_alpha8_pp87_energy_efficiency_compliance_fast_path_promotes_explicit_justification():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":9,
        "text":(
            "Соответствие архитектурных решений требованиям энергетической эффективности "
            "обосновано применением утеплённой оболочки здания и сокращением площади "
            "наружных ограждений."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B1-EFF")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["complete"] is True
    assert row["set_completeness"]["matched_count"]==1
    assert not any(
        packet["requirement_id"]=="PP87-13-B1-EFF"
        for packet in result["semantic_queue"]
    )
    assert result["project_findings"]==0


def test_alpha8_pp87_energy_efficiency_compliance_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":9,
        "text":(
            "Для объектов, на которые распространяются требования энергетической эффективности, "
            "АР должно содержать обоснование соответствия архитектурных решений этим требованиям."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B1-EFF")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-13-B1-EFF"
        for packet in result["semantic_queue"]
    )
    assert result["project_findings"]==0


def test_alpha8_pp87_energy_efficiency_measures_list_fast_path_promotes_explicit_list():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":10,
        "text":(
            "Перечень мероприятий по соблюдению требований энергетической эффективности "
            "включает: применение теплоизоляции наружных стен; установку энергоэффективных окон."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B2-EFF-MEASURES")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["complete"] is True
    assert row["set_completeness"]["matched_count"]==1
    assert not any(
        packet["requirement_id"]=="PP87-13-B2-EFF-MEASURES"
        for packet in result["semantic_queue"]
    )
    assert result["project_findings"]==0


def test_alpha8_pp87_energy_efficiency_measures_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":10,
        "text":(
            "Для применимых объектов в АР должен быть приведён перечень мероприятий "
            "по соблюдению требований энергетической эффективности."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B2-EFF-MEASURES")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-13-B2-EFF-MEASURES"
        for packet in result["semantic_queue"]
    )
    assert result["project_findings"]==0


def test_alpha8_pp87_energy_efficiency_measures_heading_without_items_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":10,
        "text":(
            "Перечень мероприятий по соблюдению требований энергетической эффективности "
            "предусмотрен в настоящем разделе."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B2-EFF-MEASURES")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert "energy_efficiency_measures_list" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0


def test_alpha8_production_conditional_clause_passes_applicability_but_alpha9_requires_semantic_proof():
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
    assert row["applicability_reason_code"]=="PROJECT_PROFILE_PRODUCTION"
    assert row["retrieval_kind"]=="VERIFIED_OK"
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_type"]=="SET_COMPLETENESS"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"]=="NORMATIVE_SET_DETERMINISTIC_FAST_PATH_NOT_PROVEN"
    assert row["evidence_page"]==11


def test_alpha8_conditional_applicability_and_morphology_rank_real_conveyor_evidence():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №4_КР1.pdf","Тип документа":"КР"}]
    pages=[
        {
            "document":"Раздел ПД №4_КР1.pdf",
            "document_type":"КР",
            "page":40,
            "text":"В расчёте приведены расстояния 50 м и 100 м для несвязанного инженерного параметра.",
        },
        {
            "document":"Раздел ПД №4_КР1.pdf",
            "document_type":"КР",
            "page":51,
            "text":"Выходы из эстакад конвейерных и переходных мостиков над конвейерами "
                   "расположены не реже чем через 100 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1215-CONVEYOR-CROSSING-SPACING")
    assert row["applicability_reason_code"]=="PROJECT_CORPUS_CONDITION_PROVEN"
    assert row["evidence_page"]==51
    assert "переходные мостики" in row["matched_keywords"]
    assert "100 м" in row["matched_keywords"]
    assert row["proof_state"]=="STRUCTURED_PROOF_REQUIRED"
    assert row["typed_value"]["status"] in {"OWNER_NOT_PROVEN","VALUE_NOT_PROVEN"}
    assert all(candidate["page"]!=40 for candidate in row["evidence_candidates"])


def test_alpha8_gate_width_retrieval_handles_word_order_and_inflection():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ1.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ1.pdf",
        "document_type":"ПЗУ",
        "page":27,
        "text":"В ограждении в местах заезда автотранспорта устанавливаются ворота: "
               "около КПП — распашные шириной 4,5 м.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.37-ENTRANCE-GATE-WIDTH")
    assert row["applicability_reason_code"]=="PROJECT_CORPUS_CONDITION_PROVEN"
    assert row["evidence_page"]==27
    assert "ширина ворот" in row["matched_keywords"]
    assert "4,5 м" in row["matched_keywords"]
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"


def test_alpha8_numeric_only_page_is_not_normative_candidate():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №4_КР1.pdf","Тип документа":"КР"}]
    pages=[{
        "document":"Раздел ПД №4_КР1.pdf",
        "document_type":"КР",
        "page":40,
        "text":"В гидравлическом расчёте приведены радиусы 50 м и 100 м для водоотводного сооружения.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1215-CONVEYOR-CROSSING-SPACING")
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["reason_code"]=="NORMATIVE_APPLICABILITY_NOT_PROVEN"
    assert row["retrieval_candidate_count"]==0


def test_alpha8_cross_document_candidates_preserve_top3_and_add_section_diversity():
    ranked=[
        (4,1.0,900,{"document":"КР1.pdf","document_type":"КР","page":24,"text":"A"},["идентификационные признаки","уровень ответственности"]),
        (4,1.0,800,{"document":"КР1.pdf","document_type":"КР","page":25,"text":"B"},["идентификационные признаки","уровень ответственности"]),
        (4,1.0,700,{"document":"КР1.pdf","document_type":"КР","page":26,"text":"C"},["идентификационные признаки","уровень ответственности"]),
        (4,1.0,600,{"document":"КР1.pdf","document_type":"КР","page":27,"text":"D"},["идентификационные признаки","уровень ответственности"]),
        (3,0.75,500,{"document":"Задание.pdf","document_type":"Задание на проектирование","page":13,"text":"E"},["идентификационные признаки","уровень ответственности"]),
    ]
    payloads=_candidate_payloads(ranked,"X-CROSS",limit=4,minimum_distinct_sections=2)
    assert [(row["document"],row["page"]) for row in payloads[:3]] == [
        ("КР1.pdf",24),("КР1.pdf",25),("КР1.pdf",26)
    ]
    assert payloads[3]["document"]=="Задание.pdf"
    assert len({row["section"] for row in payloads})>=2

def test_alpha8_single_document_candidate_order_is_unchanged():
    contract={
        "requirement_id":"X-SINGLE",
        "check_kind":"SEMANTIC",
        "keywords":["аварийное освещение","эвакуационное освещение"],
        "evidence_contract":{"minimum_sources":1},
    }
    pages=[
        {"document":"ИОС1.pdf","document_type":"ИОС","page":24,
         "text":"Аварийное освещение. Эвакуационное освещение."},
        {"document":"ИОС1.pdf","document_type":"ИОС","page":25,
         "text":"Аварийное освещение. Эвакуационное освещение."},
        {"document":"ИОС1.pdf","document_type":"ИОС","page":26,
         "text":"Аварийное освещение. Эвакуационное освещение."},
        {"document":"АР1.pdf","document_type":"АР","page":10,
         "text":"Аварийное освещение."},
    ]
    ranked=_rank_candidates(contract,pages)
    plain=_candidate_payloads(ranked,"X-SINGLE",limit=4)
    explicit=_candidate_payloads(ranked,"X-SINGLE",limit=4,minimum_distinct_sections=1)
    assert [(x["document"],x["page"]) for x in plain] == [
        (x["document"],x["page"]) for x in explicit
    ]



def test_alpha8_near_miss_diagnostics_rank_partial_overlap_without_changing_verdict():
    contract={
        "requirement_id":"X-TEP",
        "keywords":[
            "технико-экономические показатели",
            "площадь участка",
            "коэффициент",
        ],
    }
    pages=[
        {
            "document":"ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":12,
            "text":"Площадь земельного участка составляет 12500 м2.",
        },
        {
            "document":"ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":13,
            "text":"Общие сведения о проекте без релевантных показателей.",
        },
    ]

    near=_near_miss_candidates(contract,pages)

    assert near
    assert near[0]["document"]=="ПЗУ.pdf"
    assert near[0]["page"]==12
    assert near[0]["overlap_count"] >= 1
    assert "площадь" in near[0]["matched_terms"]
    assert near[0]["fragment"]


def test_alpha8_unresolved_retrieval_row_keeps_near_miss_diagnostics():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ1.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ1.pdf",
        "document_type":"ПЗУ",
        "page":7,
        "text":"Технико-экономические показатели земельного участка приведены в таблице.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-D-TEP")

    assert row["retrieval_kind"]=="REVIEW_QUESTION"
    assert row["reason_code"] in {
        "NORMATIVE_EVIDENCE_WEAK",
        "NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
        "NORMATIVE_SEMANTIC_PROOF_REQUIRED",
        "NORMATIVE_SET_DETERMINISTIC_FAST_PATH_NOT_PROVEN",
    }
    assert row["retrieval_near_misses"]
    assert row["retrieval_near_misses"][0]["page"]==7



def test_alpha8_strong_near_miss_becomes_addressable_review_candidate():
    contract={
        "requirement_id":"X-RESP",
        "keywords":[
            "исходные данные",
            "уровень ответственности",
            "задание на проектирование",
        ],
    }
    pages=[{
        "document":"Задание.pdf",
        "document_type":"Задание на проектирование",
        "page":11,
        "text":(
            "Исходные сведения для разработки проекта. В задании заказчика определён уровень "
            "ответственности объекта; требования для проектирования приведены ниже."
        ),
    }]

    fallback=_strong_near_miss_evidence(contract,pages,"X-RESP")

    assert fallback
    assert fallback[0]["document"]=="Задание.pdf"
    assert fallback[0]["page"]==11
    assert fallback[0]["retrieval_admission"]=="STRONG_NEAR_MISS"
    assert fallback[0]["retrieval_keyword_coverage"] >= 0.70
    assert fallback[0]["fragment"]



def test_alpha8_energy_efficiency_applicability_has_addressable_trace():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":8,
        "text":"Для проектируемого здания требования энергетической эффективности применяются.",
    }]

    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B1-EFF")

    assert row["applicability_reason_code"]=="PROJECT_CORPUS_CONDITION_PROVEN"
    assert row["applicability_trace"]
    assert row["applicability_trace"][0]["document"]=="Раздел ПД №3_АР.pdf"
    assert row["applicability_trace"][0]["page"]==8


def test_alpha8_negative_energy_efficiency_text_does_not_prove_applicability():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":8,
        "text":"Требования энергетической эффективности на проектируемый объект не распространяются.",
    }]

    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B1-EFF")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["reason_code"]=="NORMATIVE_APPLICABILITY_NOT_PROVEN"
    assert row["applicability_reason_code"]=="PROJECT_CORPUS_CONDITION_NOT_PROVEN"
    assert not row["applicability_trace"]
    assert row["applicability_negative_trace"]
    assert row["applicability_negative_trace"][0]["page"]==8


def test_alpha8_surface_complex_phrase_proves_only_applicability_not_compliance():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №6_ТХ1.pdf","Тип документа":"ТХ"}]
    pages=[{
        "document":"Раздел ПД №6_ТХ1.pdf",
        "document_type":"ТХ",
        "page":15,
        "text":"Проектируемый объект относится к объектам поверхностного комплекса.",
    }]

    result=engine.run(documents,pages)
    row=next(
        x for x in result["rows"]
        if x["requirement_id"]=="FNP505-1461-SURFACE-EMERGENCY-LIGHTING"
    )

    assert row["applicability_reason_code"]=="PROJECT_CORPUS_CONDITION_PROVEN"
    assert row["applicability_trace"]
    assert row["kind"]!="VERIFIED_OK"


def test_alpha8_ios_inventory_routes_to_set_completeness_without_auto_verification():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[
        {
            "Файл":"Раздел ПД №5_подраздел ПД №1_ИОС1.pdf",
            "Тип документа":"ИОС1",
        },
        {
            "Файл":"Раздел ПД №5_подраздел ПД №2_ИОС2.pdf",
            "Тип документа":"ИОС2",
        },
    ]

    result=engine.run(documents,[])
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-CLAUSE-15-IOS")

    assert row["retrieval_kind"]=="VERIFIED_OK"
    assert row["retrieval_reason_code"]=="NORMATIVE_IOS_INVENTORY_CANDIDATE"
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_type"]=="SET_COMPLETENESS"
    assert row["proof_state"]=="SET_PROOF_CONTRACT_REQUIRED"
    assert result["set_completeness_queue_total"] >= 1
    packet=next(
        x for x in result["set_completeness_queue"]
        if x["requirement_id"]=="PP87-CLAUSE-15-IOS"
    )
    assert packet["evidence"]
    assert packet["evidence"][0]["locator_kind"]=="DOCUMENT_INVENTORY"
    assert packet["evidence"][0]["page"] is None



def test_alpha8_set_completeness_reports_missing_elements():
    contract={
        "requirement_id":"SET-X",
        "evidence_contract":{
            "set_contract":{
                "mode":"ALL_REQUIRED",
                "promotion_policy":"SEMANTIC_AFTER_COMPLETE",
                "atomization_complete":True,
                "elements":[
                    {
                        "id":"first",
                        "label":"Первый элемент",
                        "aliases":["первый обязательный элемент"],
                    },
                    {
                        "id":"second",
                        "label":"Второй элемент",
                        "aliases":["второй обязательный элемент"],
                    },
                ],
            },
        },
    }
    pages=[{
        "document":"ПЗ.pdf",
        "document_type":"ПЗ",
        "page":5,
        "text":"В проекте предусмотрен первый обязательный элемент.",
    }]

    result=_set_completeness_evaluation(contract,pages,[])

    assert result["configured"] is True
    assert result["complete"] is False
    assert result["matched_count"]==1
    assert result["total_count"]==2
    assert result["missing_ids"]==["second"]
    assert result["missing_labels"]==["Второй элемент"]


def test_alpha8_set_completeness_collects_addressable_evidence_for_every_element():
    contract={
        "requirement_id":"SET-X",
        "evidence_contract":{
            "set_contract":{
                "mode":"ALL_REQUIRED",
                "promotion_policy":"SEMANTIC_AFTER_COMPLETE",
                "atomization_complete":True,
                "elements":[
                    {"id":"first","label":"Первый элемент","aliases":["первый обязательный элемент"]},
                    {"id":"second","label":"Второй элемент","aliases":["второй обязательный элемент"]},
                ],
            },
        },
    }
    pages=[
        {
            "document":"ПЗ.pdf",
            "document_type":"ПЗ",
            "page":5,
            "text":"В проекте предусмотрен первый обязательный элемент.",
        },
        {
            "document":"ПЗ.pdf",
            "document_type":"ПЗ",
            "page":8,
            "text":"В проекте предусмотрен второй обязательный элемент.",
        },
    ]

    result=_set_completeness_evaluation(contract,pages,[])

    assert result["complete"] is True
    assert result["matched_count"]==2
    assert result["total_count"]==2
    assert {row["set_element_id"] for row in result["evidence"]}=={"first","second"}
    assert {row["page"] for row in result["evidence"]}=={5,8}


def test_alpha8_ios_inventory_set_contract_stays_hold_without_applicability_map():
    contract={
        "requirement_id":"PP87-CLAUSE-15-IOS",
        "evidence_contract":{
            "set_contract":{
                "mode":"APPLICABILITY_AWARE_INVENTORY",
                "promotion_policy":"HOLD",
                "atomization_complete":False,
            },
        },
    }
    documents=[
        {"Файл":"Раздел ПД №5_подраздел ПД №1_ИОС1.pdf","Тип документа":"ИОС1"},
        {"Файл":"Раздел ПД №5_подраздел ПД №2_ИОС2.pdf","Тип документа":"ИОС2"},
    ]

    result=_set_completeness_evaluation(contract,[],documents)

    assert result["mode"]=="APPLICABILITY_AWARE_INVENTORY"
    assert result["complete"] is False
    assert result["promotion_policy"]=="HOLD"
    assert set(result["observed_inventory"])=={"ИОС1","ИОС2"}
    assert result["missing_ids"]==["APPLICABILITY_MAP_REQUIRED"]



def test_alpha8_missing_set_element_keeps_near_miss_without_closing_element():
    contract={
        "requirement_id":"SET-FIRE",
        "evidence_contract":{
            "set_contract":{
                "mode":"ALL_REQUIRED",
                "promotion_policy":"SEMANTIC_AFTER_COMPLETE",
                "atomization_complete":True,
                "elements":[{
                    "id":"fire_suppression_points",
                    "label":"Пожаротушение на приводных станциях и перегрузочных пунктах",
                    "aliases":["автоматическое пожаротушение"],
                    "all_terms":["приводная станция","перегрузочный пункт"],
                }],
            },
        },
    }
    pages=[{
        "document":"ПБ.pdf",
        "document_type":"ПБ",
        "page":17,
        "text":"На приводной станции предусмотрено автоматическое пожаротушение.",
    }]

    result=_set_completeness_evaluation(contract,pages,[])
    element=result["elements"][0]

    assert result["complete"] is False
    assert element["matched"] is False
    assert element["near_misses"]
    near=element["near_misses"][0]
    assert near["document"]=="ПБ.pdf"
    assert near["page"]==17
    assert near["required_group_matched"]==2
    assert near["required_group_total"]==3
    assert "перегрузочный пункт" in near["missing_groups"]



def test_alpha8_conveyor_gallery_fire_contract_is_atomized_by_location():
    foundation=_foundation()
    contract=next(
        x for x in foundation.contracts()
        if x["requirement_id"]=="FNP505-1184-CONVEYOR-GALLERY-FIRE"
    )
    set_contract=dict((contract.get("evidence_contract") or {}).get("set_contract") or {})
    elements=list(set_contract.get("elements") or [])
    ids={str(x.get("id") or "") for x in elements}

    assert set_contract.get("mode")=="ALL_REQUIRED"
    assert set_contract.get("promotion_policy")=="SEMANTIC_AFTER_COMPLETE"
    assert set_contract.get("atomization_complete") is True
    assert len(elements)==9
    assert {
        "automatic_fire_suppression_drive_stations",
        "automatic_fire_suppression_transfer_points",
        "fire_alarm_drive_stations",
        "fire_alarm_transfer_points",
    }.issubset(ids)



def test_alpha8_conditional_set_element_separates_applicability_from_evidence():
    element={
        "id":"corridor_lighting",
        "label":"Эвакуационное освещение коридора",
        "applicability_aliases":["коридор"],
        "evidence_groups":[
            {"label":"Эвакуационное освещение","aliases":["эвакуационное освещение"]},
            {"label":"Коридор","aliases":["коридор"]},
        ],
    }

    pending=_set_element_match(
        element,
        [{
            "document":"ПЗ.pdf",
            "document_type":"ПЗ",
            "page":1,
            "text":"Общие сведения о проектируемом объекте.",
        }],
        "SET-COND",
    )
    assert pending["matched"] is False
    assert pending["applicability_state"]=="APPLICABILITY_PENDING"
    assert pending["evidence"]==[]
    assert pending["near_misses"]==[]

    required_missing=_set_element_match(
        element,
        [{
            "document":"АР.pdf",
            "document_type":"АР",
            "page":5,
            "text":"В здании предусмотрен коридор шириной 1,5 м.",
        }],
        "SET-COND",
    )
    assert required_missing["matched"] is False
    assert required_missing["applicability_state"]=="REQUIRED"
    assert required_missing["applicability_trace"]
    assert required_missing["applicability_trace"][0]["page"]==5

    matched=_set_element_match(
        element,
        [{
            "document":"ИОС.pdf",
            "document_type":"ИОС",
            "page":12,
            "text":"В коридоре предусмотрено эвакуационное освещение.",
        }],
        "SET-COND",
    )
    assert matched["matched"] is True
    assert matched["applicability_state"]=="REQUIRED"
    assert matched["evidence"]
    assert matched["evidence"][0]["page"]==12


def test_alpha8_sp52_set_contract_uses_conditional_element_applicability():
    foundation=_foundation()
    contract=next(
        x for x in foundation.contracts()
        if x["requirement_id"]=="SP52-7.6.3-EVACUATION-LIGHTING"
    )
    set_contract=dict((contract.get("evidence_contract") or {}).get("set_contract") or {})
    elements=list(set_contract.get("elements") or [])

    assert len(elements)==6
    assert all(element.get("applicability_aliases") for element in elements)
    assert all(element.get("evidence_groups") for element in elements)
    assert all(
        any(
            "эвакуационное освещение" in " ".join(group.get("aliases") or [])
            for group in element.get("evidence_groups") or []
        )
        for element in elements
    )



def test_alpha8_set_evidence_groups_require_local_colocation():
    element={
        "id":"stairs",
        "label":"Лестничные марши",
        "applicability_aliases":["лестница"],
        "group_window_chars":220,
        "evidence_groups":[
            {"label":"Эвакуационное освещение","aliases":["эвакуационное освещение"]},
            {"label":"Лестница/марш","aliases":["лестница","марш"]},
        ],
    }

    matched=_set_element_match(
        element,
        [{
            "document":"ИОС.pdf",
            "document_type":"ИОС",
            "page":25,
            "text":"На лестничном марше предусмотрено эвакуационное освещение.",
        }],
        "SP52",
    )
    assert matched["matched"] is True
    assert matched["evidence"]

    far_text="Лестница предусмотрена у входа. " + ("общие сведения " * 80) + "Эвакуационное освещение предусмотрено в здании."
    far=_set_element_match(
        element,
        [{
            "document":"ИОС.pdf",
            "document_type":"ИОС",
            "page":26,
            "text":far_text,
        }],
        "SP52",
    )
    assert far["matched"] is False
    assert far["applicability_state"]=="REQUIRED"
    assert far["near_misses"]
    assert "локальная связь смысловых групп" in far["near_misses"][0]["missing_groups"]



def test_alpha8_keyword_span_diagnostic_distinguishes_missing_from_distant_terms():
    missing=_keyword_span_diagnostic(
        "автоматическое пожаротушение",
        "На перегрузочном пункте предусмотрена пожарная сигнализация.",
    )
    assert missing["matched"] is False
    assert missing["reason"]=="MISSING_STEMS"
    assert missing["missing_stems"]

    distant=_keyword_span_diagnostic(
        "автоматическое пожаротушение",
        "Автоматическое управление предусмотрено. "
        + ("технологическое описание " * 40)
        + "Пожаротушение выполняется отдельной системой.",
    )
    assert distant["matched"] is False
    assert distant["reason"]=="TERMS_TOO_FAR_APART"
    assert distant["span_chars"] > 320

    local=_keyword_span_diagnostic(
        "автоматическое пожаротушение",
        "На участке предусмотрена автоматическая система пожаротушения.",
    )
    assert local["matched"] is True
    assert local["reason"]=="LOCAL_MATCH"
    assert local["span_chars"] <= 320



def test_alpha8_visual_contracts_are_explicit_for_all_seven_graphic_requirements():
    foundation=_foundation()
    ids={
        "PP87-12-M-GRAPHIC",
        "PP87-12-N-EARTHWORKS",
        "PP87-12-O-UTILITIES",
        "PP87-12-P-SITUATION",
        "PP87-13-I-FACADES",
        "PP87-13-L1-FLOOR-PLANS",
        "PP87-13-L2-SECTIONS",
    }
    contracts={
        row["requirement_id"]:row
        for row in foundation.contracts()
        if row["requirement_id"] in ids
    }

    assert set(contracts)==ids
    for row in contracts.values():
        ec=dict(row.get("evidence_contract") or {})
        visual=dict(ec.get("visual_contract") or {})
        assert ec.get("proof_type")=="GRAPHIC_CONTENT"
        assert visual.get("visual_kind")
        assert visual.get("candidate_markers")
        assert visual.get("elements")
        assert visual.get("review_policy")=="VISUAL_CONFIRMATION_REQUIRED"


def test_alpha8_visual_preflight_selects_pages_but_never_claims_graphic_proof():
    contract={
        "requirement_id":"VIS-1",
        "evidence_contract":{
            "visual_contract":{
                "visual_kind":"AR_FLOOR_PLANS",
                "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
                "candidate_markers":["план этажа","экспликация помещений"],
                "elements":[
                    {"id":"plan","label":"План этажа","aliases":["план этажа"]},
                    {"id":"schedule","label":"Экспликация помещений","aliases":["экспликация помещений"]},
                    {"id":"equipment","label":"Технологическое оборудование","aliases":["технологическое оборудование"]},
                ],
            },
        },
    }
    pages=[{
        "document":"АР.pdf",
        "document_type":"АР",
        "page":12,
        "text":"План этажа. Экспликация помещений. Технологическое оборудование.",
    }]

    result=_visual_preflight_evaluation(contract,pages)

    assert result["configured"] is True
    assert result["visual_kind"]=="AR_FLOOR_PLANS"
    assert result["ready_for_visual_review"] is True
    assert result["coverage_count"]==3
    assert result["total_count"]==3
    assert len(result["candidate_pages"])==1
    assert result["candidate_pages"][0]["document"]=="АР.pdf"
    assert result["candidate_pages"][0]["page"]==12
    assert "preflight only" in result["principle"]



def test_alpha8_ar_visual_preflight_requires_drawing_intelligence_sheet_kind():
    contract={
        "requirement_id":"VIS-AR",
        "evidence_contract":{
            "visual_contract":{
                "visual_kind":"AR_FACADES",
                "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
                "candidate_markers":["фасад"],
                "trusted_drawing_kinds":["facade"],
                "elements":[
                    {
                        "id":"facade_views",
                        "label":"Отображение фасадов",
                        "aliases":["фасад"],
                        "drawing_kinds":["facade"],
                    },
                ],
            },
        },
    }
    pages=[
        {
            "document":"АР1.pdf",
            "document_type":"АР",
            "page":5,
            "text":"Описание архитектурных решений. Фасады приняты в соответствии с заданием.",
        },
        {
            "document":"АР2.pdf",
            "document_type":"АР",
            "page":22,
            "text":"Фасад 1-8. Фасад А-Д.",
        },
    ]
    documents=[{
        "drawing_intelligence_v2":{
            "sheets":[
                {
                    "document":"АР2.pdf",
                    "page":22,
                    "designation":"RAM-01-АР2",
                    "object_name":"Производственное здание",
                    "drawing_kinds":["facade","section_view"],
                    "title_drawing_kinds":["facade"],
                    "sheet_title":"Фасад 1-8",
                    "owner_binding":"TITLE_BLOCK_EXACT",
                },
            ],
        },
    }]

    result=_visual_preflight_evaluation(contract,pages,documents)

    assert result["selection_source"]=="DRAWING_INTELLIGENCE_V2"
    assert result["coverage_count"]==1
    assert result["total_count"]==1
    assert len(result["candidate_pages"])==1
    assert result["candidate_pages"][0]["document"]=="АР2.pdf"
    assert result["candidate_pages"][0]["page"]==22
    assert result["candidate_pages"][0]["drawing_kinds"]==["facade"]
    assert result["candidate_pages"][0]["designation"]=="RAM-01-АР2"
    assert result["rejected_untrusted_pages"]
    assert result["rejected_untrusted_pages"][0]["document"]=="АР1.pdf"
    assert result["rejected_untrusted_pages"][0]["page"]==5


def test_alpha8_ar_visual_element_kind_gate_blocks_wrong_sheet_kind():
    contract={
        "requirement_id":"VIS-PLAN",
        "evidence_contract":{
            "visual_contract":{
                "visual_kind":"AR_FLOOR_PLANS",
                "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
                "candidate_markers":["план этажа","экспликация помещений"],
                "trusted_drawing_kinds":["floor_plan","room_explication"],
                "elements":[
                    {
                        "id":"plan",
                        "label":"План этажа",
                        "aliases":["план этажа"],
                        "drawing_kinds":["floor_plan"],
                    },
                    {
                        "id":"schedule",
                        "label":"Экспликация помещений",
                        "aliases":["экспликация помещений"],
                        "drawing_kinds":["room_explication"],
                    },
                ],
            },
        },
    }
    pages=[
        {
            "document":"АР2.pdf",
            "document_type":"АР",
            "page":10,
            "text":"План этажа. Экспликация помещений.",
        },
        {
            "document":"АР2.pdf",
            "document_type":"АР",
            "page":11,
            "text":"Экспликация помещений.",
        },
    ]
    documents=[{
        "drawing_intelligence_v2":{
            "sheets":[
                {
                    "document":"АР2.pdf",
                    "page":10,
                    "drawing_kinds":["floor_plan"],
                    "title_drawing_kinds":["floor_plan"],
                    "sheet_title":"План 1 этажа",
                },
                {
                    "document":"АР2.pdf",
                    "page":11,
                    "drawing_kinds":["room_explication"],
                    "title_drawing_kinds":[],
                    "sheet_title":"",
                },
            ],
            "room_schedules":[
                {
                    "document":"АР2.pdf",
                    "page":11,
                    "designation":"RAM-01-АР2",
                    "position":"1.1",
                    "parent_object":"Производственное здание",
                    "owner_binding":"TITLE_BLOCK_EXACT",
                },
            ],
        },
    }]

    result=_visual_preflight_evaluation(contract,pages,documents)
    by_id={row["id"]:row for row in result["elements"]}

    assert by_id["plan"]["candidate_locations"][0]["page"]==10
    assert by_id["schedule"]["candidate_locations"][0]["page"]==11



def test_alpha8_broad_page_kind_does_not_qualify_without_title_kind():
    contract={
        "requirement_id":"VIS-FACADE-STRICT",
        "evidence_contract":{
            "visual_contract":{
                "visual_kind":"AR_FACADES",
                "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
                "candidate_markers":["фасад"],
                "trusted_drawing_kinds":["facade"],
                "elements":[
                    {
                        "id":"facade_views",
                        "label":"Фасады",
                        "aliases":["фасад"],
                        "drawing_kinds":["facade"],
                    },
                ],
            },
        },
    }
    pages=[{
        "document":"АР1.pdf",
        "document_type":"АР",
        "page":5,
        "text":"В пояснительном тексте рассмотрены фасады здания.",
    }]
    documents=[{
        "drawing_intelligence_v2":{
            "sheets":[{
                "document":"АР1.pdf",
                "page":5,
                "designation":"RAM-01-АР1",
                "drawing_kinds":["facade"],
                "title_drawing_kinds":[],
                "sheet_title":"",
            }],
        },
    }]

    result=_visual_preflight_evaluation(contract,pages,documents)

    assert result["coverage_count"]==0
    assert result["candidate_pages"]==[]
    assert result["rejected_untrusted_pages"]
    assert result["rejected_untrusted_pages"][0]["broad_drawing_kinds"]==["facade"]



def test_alpha8_pzu_visual_kind_rejects_drawing_index_page():
    assert _general_plan_visual_kinds_from_text(
        "Ведомость графической части. Лист 3 План земляных масс. Лист 4 Ситуационный план."
    ) == []
    assert _general_plan_visual_kinds_from_text(
        "План земляных масс. Схема организации рельефа. Масштаб 1:1000."
    ) == ["relief_earthworks"]


def test_alpha8_pzu_visual_preflight_rejects_drawing_index_page():
    contract={
        "requirement_id":"VIS-PZU",
        "evidence_contract":{
            "visual_contract":{
                "visual_kind":"PZU_RELIEF_EARTHWORKS",
                "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
                "candidate_markers":["план земляных масс","схема организации рельефа"],
                "trusted_general_plan_kinds":["relief_earthworks"],
                "elements":[
                    {
                        "id":"earth",
                        "label":"План земляных масс",
                        "aliases":["план земляных масс"],
                    },
                ],
            },
        },
    }
    pages=[
        {
            "document":"ПЗУ2.pdf",
            "document_type":"ПЗУ2",
            "page":3,
            "text":"Ведомость графической части. Лист 3 План земляных масс.",
        },
        {
            "document":"ПЗУ2.pdf",
            "document_type":"ПЗУ2",
            "page":12,
            "text":"План земляных масс. Схема организации рельефа. Масштаб 1:1000.",
        },
    ]

    result=_visual_preflight_evaluation(contract,pages,[{}])

    assert result["selection_source"]=="PZU_STRUCTURAL_PREFLIGHT"
    assert result["coverage_count"]==1
    assert len(result["candidate_pages"])==1
    assert result["candidate_pages"][0]["page"]==12
    assert result["candidate_pages"][0]["drawing_kinds"]==["relief_earthworks"]
    assert result["rejected_untrusted_pages"]
    assert result["rejected_untrusted_pages"][0]["page"]==3


def test_alpha8_pzu_visual_preflight_prefers_general_plan_engine_audit():
    contract={
        "requirement_id":"VIS-PZU-SITUATION",
        "evidence_contract":{
            "visual_contract":{
                "visual_kind":"PZU_SITUATION_PLAN",
                "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
                "candidate_markers":["ситуационный план"],
                "trusted_general_plan_kinds":["situation_plan"],
                "elements":[
                    {
                        "id":"situation",
                        "label":"Ситуационный план",
                        "aliases":["ситуационный план"],
                    },
                ],
            },
        },
    }
    pages=[{
        "document":"ПЗУ2.pdf",
        "document_type":"ПЗУ2",
        "page":4,
        "text":"Ситуационный план. Условные обозначения.",
    }]
    documents=[{
        "general_plan_audit":[{
            "document":"ПЗУ2.pdf",
            "page":4,
            "decision":"visual_sheet_audit",
            "general_plan_page":True,
            "visual_kinds":["situation_plan"],
            "position_count":3,
            "has_explication":False,
        }],
    }]

    result=_visual_preflight_evaluation(contract,pages,documents)

    assert result["selection_source"]=="GENERAL_PLAN_ENGINE"
    assert result["candidate_pages"][0]["selection_source"]=="GENERAL_PLAN_ENGINE"
    assert result["candidate_pages"][0]["drawing_kinds"]==["situation_plan"]



def test_alpha8_visual_preflight_separates_structural_and_visual_elements():
    contract={
        "requirement_id":"VIS-AR-PLAN-PROOF",
        "evidence_contract":{
            "visual_contract":{
                "visual_kind":"AR_FLOOR_PLANS",
                "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
                "candidate_markers":["план этажа","экспликация помещений"],
                "trusted_drawing_kinds":["floor_plan","room_explication"],
                "elements":[
                    {
                        "id":"plan",
                        "label":"Поэтажный план",
                        "aliases":["план этажа"],
                        "drawing_kinds":["floor_plan"],
                        "verification_mode":"SHEET_PRESENCE",
                    },
                    {
                        "id":"schedule",
                        "label":"Экспликация помещений",
                        "aliases":["экспликация помещений"],
                        "drawing_kinds":["room_explication"],
                        "verification_mode":"SHEET_PRESENCE",
                    },
                    {
                        "id":"equipment",
                        "label":"Размещение технологического оборудования",
                        "aliases":["технологическое оборудование"],
                        "drawing_kinds":["floor_plan"],
                        "verification_mode":"VISUAL_CONTENT",
                    },
                ],
            },
        },
    }
    pages=[
        {
            "document":"АР2.pdf",
            "document_type":"АР",
            "page":10,
            "text":"План этажа. Технологическое оборудование.",
        },
        {
            "document":"АР2.pdf",
            "document_type":"АР",
            "page":11,
            "text":"Экспликация помещений.",
        },
    ]
    documents=[{
        "drawing_intelligence_v2":{
            "sheets":[
                {
                    "document":"АР2.pdf",
                    "page":10,
                    "designation":"RAM-АР2-10",
                    "drawing_kinds":["floor_plan"],
                    "title_drawing_kinds":["floor_plan"],
                    "sheet_title":"План этажа",
                },
                {
                    "document":"АР2.pdf",
                    "page":11,
                    "designation":"RAM-АР2-11",
                    "drawing_kinds":["room_explication"],
                    "title_drawing_kinds":[],
                    "sheet_title":"",
                },
            ],
            "room_schedules":[{
                "document":"АР2.pdf",
                "page":11,
                "designation":"RAM-АР2-11",
                "parent_object":"Здание",
                "owner_binding":"TITLE_BLOCK_EXACT",
            }],
        },
    }]

    result=_visual_preflight_evaluation(contract,pages,documents)
    by_id={row["id"]:row for row in result["elements"]}

    assert by_id["plan"]["structural_confirmed"] is True
    assert by_id["schedule"]["structural_confirmed"] is True
    assert by_id["equipment"]["structural_confirmed"] is False
    assert by_id["equipment"]["proof_status"]=="VISUAL_REVIEW_REQUIRED"
    assert result["structural_target_count"]==2
    assert result["structural_confirmed_count"]==2
    assert result["structural_review_required_count"]==0
    assert result["visual_review_required_count"]==1
    assert result["structural_proof_complete"] is False
    assert result["remaining_visual_labels"]==["Размещение технологического оборудования"]


def test_alpha8_pzu_fallback_cannot_create_structural_proof():
    contract={
        "requirement_id":"VIS-PZU-STRUCTURAL",
        "evidence_contract":{
            "visual_contract":{
                "visual_kind":"PZU_RELIEF_EARTHWORKS",
                "review_policy":"VISUAL_CONFIRMATION_REQUIRED",
                "candidate_markers":["план земляных масс"],
                "trusted_general_plan_kinds":["relief_earthworks"],
                "elements":[{
                    "id":"earth",
                    "label":"План земляных масс",
                    "aliases":["план земляных масс"],
                    "verification_mode":"SHEET_PRESENCE",
                }],
            },
        },
    }
    pages=[{
        "document":"ПЗУ2.pdf",
        "document_type":"ПЗУ2",
        "page":12,
        "text":"План земляных масс. Масштаб 1:1000.",
    }]

    fallback=_visual_preflight_evaluation(contract,pages,[{}])
    assert fallback["selection_source"]=="PZU_STRUCTURAL_PREFLIGHT"
    assert fallback["structural_target_count"]==1
    assert fallback["structural_confirmed_count"]==0
    assert fallback["structural_review_required_count"]==1
    assert fallback["visual_review_required_count"]==0
    assert fallback["elements"][0]["proof_status"]=="STRUCTURAL_REINDEX_REQUIRED"
    assert fallback["structural_proof_complete"] is False

    trusted=_visual_preflight_evaluation(
        contract,
        pages,
        [{
            "general_plan_audit":[{
                "document":"ПЗУ2.pdf",
                "page":12,
                "decision":"visual_sheet_audit",
                "general_plan_page":True,
                "visual_kinds":["relief_earthworks"],
                "position_count":0,
                "has_explication":False,
            }],
        }],
    )
    assert trusted["selection_source"]=="GENERAL_PLAN_ENGINE"
    assert trusted["structural_target_count"]==1
    assert trusted["structural_confirmed_count"]==1
    assert trusted["structural_review_required_count"]==0
    assert trusted["visual_review_required_count"]==0
    assert trusted["structural_proof_complete"] is True



def _owner_model_document(*rows):
    objects={}
    for object_id,document,page in rows:
        obj=objects.setdefault(object_id,{
            "object_id":object_id,
            "name":object_id,
            "properties":{"TEST":[]},
        })
        obj["properties"]["TEST"].append({
            "document":document,
            "page":page,
            "section":"ПЗ",
            "fact_admission_decision":"ADMIT",
        })
    return {"project_understanding":{"objects":list(objects.values())}}


def _owner_scoped_set_contract():
    return {
        "requirement_id":"OWNER-SET-TEST",
        "evidence_contract":{
            "set_contract":{
                "mode":"ALL_REQUIRED",
                "promotion_policy":"DETERMINISTIC_AFTER_COMPLETE",
                "atomization_complete":True,
                "owner_scope":"SAME_CONFIRMED_OBJECT",
                "elements":[
                    {
                        "id":"first",
                        "label":"Первый признак",
                        "aliases":["первый признак"],
                    },
                    {
                        "id":"second",
                        "label":"Второй признак",
                        "aliases":["второй признак"],
                    },
                ],
            }
        },
    }


def test_alpha8_owner_scoped_set_cannot_merge_two_project_objects():
    pages=[
        {"document":"ПЗ.pdf","document_type":"ПЗ","page":10,"text":"Первый признак подтвержден."},
        {"document":"ПЗ.pdf","document_type":"ПЗ","page":20,"text":"Второй признак подтвержден."},
    ]
    documents=[_owner_model_document(
        ("OBJ-A","ПЗ.pdf",10),
        ("OBJ-B","ПЗ.pdf",20),
    )]

    result=_set_completeness_evaluation(_owner_scoped_set_contract(),pages,documents)

    assert result["complete"] is False
    assert result["owner_scope"]=="SAME_CONFIRMED_OBJECT"
    assert result["owner_scope_state"]=="OWNER_NOT_PROVEN"
    assert result["owner_object_id"]==""
    assert result["evidence"]


def test_alpha8_owner_scoped_set_confirms_one_project_object_only():
    pages=[
        {"document":"ПЗ.pdf","document_type":"ПЗ","page":10,"text":"Первый признак подтвержден."},
        {"document":"ПЗ.pdf","document_type":"ПЗ","page":11,"text":"Второй признак подтвержден."},
    ]
    documents=[_owner_model_document(
        ("OBJ-A","ПЗ.pdf",10),
        ("OBJ-A","ПЗ.pdf",11),
    )]

    result=_set_completeness_evaluation(_owner_scoped_set_contract(),pages,documents)

    assert result["complete"] is True
    assert result["owner_scope_state"]=="CONFIRMED"
    assert result["owner_object_id"]=="OBJ-A"
    assert {row["object_id"] for row in result["evidence"]}=={"OBJ-A"}
    assert {row["set_element_id"] for row in result["evidence"]}=={"first","second"}


def test_alpha8_owner_scoped_set_holds_when_page_owner_is_ambiguous():
    pages=[
        {"document":"ПЗ.pdf","document_type":"ПЗ","page":10,"text":"Первый признак подтвержден. Второй признак подтвержден."},
    ]
    documents=[_owner_model_document(
        ("OBJ-A","ПЗ.pdf",10),
        ("OBJ-B","ПЗ.pdf",10),
    )]

    result=_set_completeness_evaluation(_owner_scoped_set_contract(),pages,documents)

    assert result["complete"] is False
    assert result["owner_scope_state"]=="AMBIGUOUS_OWNER"
    assert result["owner_object_id"]==""



def test_alpha8_fz123_category_basis_owner_scoped_set_can_close_without_ai():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contract={
        row["requirement_id"]:row for row in foundation.contracts()
    }["FZ123-27-3-CATEGORY-BASIS"]

    assert contract["evidence_contract"]["proof_type"]=="SET_COMPLETENESS"
    set_contract=contract["evidence_contract"]["set_contract"]
    assert set_contract["promotion_policy"]=="DETERMINISTIC_AFTER_COMPLETE"
    assert set_contract["owner_scope"]=="SAME_CONFIRMED_OBJECT"

    pages=[
        {
            "document":"ТХ.pdf","document_type":"ТХ","page":10,
            "text":"В обращении находятся горючие вещества. Масса горючих веществ 125 кг.",
        },
        {
            "document":"ТХ.pdf","document_type":"ТХ","page":11,
            "text":"Для веществ приведены пожароопасные свойства и показатели пожарной опасности.",
        },
        {
            "document":"АР.pdf","document_type":"АР","page":12,
            "text":"Объёмно-планировочные решения производственного помещения приведены в разделе.",
        },
        {
            "document":"ТХ.pdf","document_type":"ТХ","page":13,
            "text":"Характеристики технологического процесса приняты для расчёта категории помещения.",
        },
    ]
    documents=[_owner_model_document(
        ("OBJ-A","ТХ.pdf",10),
        ("OBJ-A","ТХ.pdf",11),
        ("OBJ-A","АР.pdf",12),
        ("OBJ-A","ТХ.pdf",13),
    )]

    result=_set_completeness_evaluation(contract,pages,documents)

    assert result["complete"] is True
    assert result["owner_scope_state"]=="CONFIRMED"
    assert result["owner_object_id"]=="OBJ-A"
    assert result["matched_count"]==4
    assert {row["set_element_id"] for row in result["evidence"]}=={
        "substance_quantity","fire_hazard_properties","space_planning","process_characteristics"
    }


def test_alpha8_fz123_category_basis_does_not_merge_different_objects():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contract={
        row["requirement_id"]:row for row in foundation.contracts()
    }["FZ123-27-3-CATEGORY-BASIS"]

    pages=[
        {
            "document":"ТХ.pdf","document_type":"ТХ","page":10,
            "text":"В обращении находятся горючие вещества. Масса горючих веществ 125 кг. "
                   "Для веществ приведены пожароопасные свойства.",
        },
        {
            "document":"АР.pdf","document_type":"АР","page":12,
            "text":"Объёмно-планировочные решения производственного помещения приведены в разделе.",
        },
        {
            "document":"ТХ.pdf","document_type":"ТХ","page":13,
            "text":"Характеристики технологического процесса приняты для расчёта категории помещения.",
        },
    ]
    documents=[_owner_model_document(
        ("OBJ-A","ТХ.pdf",10),
        ("OBJ-B","АР.pdf",12),
        ("OBJ-B","ТХ.pdf",13),
    )]

    result=_set_completeness_evaluation(contract,pages,documents)

    assert result["complete"] is False
    assert result["owner_scope_state"]=="OWNER_NOT_PROVEN"
    assert result["owner_object_id"]==""



def test_alpha8_sp12_category_inputs_reuse_owner_scoped_deterministic_set():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}
    contract=contracts["SP12-4.2-CATEGORY-INPUTS"]

    assert contract["evidence_contract"]["proof_type"]=="SET_COMPLETENESS"
    set_contract=contract["evidence_contract"]["set_contract"]
    assert set_contract["promotion_policy"]=="DETERMINISTIC_AFTER_COMPLETE"
    assert set_contract["owner_scope"]=="SAME_CONFIRMED_OBJECT"

    pages=[
        {
            "document":"ТХ.pdf","document_type":"ТХ","page":20,
            "text":"В помещении обращаются горючие материалы. Количество материалов 80 кг.",
        },
        {
            "document":"ТХ.pdf","document_type":"ТХ","page":21,
            "text":"Приведены пожароопасные свойства обращающихся материалов.",
        },
        {
            "document":"АР.pdf","document_type":"АР","page":22,
            "text":"Объемно-планировочные решения помещения приведены на планах и в пояснениях.",
        },
        {
            "document":"ТХ.pdf","document_type":"ТХ","page":23,
            "text":"Особенности технологического процесса учтены при определении категории.",
        },
    ]
    documents=[_owner_model_document(
        ("OBJ-CAT","ТХ.pdf",20),
        ("OBJ-CAT","ТХ.pdf",21),
        ("OBJ-CAT","АР.pdf",22),
        ("OBJ-CAT","ТХ.pdf",23),
    )]

    result=_set_completeness_evaluation(contract,pages,documents)

    assert result["complete"] is True
    assert result["owner_scope_state"]=="CONFIRMED"
    assert result["owner_object_id"]=="OBJ-CAT"
    assert result["matched_count"]==4


def test_alpha8_pp87_zouit_disclosure_is_addressable_presence_even_when_absent():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":6,
        "text":"Зоны с особыми условиями использования территорий (ЗОУИТ) "
               "в границах земельного участка отсутствуют.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-A1-ZOUIT")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="ADDRESSABLE_PRESENCE_PROOF"
    assert row["evidence_document"]=="Раздел ПД №2_ПЗУ.pdf"
    assert row["evidence_page"]==6


def test_alpha8_pp87_zouit_presence_does_not_infer_disclosure_from_land_plot_words_only():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":6,
        "text":"Границы земельного участка показаны на схеме планировочной организации.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-A1-ZOUIT")
    assert row["kind"]!="VERIFIED_OK"


def _typed_owner_document(*rows):
    document=_owner_model_document(*rows)
    document["Файл"]="Раздел ПД №2_ПЗУ.pdf"
    document["Тип документа"]="ПЗУ"
    return document


def test_alpha8_gate_width_relative_minimum_fast_path_promotes_auto_only_owner():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",27),
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",28),
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",29),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":27,
            "text":(
                "В местах заезда автотранспорта предусмотрены ворота. "
                "Железнодорожный въезд не предусмотрен."
            ),
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":28,
            "text":"Ширина наиболее габаритного применяемого автомобиля составляет 3,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":29,
            "text":"Ширина ворот автомобильного въезда принята 4,5 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.37-ENTRANCE-GATE-WIDTH")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_TYPED_VALUE_PROOF"
    assert row["typed_value"]["kind"]=="OWNER_BOUND_RELATIVE_MINIMUM"
    assert row["typed_value"]["owner_object_id"]=="OBJ-SITE"
    assert row["typed_value"]["reference_value"]==3.0
    assert row["typed_value"]["measured_value"]==4.5
    assert row["typed_value"]["required_minimum"]==4.5
    assert row["typed_value"]["guard_categories"]==["AUTO_ONLY"]
    assert not any(
        packet["requirement_id"]=="SP18-5.37-ENTRANCE-GATE-WIDTH"
        for packet in result["semantic_queue"]
    )
    assert result["project_findings"]==0


def test_alpha8_gate_width_relative_minimum_below_formula_falls_back_to_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",27),
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",28),
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",29),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":27,
            "text":(
                "В местах заезда автотранспорта предусмотрены ворота. "
                "Железнодорожные въезды отсутствуют."
            ),
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":28,
            "text":"Ширина наиболее габаритного автомобиля составляет 3,2 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":29,
            "text":"Ширина ворот автомобильного въезда принята 4,6 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.37-ENTRANCE-GATE-WIDTH")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"]=="NORMATIVE_TYPED_DETERMINISTIC_FAST_PATH_NOT_PROVEN"
    assert row["typed_value"]["status"]=="BELOW_MINIMUM"
    assert row["typed_value"]["required_minimum"]==4.7
    assert any(
        packet["requirement_id"]=="SP18-5.37-ENTRANCE-GATE-WIDTH"
        for packet in result["semantic_queue"]
    )
    assert result["project_findings"]==0


def test_alpha8_gate_width_relative_minimum_requires_explicit_no_rail_guard():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",27),
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",28),
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",29),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":27,
            "text":"В местах заезда автотранспорта предусмотрены ворота.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":28,
            "text":"Ширина наиболее габаритного автомобиля составляет 3,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":29,
            "text":"Ширина ворот автомобильного въезда принята 5,0 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.37-ENTRANCE-GATE-WIDTH")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["typed_value"]["complete"] is False
    assert row["typed_value"]["owner_results"][0]["status"]=="GUARD_NOT_PROVEN"
    assert any(
        packet["requirement_id"]=="SP18-5.37-ENTRANCE-GATE-WIDTH"
        for packet in result["semantic_queue"]
    )
    assert result["project_findings"]==0


def test_alpha8_gate_width_copied_normative_formula_never_promotes():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-SITE","Раздел ПД №2_ПЗУ.pdf",27),
    )]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":27,
        "text":(
            "В местах заезда автотранспорта предусмотрены ворота. "
            "Ширина ворот автомобильного въезда должна быть не менее ширины наиболее "
            "габаритного автомобиля плюс 1,5 м и не менее 3,5 м; "
            "для железнодорожного въезда — не менее 4,5 м."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.37-ENTRANCE-GATE-WIDTH")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["typed_value"]["complete"] is False
    assert result["project_findings"]==0


def test_alpha8_fire_road_width_typed_threshold_promotes_same_owner_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-FIRE","Раздел ПД №2_ПЗУ.pdf",10),
        ("OBJ-FIRE","Раздел ПД №2_ПЗУ.pdf",11),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":10,
            "text":"Высота здания составляет 12,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":11,
            "text":"Ширина пожарного проезда принята 3,8 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.3-FIRE-ROAD-WIDTH")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_TYPED_VALUE_PROOF"
    assert row["typed_value"]["owner_object_id"]=="OBJ-FIRE"
    assert row["typed_value"]["selector_value"]==12.0
    assert row["typed_value"]["measured_value"]==3.8
    assert row["typed_value"]["required_minimum"]==3.5


def test_alpha8_fire_road_width_typed_threshold_rejects_copied_normative_limits():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-FIRE","Раздел ПД №2_ПЗУ.pdf",10),
    )]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":10,
        "text":"Минимальная ширина пожарного проезда должна быть не менее 3,5 м "
               "при высоте до 13 м включительно.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.3-FIRE-ROAD-WIDTH")
    assert row["kind"]!="VERIFIED_OK"
    assert row["proof_state"]=="STRUCTURED_PROOF_REQUIRED"


def test_alpha8_fire_road_width_below_minimum_stays_review_not_project_finding():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-FIRE","Раздел ПД №2_ПЗУ.pdf",10),
        ("OBJ-FIRE","Раздел ПД №2_ПЗУ.pdf",11),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":10,
            "text":"Высота здания составляет 20,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":11,
            "text":"Ширина пожарного проезда принята 4,0 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.3-FIRE-ROAD-WIDTH")
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="STRUCTURED_PROOF_REQUIRED"
    assert row["reason_code"]=="NORMATIVE_TYPED_VALUE_BELOW_MINIMUM_REVIEW"
    assert row["typed_value"]["required_minimum"]==4.2
    assert result["project_findings"]==0


def test_alpha8_fire_road_width_typed_threshold_cannot_merge_two_owners():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-A","Раздел ПД №2_ПЗУ.pdf",10),
        ("OBJ-B","Раздел ПД №2_ПЗУ.pdf",11),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":10,
            "text":"Высота здания составляет 12,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":11,
            "text":"Ширина пожарного проезда принята 4,0 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.3-FIRE-ROAD-WIDTH")
    assert row["kind"]!="VERIFIED_OK"
    assert row["proof_state"]=="STRUCTURED_PROOF_REQUIRED"
    assert row["typed_value"]["owner_object_id"]==""


def test_alpha8_fire_road_width_typed_threshold_binds_nearest_post_label_values_on_same_page():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-FIRE","Раздел ПД №2_ПЗУ.pdf",10),
    )]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":10,
        "text":"Высота здания составляет 12,0 м. "
               "Ширина пожарного проезда принята 3,8 м.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.3-FIRE-ROAD-WIDTH")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_TYPED_VALUE_PROOF"
    assert row["typed_value"]["selector_value"]==12.0
    assert row["typed_value"]["measured_value"]==3.8


def test_alpha8_fire_road_wall_distance_range_promotes_middle_height_band():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",20),
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",21),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":20,
            "text":"Высота здания составляет 20,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":21,
            "text":"Расстояние от края пожарного проезда до стены здания принято 6,5 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.6-ROAD-WALL-DISTANCE")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_TYPED_VALUE_PROOF"
    assert row["typed_value"]["owner_object_id"]=="OBJ-WALL"
    assert row["typed_value"]["required_minimum"]==5.0
    assert row["typed_value"]["required_maximum"]==8.0
    assert row["typed_value"]["measured_minimum"]==6.5
    assert row["typed_value"]["measured_maximum"]==6.5


def test_alpha8_fire_road_wall_distance_supports_upper_bound_only_low_height_band():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",20),
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",21),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":20,
            "text":"Высота сооружения составляет 10,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":21,
            "text":"Расстояние от пожарного проезда до стены принято 24,0 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.6-ROAD-WALL-DISTANCE")
    assert row["kind"]=="VERIFIED_OK"
    assert row["typed_value"]["required_minimum"] is None
    assert row["typed_value"]["required_maximum"]==25.0


def test_alpha8_fire_road_wall_distance_outside_range_stays_review():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",20),
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",21),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":20,
            "text":"Высота здания составляет 20,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":21,
            "text":"Расстояние от края пожарного проезда до стены здания принято 9,0 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.6-ROAD-WALL-DISTANCE")
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["reason_code"]=="NORMATIVE_TYPED_VALUE_OUTSIDE_RANGE_REVIEW"
    assert result["project_findings"]==0


def test_alpha8_fire_road_wall_distance_all_observed_values_must_fit_range():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",20),
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",21),
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",22),
    )]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":20,
            "text":"Высота здания составляет 20,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":21,
            "text":"Расстояние от края пожарного проезда до стены здания принято 6,0 м.",
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":22,
            "text":"Расстояние от края пожарного проезда до стены здания принято 9,0 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.6-ROAD-WALL-DISTANCE")
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["typed_value"]["measured_minimum"]==6.0
    assert row["typed_value"]["measured_maximum"]==9.0
    assert row["reason_code"]=="NORMATIVE_TYPED_VALUE_OUTSIDE_RANGE_REVIEW"


def test_alpha8_fire_road_wall_distance_copied_normative_range_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_owner_document(
        ("OBJ-WALL","Раздел ПД №2_ПЗУ.pdf",20),
    )]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":20,
        "text":"При высоте свыше 12 до 28 м расстояние от края пожарного проезда "
               "до стен здания должно составлять 5–8 м.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.6-ROAD-WALL-DISTANCE")
    assert row["kind"]!="VERIFIED_OK"


def _typed_conveyor_document(*rows):
    document=_owner_model_document(*rows)
    document["Файл"]="Раздел ПД №6_ТХ.pdf"
    document["Тип документа"]="ТХ"
    return document


def test_alpha8_conveyor_crossing_spacing_indoor_promotes_50m_limit():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_conveyor_document(
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",30),
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",31),
    )]
    pages=[
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":30,
            "text":"Конвейер расположен в здании дробильного корпуса.",
        },
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":31,
            "text":"Интервал между переходными мостиками принят 45 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1215-CONVEYOR-CROSSING-SPACING")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_TYPED_VALUE_PROOF"
    assert row["typed_value"]["selector_category"]=="INDOOR_OR_UNDERGROUND"
    assert row["typed_value"]["required_maximum"]==50.0
    assert row["typed_value"]["measured_maximum"]==45.0


def test_alpha8_conveyor_crossing_spacing_outdoor_promotes_100m_limit():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_conveyor_document(
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",30),
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",31),
    )]
    pages=[
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":30,
            "text":"Наружный конвейер размещен на открытой площадке.",
        },
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":31,
            "text":"Расстояние между переходными мостиками принято 80 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1215-CONVEYOR-CROSSING-SPACING")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_TYPED_VALUE_PROOF"
    assert row["typed_value"]["selector_category"]=="OUTDOOR"
    assert row["typed_value"]["required_maximum"]==100.0
    assert row["typed_value"]["measured_maximum"]==80.0


def test_alpha8_conveyor_crossing_spacing_above_limit_stays_review():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_conveyor_document(
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",30),
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",31),
    )]
    pages=[
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":30,
            "text":"Конвейер расположен внутри здания.",
        },
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":31,
            "text":"Шаг переходных мостиков принят 60 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1215-CONVEYOR-CROSSING-SPACING")
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["reason_code"]=="NORMATIVE_TYPED_VALUE_OUTSIDE_RANGE_REVIEW"
    assert row["typed_value"]["status"]=="ABOVE_MAXIMUM"
    assert result["project_findings"]==0


def test_alpha8_conveyor_crossing_spacing_needs_explicit_location_category():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_conveyor_document(
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",30),
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",31),
    )]
    pages=[
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":30,
            "text":"Предусмотрен ленточный конвейер.",
        },
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":31,
            "text":"Интервал между переходными мостиками принят 40 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1215-CONVEYOR-CROSSING-SPACING")
    assert row["kind"]!="VERIFIED_OK"
    assert row["proof_state"]=="STRUCTURED_PROOF_REQUIRED"
    assert row["typed_value"]["owner_object_id"]==""


def test_alpha8_conveyor_crossing_spacing_category_conflict_stays_unproven():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_conveyor_document(
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",30),
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",31),
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",32),
    )]
    pages=[
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":30,
            "text":"Конвейер расположен в здании.",
        },
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":31,
            "text":"Наружный конвейер также размещен на открытой площадке.",
        },
        {
            "document":"Раздел ПД №6_ТХ.pdf",
            "document_type":"ТХ",
            "page":32,
            "text":"Интервал между переходными мостиками принят 45 м.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1215-CONVEYOR-CROSSING-SPACING")
    assert row["kind"]!="VERIFIED_OK"
    assert row["proof_state"]=="STRUCTURED_PROOF_REQUIRED"


def test_alpha8_conveyor_crossing_spacing_copied_fnp_limits_do_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_typed_conveyor_document(
        ("OBJ-CONV","Раздел ПД №6_ТХ.pdf",30),
    )]
    pages=[{
        "document":"Раздел ПД №6_ТХ.pdf",
        "document_type":"ТХ",
        "page":30,
        "text":"Переходные мостики через конвейер должны размещаться с интервалом "
               "не более 50 м в зданиях и подземных камерах и не более 100 м в остальных случаях.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1215-CONVEYOR-CROSSING-SPACING")
    assert row["kind"]!="VERIFIED_OK"


def _id_features_document(*rows):
    document=_owner_model_document(*rows)
    document["Файл"]="Раздел ПД №1_ПЗ.pdf"
    document["Тип документа"]="ПЗ"
    return document


def _complete_id_features_text():
    return (
        "Идентификационные признаки здания или сооружения. "
        "Назначение объекта: производственное. "
        "Функционально-технологические особенности: дробление и транспортирование руды. "
        "Опасные природные процессы и техногенные воздействия: отсутствуют. "
        "Объект не относится к опасным производственным объектам. "
        "Пожарная и взрывопожарная опасность: категория В1. "
        "Постоянное пребывание людей: не предусмотрено. "
        "Уровень ответственности: нормальный."
    )


def test_alpha8_fz384_id_features_complete_same_owner_promotes_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_id_features_document(
        ("OBJ-ID","Раздел ПД №1_ПЗ.pdf",10),
    )]
    pages=[{
        "document":"Раздел ПД №1_ПЗ.pdf",
        "document_type":"ПЗ",
        "page":10,
        "text":_complete_id_features_text(),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FZ384-4-1-ID-FEATURES")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["owner_scope_state"]=="CONFIRMED"
    assert row["set_completeness"]["owner_object_id"]=="OBJ-ID"
    assert row["set_completeness"]["matched_count"]==7
    assert row["set_completeness"]["total_count"]==7


def test_alpha8_fz384_id_features_copied_statutory_list_is_not_project_evidence():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_id_features_document(
        ("OBJ-ID","Раздел ПД №1_ПЗ.pdf",10),
    )]
    pages=[{
        "document":"Раздел ПД №1_ПЗ.pdf",
        "document_type":"ПЗ",
        "page":10,
        "text":(
            "В соответствии со статьей 4 к идентификационным признакам относятся: "
            "назначение, функционально-технологические особенности, опасные природные "
            "и техногенные воздействия, принадлежность к ОПО, пожарная и взрывопожарная "
            "опасность, постоянное пребывание людей и уровень ответственности."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FZ384-4-1-ID-FEATURES")
    assert row["kind"]!="VERIFIED_OK"
    assert row["proof_state"]=="SET_PROOF_CONTRACT_REQUIRED"
    assert row["set_completeness"]["complete"] is False


def test_alpha8_fz384_id_features_missing_one_feature_stays_review():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_id_features_document(
        ("OBJ-ID","Раздел ПД №1_ПЗ.pdf",10),
    )]
    text=_complete_id_features_text().replace(
        "Функционально-технологические особенности: дробление и транспортирование руды. ",
        "",
    )
    pages=[{
        "document":"Раздел ПД №1_ПЗ.pdf",
        "document_type":"ПЗ",
        "page":10,
        "text":text,
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FZ384-4-1-ID-FEATURES")
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SET_PROOF_CONTRACT_REQUIRED"
    assert "functional_technology" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0


def test_alpha8_fz384_id_features_cannot_merge_two_objects():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}
    contract=contracts["FZ384-4-1-ID-FEATURES"]
    pages=[
        {
            "document":"Раздел ПД №1_ПЗ.pdf",
            "document_type":"ПЗ",
            "page":10,
            "text":(
                "Назначение объекта: производственное. "
                "Функционально-технологические особенности: дробление руды. "
                "Опасные природные процессы и техногенные воздействия: отсутствуют. "
                "Объект не относится к опасным производственным объектам."
            ),
        },
        {
            "document":"Раздел ПД №1_ПЗ.pdf",
            "document_type":"ПЗ",
            "page":11,
            "text":(
                "Пожарная и взрывопожарная опасность: категория В1. "
                "Постоянное пребывание людей: не предусмотрено. "
                "Уровень ответственности: нормальный."
            ),
        },
    ]
    documents=[_id_features_document(
        ("OBJ-A","Раздел ПД №1_ПЗ.pdf",10),
        ("OBJ-B","Раздел ПД №1_ПЗ.pdf",11),
    )]
    set_result=_set_completeness_evaluation(contract,pages,documents)
    assert set_result["complete"] is False
    assert set_result["owner_scope_state"]=="OWNER_NOT_PROVEN"
    assert set_result["owner_object_id"]==""


def test_alpha8_negated_set_evidence_requires_explicit_disclosure_opt_in():
    page={
        "document":"ПЗ.pdf",
        "document_type":"ПЗ",
        "page":1,
        "text":"Объект не относится к опасным производственным объектам.",
    }
    ordinary=_set_element_match(
        {
            "id":"opo",
            "label":"ОПО",
            "aliases":["опасным производственным объектам"],
        },
        [page],
        "TEST-ORDINARY",
    )
    disclosure=_set_element_match(
        {
            "id":"opo",
            "label":"ОПО",
            "aliases":["опасным производственным объектам"],
            "allow_negated_evidence":True,
            "assertion_regexes":[
                r"(?:не\s+)?(?:относится|является)[^\n]{0,90}опасн\w+\s+производственн\w+\s+объект\w*"
            ],
        },
        [page],
        "TEST-DISCLOSURE",
    )
    assert ordinary["matched"] is False
    assert disclosure["matched"] is True


def _responsibility_assignment_document(*rows):
    document=_owner_model_document(*rows)
    document["Файл"]="Задание на проектирование.pdf"
    document["Тип документа"]="Задание на проектирование"
    return document


def test_alpha8_fz384_responsibility_in_assignment_promotes_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_responsibility_assignment_document(
        ("OBJ-RESP","Задание на проектирование.pdf",5),
    )]
    pages=[{
        "document":"Задание на проектирование.pdf",
        "document_type":"Задание на проектирование",
        "page":5,
        "text":"Уровень ответственности объекта: нормальный.",
    }]
    contracts={row["requirement_id"]:row for row in _foundation().contracts()}
    contract=contracts["FZ384-15-2-RESP-INPUT"]
    ranked=_rank_candidates(contract,pages)
    assert ranked and ranked[0][0] >= 2, {
        "keywords":contract.get("keywords"),
        "ranked":ranked,
    }
    raw_row=engine._execute(contract,pages,documents)
    assert raw_row["kind"]=="VERIFIED_OK", {
        "raw_kind":raw_row.get("kind"),
        "raw_reason":raw_row.get("reason_code"),
        "raw_score":raw_row.get("retrieval_keyword_score"),
        "raw_set":raw_row.get("set_completeness"),
    }
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FZ384-15-2-RESP-INPUT")
    diagnostic={
        "kind":row.get("kind"),
        "reason_code":row.get("reason_code"),
        "proof_state":row.get("proof_state"),
        "retrieval_kind":row.get("retrieval_kind"),
        "retrieval_reason_code":row.get("retrieval_reason_code"),
        "retrieval_keyword_score":row.get("retrieval_keyword_score"),
        "set_complete":(row.get("set_completeness") or {}).get("complete"),
        "set_owner":(row.get("set_completeness") or {}).get("owner_scope_state"),
        "missing_ids":(row.get("set_completeness") or {}).get("missing_ids"),
    }
    assert int(row.get("retrieval_keyword_score") or 0) >= 2, diagnostic
    assert row["set_completeness"]["complete"] is True, diagnostic
    assert row["kind"]=="VERIFIED_OK", row
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["owner_scope_state"]=="CONFIRMED"
    assert row["set_completeness"]["owner_object_id"]=="OBJ-RESP"
    assert row["set_completeness"]["matched_count"]==1


def test_alpha8_fz384_responsibility_same_words_in_pd_do_not_satisfy_input_source():
    engine=NormativeExecutionEngine20(_foundation())
    document=_owner_model_document(
        ("OBJ-RESP","Раздел ПД №1_ПЗ.pdf",5),
    )
    document["Файл"]="Раздел ПД №1_ПЗ.pdf"
    document["Тип документа"]="ПЗ"
    documents=[document]
    pages=[{
        "document":"Раздел ПД №1_ПЗ.pdf",
        "document_type":"ПЗ",
        "page":5,
        "text":"Уровень ответственности объекта: нормальный.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FZ384-15-2-RESP-INPUT")
    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False


def test_alpha8_fz384_responsibility_assignment_requires_actual_level_value():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_responsibility_assignment_document(
        ("OBJ-RESP","Задание на проектирование.pdf",5),
    )]
    pages=[{
        "document":"Задание на проектирование.pdf",
        "document_type":"Задание на проектирование",
        "page":5,
        "text":"Уровень ответственности объекта определяется в соответствии с 384-ФЗ.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FZ384-15-2-RESP-INPUT")
    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False


def test_alpha8_source_scoped_set_uses_document_metadata_not_text_reference():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}
    contract=contracts["FZ384-15-2-RESP-INPUT"]
    pages=[
        {
            "document":"Раздел ПД №1_ПЗ.pdf",
            "document_type":"ПЗ",
            "page":8,
            "text":"В задании на проектирование указан уровень ответственности: нормальный.",
        },
        {
            "document":"Задание на проектирование.pdf",
            "document_type":"Задание на проектирование",
            "page":9,
            "text":"Уровень ответственности: нормальный.",
        },
    ]
    documents=[_owner_model_document(
        ("OBJ-RESP","Раздел ПД №1_ПЗ.pdf",8),
        ("OBJ-RESP","Задание на проектирование.pdf",9),
    )]
    result=_set_completeness_evaluation(contract,pages,documents)
    assert result["complete"] is True
    assert result["evidence"][0]["document"]=="Задание на проектирование.pdf"


def test_alpha8_pp87_insolation_and_daylight_results_promote_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":30,
            "text":"Продолжительность инсоляции помещения составляет 2,5 ч.",
        },
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":31,
            "text":"КЕО помещения принято 1,5 %.",
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-D1-INSOLATION")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["total_count"]==2


def test_alpha8_pp87_insolation_heading_without_numeric_results_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":30,
        "text":"Инсоляция и КЕО. Приведены результаты расчётов продолжительности "
               "инсоляции и коэффициента естественной освещённости.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-D1-INSOLATION")
    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False


def test_alpha8_pp87_insolation_requires_both_calculation_results():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":30,
        "text":"Продолжительность инсоляции помещения составляет 2,5 ч.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-D1-INSOLATION")
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SET_PROOF_CONTRACT_REQUIRED"
    assert "daylight_factor_result" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0


def test_alpha8_pp87_insolation_copied_requirement_with_clause_number_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":30,
        "text":"Согласно п. 13 д(1) должны быть приведены результаты расчётов "
               "продолжительности инсоляции и коэффициента естественной освещённости.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-D1-INSOLATION")
    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False


def test_alpha8_sp18_closed_storm_sewer_promotes_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":14,
        "text":"Система дождевой канализации принята закрытого типа.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.52-CLOSED-STORM-SEWER")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==1
    assert row["set_completeness"]["total_count"]==1


def test_alpha8_sp18_generic_storm_sewer_without_closed_type_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":14,
        "text":"На площадке предусматривается дождевая канализация для отвода поверхностного стока.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.52-CLOSED-STORM-SEWER")
    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False


def test_alpha8_sp18_unrelated_closed_system_cannot_prove_storm_sewer():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":14,
        "text":"Закрытая система хозяйственно-бытовой канализации. Дождевая канализация принята открытой.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.52-CLOSED-STORM-SEWER")
    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False


def test_alpha8_sp18_livnevaya_closed_type_is_equivalent_positive_evidence():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №5_подраздел ПД №3_ИОС3.pdf","Тип документа":"ИОС"}]
    pages=[{
        "document":"Раздел ПД №5_подраздел ПД №3_ИОС3.pdf",
        "document_type":"ИОС",
        "page":22,
        "text":"Ливневая канализация запроектирована закрытого типа.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP18-5.52-CLOSED-STORM-SEWER")
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"


def _hybrid_set_proof_row(*, complete):
    evidence=[{
        "evidence_id":"NORM-SET-HYBRID-X-01",
        "document":"ИОС.pdf",
        "page":7,
        "section":"ИОС",
        "fragment":"Полное достаточное доказательство.",
        "matched_terms":["достаточное доказательство"],
        "set_element_id":"sufficient_condition",
        "set_element_label":"Достаточное условие",
    }] if complete else []
    return {
        "requirement_id":"HYBRID-SET-X",
        "document_id":"TEST",
        "source":"Test source",
        "paragraph":"1",
        "topic":"Гибридный set proof",
        "requirement":"Требование с детерминированным достаточным условием и semantic fallback.",
        "sections":["ИОС"],
        "check_kind":"SEMANTIC",
        "proof_type_hint":"SET_COMPLETENESS",
        "kind":"VERIFIED_OK",
        "state":"Подтверждено",
        "reason_code":"NORMATIVE_RETRIEVAL_CANDIDATE_CONFIRMED",
        "evidence_id":"NORM-E-HYBRID-X-01",
        "evidence_document":"ИОС.pdf",
        "evidence_page":7,
        "evidence_fragment":"Адресный кандидат для смысловой проверки.",
        "matched_keywords":["кандидат"],
        "retrieval_candidate_count":1,
        "evidence_candidates":[{
            "evidence_id":"NORM-E-HYBRID-X-01",
            "document":"ИОС.pdf",
            "page":7,
            "section":"ИОС",
            "fragment":"Адресный кандидат для смысловой проверки.",
            "matched_keywords":["кандидат"],
            "retrieval_keyword_score":2,
            "retrieval_keyword_coverage":1.0,
        }],
        "set_completeness":{
            "configured":True,
            "mode":"ALL_REQUIRED",
            "promotion_policy":"DETERMINISTIC_WITH_SEMANTIC_FALLBACK",
            "atomization_complete":True,
            "complete":complete,
            "matched_count":1 if complete else 0,
            "required_count":1,
            "total_count":1,
            "missing_ids":[] if complete else ["sufficient_condition"],
            "missing_labels":[] if complete else ["Достаточное условие"],
            "applicability_pending_count":0,
            "evidence":evidence,
        },
    }


def test_alpha8_hybrid_set_complete_uses_deterministic_fast_path():
    result=NormativeProofEngine20().run([_hybrid_set_proof_row(complete=True)])
    row=result["rows"][0]

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["reason_code"]=="NORMATIVE_SET_COMPLETENESS_PROOF_CONFIRMED"
    assert result["semantic_queue_total"]==0


def test_alpha8_hybrid_set_incomplete_routes_to_semantic_fallback():
    result=NormativeProofEngine20().run([_hybrid_set_proof_row(complete=False)])
    row=result["rows"][0]

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"]=="NORMATIVE_SET_DETERMINISTIC_FAST_PATH_NOT_PROVEN"
    assert result["semantic_queue_total"]==1
    assert result["semantic_queue"][0]["requirement_id"]=="HYBRID-SET-X"
    assert result["project_findings"]==0


def test_alpha8_fnp505_surface_emergency_universal_scope_uses_deterministic_fast_path():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №5_ИОС.pdf","Тип документа":"ИОС"}]
    pages=[{
        "document":"Раздел ПД №5_ИОС.pdf",
        "document_type":"ИОС",
        "page":18,
        "text":(
            "На всех объектах поверхностного комплекса предусмотрено аварийное освещение "
            "от независимого источника питания."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1461-SURFACE-EMERGENCY-LIGHTING")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="FNP505-1461-SURFACE-EMERGENCY-LIGHTING"
        for packet in result["semantic_queue"]
    )


def test_alpha8_fnp505_workplace_only_statement_keeps_semantic_fallback():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №5_ИОС.pdf","Тип документа":"ИОС"}]
    pages=[{
        "document":"Раздел ПД №5_ИОС.pdf",
        "document_type":"ИОС",
        "page":18,
        "text":(
            "Каждое рабочее место поверхностного комплекса имеет аварийное освещение "
            "от независимого источника питания."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1461-SURFACE-EMERGENCY-LIGHTING")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"]=="NORMATIVE_SET_DETERMINISTIC_FAST_PATH_NOT_PROVEN"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="FNP505-1461-SURFACE-EMERGENCY-LIGHTING"
        for packet in result["semantic_queue"]
    )
    assert result["project_findings"]==0


def test_alpha8_fnp505_surface_scope_without_independent_power_keeps_semantic_fallback():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №5_ИОС.pdf","Тип документа":"ИОС"}]
    pages=[{
        "document":"Раздел ПД №5_ИОС.pdf",
        "document_type":"ИОС",
        "page":18,
        "text":(
            "На всех объектах поверхностного комплекса предусмотрено аварийное освещение. "
            "Питание систем освещения приведено ниже."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="FNP505-1461-SURFACE-EMERGENCY-LIGHTING")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def _production_pzu_document():
    return {
        "Файл":"Раздел ПД №2_ПЗУ.pdf",
        "Тип документа":"ПЗУ",
        "pp87_project_profile":{"profile":"Объект производственного назначения"},
    }


def test_alpha8_pp87_transport_scheme_fast_path_promotes_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_production_pzu_document()]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":19,
        "text":(
            "Схема транспортных коммуникаций обоснована для внешних и внутренних "
            "грузоперевозок."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-I-TRANSPORT")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-12-I-TRANSPORT"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_transport_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_production_pzu_document()]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":19,
        "text":(
            "Схемы транспортных коммуникаций для внешних и внутренних грузоперевозок "
            "должны быть обоснованы."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-I-TRANSPORT")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-12-I-TRANSPORT"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_transport_external_only_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_production_pzu_document()]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":19,
        "text":"Схема транспортных коммуникаций обоснована для внешних грузоперевозок.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-I-TRANSPORT")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def test_alpha8_pp87_zoning_fast_path_promotes_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_production_pzu_document()]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":21,
        "text":(
            "Зонирование территории обосновано функциональными связями производственных зон. "
            "Принципиальная схема размещения территориальных зон обоснована технологическими потоками."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-H-ZONING")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-12-H-ZONING"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_zoning_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_production_pzu_document()]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":21,
        "text":(
            "Для объекта производственного назначения в ПЗУ должно быть обосновано "
            "зонирование территории и принципиальная схема размещения территориальных зон."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-H-ZONING")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-12-H-ZONING"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_zoning_without_scheme_justification_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_production_pzu_document()]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":21,
        "text":(
            "Зонирование территории обосновано функциональными связями. "
            "Принципиальная схема размещения территориальных зон приведена на чертеже."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-H-ZONING")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert "territorial_zone_scheme_justification" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0


def test_alpha8_pp87_landscape_description_fast_path_promotes_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":24,
        "text":(
            "Решения по благоустройству территории предусматривают устройство "
            "твердого покрытия на пешеходных участках и восстановление нарушенных участков."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-G-LANDSCAPE")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-12-G-LANDSCAPE"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_landscape_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":24,
        "text":"В ПЗУ должны быть описаны решения по благоустройству территории.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-G-LANDSCAPE")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-12-G-LANDSCAPE"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_landscape_heading_only_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":24,
        "text":"Благоустройство территории. Основные решения приведены на листе 5.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-G-LANDSCAPE")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def test_alpha8_pp87_planning_fast_path_promotes_description_and_justification():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":25,
            "text":(
                "Решения по планировочной организации земельного участка предусматривают "
                "размещение проектируемых объектов с учетом технологических связей."
            ),
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":26,
            "text":(
                "Решения по планировочной организации земельного участка обоснованы "
                "взаимным расположением зданий и существующей транспортной схемой."
            ),
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-C-PLANNING")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-12-C-PLANNING"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_planning_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":25,
        "text":(
            "В ПЗУ должны быть обоснованы и описаны решения по планировочной "
            "организации земельного участка."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-C-PLANNING")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-12-C-PLANNING"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_planning_description_without_justification_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":25,
        "text":(
            "Решения по планировочной организации земельного участка предусматривают "
            "размещение проектируемых объектов вдоль внутриплощадочной дороги."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-C-PLANNING")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert "planning_solution_justification" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0


def test_alpha8_pp87_natural_light_fast_path_promotes_without_ai():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":34,
        "text":(
            "Помещения с постоянным пребыванием людей обеспечиваются естественным "
            "освещением через оконные проемы."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-E-LIGHT")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-13-E-LIGHT"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_natural_light_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":34,
        "text":(
            "В АР должны быть описаны архитектурные решения по обеспечению естественного "
            "освещения помещений с постоянным пребыванием людей."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-E-LIGHT")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-13-E-LIGHT"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_natural_light_without_permanent_occupancy_relation_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":34,
        "text":"В помещениях предусмотрено естественное освещение через оконные проемы.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-E-LIGHT")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def test_alpha8_pp87_sanitary_fast_path_promotes_compliance_and_justification():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":40,
            "text":(
                "Объёмно-планировочные решения обеспечивают соблюдение "
                "санитарно-эпидемиологических требований."
            ),
        },
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":41,
            "text":(
                "Объёмно-планировочные решения обоснованы функциональным зонированием "
                "и разделением потоков."
            ),
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-H-SANITARY")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-13-H-SANITARY"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_sanitary_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":40,
        "text":(
            "В АР должны быть описаны и обоснованы объёмно-планировочные решения, "
            "обеспечивающие соблюдение санитарно-эпидемиологических требований."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-H-SANITARY")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-13-H-SANITARY"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_sanitary_compliance_without_justification_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":40,
        "text":(
            "Объёмно-планировочные решения обеспечивают соблюдение "
            "санитарно-эпидемиологических требований."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-H-SANITARY")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert "sanitary_solution_justification" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0


def test_alpha8_pp87_facade_interior_composition_fast_path_promotes():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":45,
            "text":(
                "Композиционные приемы при оформлении фасадов и интерьеров приняты "
                "с учетом единого ритма проемов и отделочных материалов."
            ),
        },
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":46,
            "text":(
                "Композиционные приемы при оформлении фасадов и интерьеров обоснованы "
                "функциональным назначением помещений и архитектурным обликом здания."
            ),
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-C-FACADE")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-13-C-FACADE"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_facade_interior_composition_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":45,
        "text":(
            "В АР должны быть описаны и обоснованы композиционные приемы "
            "при оформлении фасадов и интерьеров."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-C-FACADE")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-13-C-FACADE"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_facade_only_composition_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":45,
        "text":"Композиционные приемы оформления фасадов приняты с учетом ритма проемов.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-C-FACADE")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def test_alpha8_pp87_room_finishing_fast_path_promotes_all_required_groups():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":50,
            "text":(
                "Решения по отделке помещений основного, вспомогательного, обслуживающего "
                "и технического назначения приняты с учетом условий эксплуатации."
            ),
        },
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":51,
            "text":(
                "Решения по отделке помещений основного, вспомогательного, обслуживающего "
                "и технического назначения обоснованы санитарными и эксплуатационными требованиями."
            ),
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-D-FINISH")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-13-D-FINISH"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_room_finishing_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":50,
        "text":(
            "В АР должны быть описаны и обоснованы решения по отделке помещений "
            "основного, вспомогательного, обслуживающего и технического назначения."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-D-FINISH")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-13-D-FINISH"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_room_finishing_partial_scope_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":50,
        "text":(
            "Решения по отделке помещений основного и вспомогательного назначения "
            "приняты с учетом условий эксплуатации."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-D-FINISH")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def test_alpha8_pp87_engineering_prep_fast_path_promotes_description_and_justification():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":28,
            "text":(
                "Решения по инженерной подготовке и инженерной защите территории от "
                "опасных процессов, поверхностных и грунтовых вод приняты с учетом рельефа площадки."
            ),
        },
        {
            "document":"Раздел ПД №2_ПЗУ.pdf",
            "document_type":"ПЗУ",
            "page":29,
            "text":(
                "Решения по инженерной подготовке и инженерной защите территории от "
                "опасных процессов, поверхностных и грунтовых вод обоснованы результатами изысканий."
            ),
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-E-ENGINEERING-PREP")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-12-E-ENGINEERING-PREP"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_engineering_prep_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":28,
        "text":(
            "В ПЗУ должны быть обоснованы и описаны решения по инженерной подготовке "
            "и инженерной защите территории от опасных процессов, поверхностных и грунтовых вод."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-E-ENGINEERING-PREP")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-12-E-ENGINEERING-PREP"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_engineering_prep_without_protection_scope_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":28,
        "text":"Решения по инженерной подготовке территории приняты с учетом существующего рельефа.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-E-ENGINEERING-PREP")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def _sp12_category_document(*rows):
    document=_owner_model_document(*rows)
    document["Файл"]="Раздел ПД №5_ТХ.pdf"
    document["Тип документа"]="ТХ"
    return document


def test_alpha8_sp12_sequential_category_fast_path_promotes_same_owner():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_sp12_category_document(
        ("ROOM-CAT","Раздел ПД №5_ТХ.pdf",60),
    )]
    pages=[{
        "document":"Раздел ПД №5_ТХ.pdf",
        "document_type":"ТХ",
        "page":60,
        "text":(
            "Определение категории помещения выполнено последовательной проверкой: "
            "категория А, категория Б, В1, В2, В3, В4, категория Г, категория Д."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP12-5.2-SEQUENTIAL-CATEGORY")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["complete"] is True
    assert row["set_completeness"]["owner_scope_state"]=="CONFIRMED"
    assert row["set_completeness"]["owner_object_id"]=="ROOM-CAT"
    assert not any(
        packet["requirement_id"]=="SP12-5.2-SEQUENTIAL-CATEGORY"
        for packet in result["semantic_queue"]
    )


def test_alpha8_sp12_sequential_category_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_sp12_category_document(
        ("ROOM-CAT","Раздел ПД №5_ТХ.pdf",60),
    )]
    pages=[{
        "document":"Раздел ПД №5_ТХ.pdf",
        "document_type":"ТХ",
        "page":60,
        "text":(
            "Определение категории помещения должно выполняться последовательной проверкой "
            "от наиболее опасной категории А к наименее опасной категории Д."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP12-5.2-SEQUENTIAL-CATEGORY")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="SP12-5.2-SEQUENTIAL-CATEGORY"
        for packet in result["semantic_queue"]
    )


def test_alpha8_sp12_sequential_category_incomplete_order_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_sp12_category_document(
        ("ROOM-CAT","Раздел ПД №5_ТХ.pdf",60),
    )]
    pages=[{
        "document":"Раздел ПД №5_ТХ.pdf",
        "document_type":"ТХ",
        "page":60,
        "text":(
            "Определение категории помещения выполнено последовательной проверкой: "
            "категория А, категория Б, В1, В2, категория Д."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP12-5.2-SEQUENTIAL-CATEGORY")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def test_alpha8_pp87_arch_justification_fast_path_promotes_both_domains():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":55,
            "text":(
                "Объёмно-пространственные решения обоснованы функциональным зонированием "
                "и взаимосвязью основных помещений."
            ),
        },
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":56,
            "text":(
                "Архитектурно-художественные решения обоснованы характером окружающей "
                "застройки и принятым композиционным построением фасадов."
            ),
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B-ARCH")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-13-B-ARCH"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_arch_justification_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":55,
        "text":(
            "В АР должно быть приведено обоснование принятых объёмно-пространственных "
            "и архитектурно-художественных решений."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B-ARCH")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-13-B-ARCH"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_arch_justification_single_domain_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":55,
        "text":"Объёмно-пространственные решения обоснованы функциональным зонированием.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B-ARCH")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert "architectural_artistic_justification" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0


def _sp4_access_document(*rows):
    document=_owner_model_document(*rows)
    document["Файл"]="Раздел ПД №2_ПЗУ.pdf"
    document["Тип документа"]="ПЗУ"
    return document


def test_alpha8_sp4_two_sided_full_length_fire_access_fast_path_promotes():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_sp4_access_document(
        ("OBJ-FIRE-ACCESS","Раздел ПД №2_ПЗУ.pdf",70),
    )]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":70,
        "text":"Подъезд пожарной техники по длине здания обеспечен с двух сторон.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.1-FIRE-ACCESS-SIDES")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["complete"] is True
    assert row["set_completeness"]["owner_scope_state"]=="CONFIRMED"
    assert row["set_completeness"]["owner_object_id"]=="OBJ-FIRE-ACCESS"
    assert not any(
        packet["requirement_id"]=="SP4-8.2.1-FIRE-ACCESS-SIDES"
        for packet in result["semantic_queue"]
    )


def test_alpha8_sp4_one_sided_access_keeps_semantic_fallback():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_sp4_access_document(
        ("OBJ-FIRE-ACCESS","Раздел ПД №2_ПЗУ.pdf",70),
    )]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":70,
        "text":"При ширине здания 12 м подъезд пожарной техники по длине здания обеспечен с одной стороны.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.1-FIRE-ACCESS-SIDES")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="SP4-8.2.1-FIRE-ACCESS-SIDES"
        for packet in result["semantic_queue"]
    )


def test_alpha8_sp4_copied_access_requirement_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[_sp4_access_document(
        ("OBJ-FIRE-ACCESS","Раздел ПД №2_ПЗУ.pdf",70),
    )]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":70,
        "text":(
            "Для производственных и складских зданий должен быть обеспечен подъезд "
            "пожарной техники по длине здания с двух сторон при ширине более 18 м."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="SP4-8.2.1-FIRE-ACCESS-SIDES")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert result["project_findings"]==0


def test_alpha8_pp87_tep_fast_path_promotes_named_numeric_indicators():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":32,
        "text":(
            "Технико-экономические показатели земельного участка: "
            "площадь земельного участка 12500 м2; коэффициент застройки 0,42."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-D-TEP")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==3
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-12-D-TEP"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_tep_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":32,
        "text":"В ПЗУ должны быть приведены технико-экономические показатели земельного участка.",
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-D-TEP")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert any(
        packet["requirement_id"]=="PP87-12-D-TEP"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_tep_incomplete_numeric_block_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":32,
        "text":(
            "Технико-экономические показатели земельного участка: "
            "площадь земельного участка 12500 м2."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-D-TEP")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert "development_coefficient_indicator" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0


def test_alpha8_pp87_energy_efficiency_design_fast_path_promotes_description_and_justification():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":60,
            "text":(
                "Архитектурные решения, направленные на повышение энергетической "
                "эффективности объекта, предусматривают компактную форму здания и "
                "сокращение площади наружных ограждений."
            ),
        },
        {
            "document":"Раздел ПД №3_АР.pdf",
            "document_type":"АР",
            "page":61,
            "text":(
                "Архитектурные решения, направленные на повышение энергетической "
                "эффективности объекта, обоснованы снижением теплопотерь через наружные ограждения."
            ),
        },
    ]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B3-EFF-DESIGN")

    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert row["set_completeness"]["matched_count"]==2
    assert row["set_completeness"]["complete"] is True
    assert not any(
        packet["requirement_id"]=="PP87-13-B3-EFF-DESIGN"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_energy_efficiency_design_copied_requirement_stays_semantic():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":60,
        "text":(
            "АР должно содержать описание и обоснование архитектурных решений, "
            "направленных на повышение энергетической эффективности объекта."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B3-EFF-DESIGN")

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["set_completeness"]["complete"] is False
    assert any(
        packet["requirement_id"]=="PP87-13-B3-EFF-DESIGN"
        for packet in result["semantic_queue"]
    )


def test_alpha8_pp87_energy_efficiency_design_without_justification_does_not_promote():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"}]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":60,
        "text":(
            "Архитектурные решения, направленные на повышение энергетической "
            "эффективности объекта, предусматривают компактную форму здания."
        ),
    }]
    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-13-B3-EFF-DESIGN")

    assert row["kind"]!="VERIFIED_OK"
    assert row["set_completeness"]["complete"] is False
    assert "energy_efficiency_arch_solution_justification" in row["set_completeness"]["missing_ids"]
    assert result["project_findings"]==0
