import json

from core20.model import CanonicalProject, Comparison, Evidence, ProjectObject
from core20.normative_execution import NormativeExecutionEngine20
from core20.normative_foundation import NormativeKnowledgeFoundation20
from core20.verification import VerificationEngine20


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
def _tda07_evidence(project, evidence_id, *, object_id, parameter_code, section, page, value):
    project.add_evidence(Evidence(
        evidence_id=evidence_id,
        document_name=f"{section}.pdf",
        section=section,
        page=page,
        fragment=f"{parameter_code}: {value} м2.",
        addressable=True,
        trusted=True,
        metadata={
            "comparison_object_id":object_id,
            "comparison_parameter_code":parameter_code,
            "observed_value":value,
            "observed_unit":"м2",
        },
    ))


def test_tda07_phase_a_surfaces_conflicting_comparison_decisions():
    project=CanonicalProject(project_id="PRJ-TDA07",name="TDA-07")
    project.add_object(ProjectObject(object_id="OBJ-A",name="Здание проборазделки"))

    _tda07_evidence(
        project,"E-PZ",object_id="OBJ-A",parameter_code="AREA_BUILD",
        section="ПЗ",page=45,value=89.9,
    )
    _tda07_evidence(
        project,"E-PZU",object_id="OBJ-A",parameter_code="AREA_BUILD",
        section="ПЗУ",page=12,value=89.9,
    )
    _tda07_evidence(
        project,"E-TH",object_id="OBJ-A",parameter_code="AREA_BUILD",
        section="ТХ",page=23,value=23.5,
    )

    project.add_comparison(Comparison(
        comparison_id="CMP-AGREE",
        object_id="OBJ-A",
        parameter_code="AREA_BUILD",
        parameter_name="Площадь застройки",
        unit="м2",
        evidence_ids=["E-PZ","E-PZU"],
        evidence_level="L5",
    ))
    project.add_comparison(Comparison(
        comparison_id="CMP-CONFLICT",
        object_id="OBJ-A",
        parameter_code="AREA_BUILD",
        parameter_name="Площадь застройки",
        unit="м2",
        evidence_ids=["E-PZ","E-TH"],
        evidence_level="L5",
    ))

    result=VerificationEngine20(project).run()

    assert result["decision_arbitration_mode"]=="OBSERVATIONAL"
    assert result["decision_arbitration_state"]=="CONFLICT_REVIEW_REQUIRED"
    assert result["decision_conflict_count"]==1

    conflict=result["decision_conflicts"][0]
    assert conflict["state"]=="CONFLICT_REVIEW_REQUIRED"
    assert conflict["object_id"]=="OBJ-A"
    assert conflict["parameter_code"]=="AREA_BUILD"
    assert conflict["conflicting_states"]==["AGREEMENT","CONFLICT"]
    assert set(conflict["decision_ids"])=={
        next(
            row["verification_id"] for row in result["decision_rows"]
            if row["metadata"].get("canonical_proof_state")=="AGREEMENT"
        ),
        next(
            row["verification_id"] for row in result["decision_rows"]
            if row["metadata"].get("canonical_proof_state")=="CONFLICT"
        ),
    }

    evidence_locations={
        (item["document"],item["page"])
        for item in conflict["evidence"]
    }
    assert ("ПЗ.pdf",45) in evidence_locations
    assert ("ПЗУ.pdf",12) in evidence_locations
    assert ("ТХ.pdf",23) in evidence_locations

    kinds={row["kind"] for row in result["decision_rows"]}
    assert "VERIFIED_OK" in kinds
    assert "PROJECT_FINDING" in kinds
    # Phase A is diagnostic only: verdict suppression is intentionally deferred.
    assert all(row["automatic_verdict_eligible"] for row in result["decision_rows"])
    assert all(
        row["metadata"].get("arbitration_conflict") is True
        for row in result["decision_rows"]
    )


def test_tda07_phase_a_does_not_merge_conflicts_across_different_owners():
    project=CanonicalProject(project_id="PRJ-TDA07-SCOPE",name="TDA-07 owner scope")
    project.add_object(ProjectObject(object_id="OBJ-A",name="Объект А"))
    project.add_object(ProjectObject(object_id="OBJ-B",name="Объект Б"))

    _tda07_evidence(
        project,"A-PZ",object_id="OBJ-A",parameter_code="AREA_BUILD",
        section="ПЗ",page=10,value=50.0,
    )
    _tda07_evidence(
        project,"A-PZU",object_id="OBJ-A",parameter_code="AREA_BUILD",
        section="ПЗУ",page=11,value=50.0,
    )
    _tda07_evidence(
        project,"B-PZ",object_id="OBJ-B",parameter_code="AREA_BUILD",
        section="ПЗ",page=20,value=80.0,
    )
    _tda07_evidence(
        project,"B-PZU",object_id="OBJ-B",parameter_code="AREA_BUILD",
        section="ПЗУ",page=21,value=70.0,
    )

    project.add_comparison(Comparison(
        comparison_id="CMP-A",
        object_id="OBJ-A",
        parameter_code="AREA_BUILD",
        unit="м2",
        evidence_ids=["A-PZ","A-PZU"],
        evidence_level="L5",
    ))
    project.add_comparison(Comparison(
        comparison_id="CMP-B",
        object_id="OBJ-B",
        parameter_code="AREA_BUILD",
        unit="м2",
        evidence_ids=["B-PZ","B-PZU"],
        evidence_level="L5",
    ))

    result=VerificationEngine20(project).run()

    assert {
        row["metadata"].get("canonical_proof_state")
        for row in result["decision_rows"]
    }=={"AGREEMENT","CONFLICT"}
    assert result["decision_arbitration_state"]=="CLEAR"
    assert result["decision_conflict_count"]==0
    assert result["decision_conflicts"]==[]
