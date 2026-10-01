from pathlib import Path

from core20.normative_execution import (
    NormativeExecutionEngine20,
    _candidate_payloads,
    _near_miss_candidates,
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


def test_alpha8_weak_retrieval_row_keeps_near_miss_diagnostics():
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
    assert row["reason_code"]=="NORMATIVE_EVIDENCE_WEAK"
    assert row["retrieval_near_misses"]
    assert row["retrieval_near_misses"][0]["page"]==7
