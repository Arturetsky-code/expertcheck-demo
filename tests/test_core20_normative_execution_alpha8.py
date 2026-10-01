from pathlib import Path

from core20.normative_execution import (
    NormativeExecutionEngine20,
    _candidate_payloads,
    _near_miss_candidates,
    _strong_near_miss_evidence,
    _set_completeness_evaluation,
    _set_element_match,
    _keyword_span_diagnostic,
    _visual_preflight_evaluation,
    _rank_candidates,
)
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
    assert row["reason_code"]=="NORMATIVE_SEMANTIC_PROOF_REQUIRED"


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
    assert row["proof_type"]=="SEMANTIC_REQUIREMENT"
    assert row["reason_code"]=="NORMATIVE_SEMANTIC_PROOF_REQUIRED"
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
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
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
    assert result["candidate_pages"][0]["drawing_kinds"]==["facade","section_view"]
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
