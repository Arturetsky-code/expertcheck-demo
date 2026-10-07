import json

from core20.normative_execution import NormativeExecutionEngine20
from core20.normative_foundation import NormativeKnowledgeFoundation20


def _foundation():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]/"knowledge"
    return NormativeKnowledgeFoundation20(root)


def _owner_document(*rows):
    objects={}
    for object_id,document,page in rows:
        obj=objects.setdefault(object_id,{
            "object_id":object_id,
            "name":object_id,
            "properties":{"TDA":[]},
        })
        obj["properties"]["TDA"].append({
            "document":document,
            "page":page,
            "section":"",
            "fact_admission_decision":"ADMIT",
        })
    return {"project_understanding":{"objects":list(objects.values())}}


def _fz384_identification_text(*, responsibility="нормальный"):
    return "\n".join([
        "Идентификационные признаки.",
        "Назначение объекта: склад аммиачной селитры;",
        "Функционально-технологические особенности: хранение аммиачной селитры;",
        "Опасные природные процессы и техногенные воздействия: отсутствуют;",
        "Принадлежность к ОПО: относится;",
        "Пожарная и взрывопожарная опасность: категория А;",
        "Постоянное пребывание людей: не предусмотрено;",
        f"Уровень ответственности: {responsibility}.",
    ])


def test_tda01_wrong_page_type_cannot_create_deterministic_proof():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[
        {"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"},
        {"Файл":"Раздел ПД №3_АР.pdf","Тип документа":"АР"},
    ]
    pages=[{
        "document":"Раздел ПД №3_АР.pdf",
        "document_type":"АР",
        "page":7,
        "text":(
            "Характеристика земельного участка, предоставленного для размещения объекта "
            "капитального строительства. Площадь земельного участка приведена."
        ),
    }]

    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-A-LAND")

    assert row["kind"]!="VERIFIED_OK"
    assert row["reason_code"]=="NORMATIVE_SECTION_EVIDENCE_MISSING"
    assert result["project_findings"]==0


def test_tda02_missing_positive_evidence_is_not_project_finding():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":7,
        "text":"Общие сведения без доказательства проверяемого требования.",
    }]

    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-A-LAND")

    assert row["kind"] in {"REVIEW_QUESTION","SYSTEM_LIMITATION"}
    assert row["kind"]!="PROJECT_FINDING"
    assert result["project_findings"]==0


def test_tda03_cross_document_mismatch_keeps_both_sources_and_falls_back():
    engine=NormativeExecutionEngine20(_foundation())
    owner=_owner_document(
        ("OBJ-ID","Задание на проектирование.pdf",5),
        ("OBJ-ID","Раздел ПД №1_ПЗ.pdf",10),
    )
    owner["Файл"]="Задание на проектирование.pdf"
    owner["Тип документа"]="Задание на проектирование"
    documents=[
        owner,
        {"Файл":"Раздел ПД №1_ПЗ.pdf","Тип документа":"ПЗ"},
    ]
    pages=[
        {
            "document":"Задание на проектирование.pdf",
            "document_type":"Задание на проектирование",
            "page":5,
            "text":_fz384_identification_text(responsibility="нормальный"),
        },
        {
            "document":"Раздел ПД №1_ПЗ.pdf",
            "document_type":"ПЗ",
            "page":10,
            "text":_fz384_identification_text(responsibility="повышенный"),
        },
    ]

    result=engine.run(documents,pages)
    row=next(
        x for x in result["rows"]
        if x["requirement_id"]=="FZ384-4-11-ID-IN-ASSIGNMENT-PD"
    )

    assert row["kind"]=="REVIEW_QUESTION"
    assert row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
    assert row["cross_document_value"]["status"]=="VALUE_MISMATCH"
    mismatch=next(
        x for x in row["cross_document_value"]["mismatches"]
        if x["field_id"]=="responsibility_level"
    )
    assert mismatch["values_by_group"]=={
        "ASSIGNMENT":"нормальный",
        "PD":"повышенный",
    }
    evidence=row["cross_document_value"]["evidence"]
    assert any(x["document"]=="Задание на проектирование.pdf" for x in evidence)
    assert any(x["document"]=="Раздел ПД №1_ПЗ.pdf" for x in evidence)
    assert result["project_findings"]==0


def test_tda04_unverified_clause_cannot_be_upgraded_by_semantic_checkpoint(tmp_path):
    (tmp_path/"normative_documents_registry.json").write_text(
        json.dumps([{
            "document_id":"TDA-DOC",
            "title":"TDA normative document",
            "source_class":"official",
            "status":"Действует",
            "verified_on":"2026-10-07",
            "validity_canonical_id":"TDA-DOC",
        }],ensure_ascii=False),
        encoding="utf-8",
    )
    (tmp_path/"normative_validity_registry.json").write_text(
        json.dumps({"records":[{
            "canonical_id":"TDA-DOC",
            "status":"Действует",
            "verified_on":"2026-10-07",
        }]},ensure_ascii=False),
        encoding="utf-8",
    )
    (tmp_path/"normative_requirements_v3.json").write_text(
        json.dumps([{
            "id":"TDA-04-UNVERIFIED",
            "source":"TDA normative document",
            "topic":"Unverified clause",
            "requirement":"Уровень ответственности должен быть указан.",
            "sections":["ПЗ"],
            "check_kind":"SEMANTIC",
            "automation":"AUTO",
            "keywords":["уровень ответственности"],
            "document_id":"TDA-DOC",
            "paragraph":"п. 1",
            "clause_verified":False,
            "evidence_contract":{
                "minimum_sources":1,
                "requires_page_reference":True,
                "execution_mode":"SEMANTIC_PROOF",
                "applicability":"SECTION_PRESENT",
            },
            "conclusion_policy":"VERIFIED_ONLY",
        }],ensure_ascii=False),
        encoding="utf-8",
    )

    foundation=NormativeKnowledgeFoundation20(tmp_path)
    contract=foundation.contracts()[0]
    assert contract["trust_state"]=="VERIFIED_DOCUMENT_CLAUSE_PENDING"
    assert contract["automatic_contract_ready"] is False

    documents=[{
        "Файл":"Раздел ПД №1_ПЗ.pdf",
        "Тип документа":"ПЗ",
        "normative_semantic_proof":{
            "decisions":{
                "TDA-04-UNVERIFIED":{
                    "state":"VERIFIED_OK",
                    "judge_verdict":"SUPPORTS",
                    "critic_accept":True,
                    "independent":True,
                }
            }
        },
    }]
    pages=[{
        "document":"Раздел ПД №1_ПЗ.pdf",
        "document_type":"ПЗ",
        "page":1,
        "text":"Уровень ответственности: нормальный.",
    }]

    result=NormativeExecutionEngine20(foundation).run(documents,pages)

    assert all(
        row["requirement_id"]!="TDA-04-UNVERIFIED"
        for row in result["rows"]
    )
    assert result["verified_ok"]==0
    assert result["project_findings"]==0


def test_tda05_promoted_result_preserves_evidence_and_normative_address():
    engine=NormativeExecutionEngine20(_foundation())
    documents=[{"Файл":"Раздел ПД №2_ПЗУ.pdf","Тип документа":"ПЗУ"}]
    pages=[{
        "document":"Раздел ПД №2_ПЗУ.pdf",
        "document_type":"ПЗУ",
        "page":7,
        "text":(
            "Характеристика земельного участка, предоставленного для размещения объекта "
            "капитального строительства. Площадь земельного участка и условия размещения "
            "объекта приведены в настоящем разделе."
        ),
    }]

    result=engine.run(documents,pages)
    row=next(x for x in result["rows"] if x["requirement_id"]=="PP87-12-A-LAND")

    assert row["kind"]=="VERIFIED_OK"
    assert row["evidence_document"]=="Раздел ПД №2_ПЗУ.pdf"
    assert row["evidence_page"]==7
    assert row["evidence_fragment"]
    assert row["source"]
    assert row["paragraph"]
    assert row["requirement_id"]=="PP87-12-A-LAND"
