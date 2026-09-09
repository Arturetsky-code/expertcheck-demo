from __future__ import annotations

from core20.model import CanonicalProject, Evidence, ProjectObject, Requirement
from core20.requirement_router import route_typed_requirement_evidence
from core20.verification import VerificationEngine20


def _project() -> CanonicalProject:
    project=CanonicalProject(project_id="PRJ-A5",name="Alpha 5")
    project.add_object(ProjectObject(object_id="OBJ-1",name="ДСК"))
    return project


def _evidence(project, eid, fragment, *, section="ТХ", trusted=False, meta=None):
    project.add_evidence(Evidence(
        evidence_id=eid,
        document_name=f"{section}.pdf",
        section=section,
        page=7,
        fragment=fragment,
        addressable=True,
        trusted=trusted,
        metadata=dict(meta or {}),
    ))


def _requirement(project, *, text, code="", value=None, unit="", evidence_ids=None, rtype="VALUE_COMPARISON"):
    project.add_requirement(Requirement(
        requirement_id="R1",
        domain="assignment",
        text=text,
        target_object_id="OBJ-1",
        expected_parameter_code=code,
        expected_evidence_route=["ТХ"],
        evidence_ids=list(evidence_ids or []),
        evidence_level="L4",
        metadata={
            "requirement_type":rtype,
            "required_value":value,
            "unit":unit,
        },
    ))


def test_bucket_volume_exact_parameter_anchor_closes():
    project=_project()
    _evidence(project,"E1","Погрузчик XCMG имеет объем ковша 4,5 м3.")
    _requirement(
        project,
        text="Погрузчик XCMG принять с объемом ковша 4,5 м3",
        code="BUCKET_VOLUME",value=4.5,unit="м3",evidence_ids=["E1"],
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="VERIFIED_OK"
    assert row["metadata"]["canonical_reason_code"]=="ASSIGNMENT_TYPED_VALUE_MATCH"
    assert row["metadata"]["typed_fact_count"]>=1


def test_bucket_volume_cannot_prove_body_volume():
    project=_project()
    _evidence(project,"E1","Погрузчик XCMG имеет объем ковша 4,5 м3.")
    _requirement(
        project,
        text="Автосамосвал принять с объемом кузова 32 м3",
        code="BODY_VOLUME",value=32,unit="м3",evidence_ids=["E1"],
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["automatic_verdict_eligible"] is False
    assert row["metadata"]["canonical_reason_code"]=="PARAMETER_BINDING_NOT_PROVEN"


def test_body_volume_typed_mismatch_can_be_project_finding():
    project=_project()
    _evidence(project,"E1","Автосамосвал SinoTrack: объем кузова 20 м3.")
    _requirement(
        project,
        text="Автосамосвал SinoTrack принять с объемом кузова 32 м3",
        code="BODY_VOLUME",value=32,unit="м3",evidence_ids=["E1"],
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="PROJECT_FINDING"
    assert row["metadata"]["project_value"]==20.0
    assert row["correct_value_verified"] is True


def test_power_pressure_and_voltage_are_parameter_local():
    cases=[
        ("POWER_INSTALLED","Насос принять мощностью 75 кВт","Проектом принят насос; установленная мощность 75 кВт.",75,"кВт"),
        ("OPERATING_PRESSURE","Компрессор принять с рабочим давлением 0,8 МПа","Компрессор устанавливается; рабочее давление 0,8 МПа.",0.8,"МПа"),
        ("VOLTAGE","Электроустановку принять напряжением 6 кВ","Проектом принимается электроустановка; номинальное напряжение 6 кВ.",6,"кВ"),
    ]
    for index,(code,req_text,fragment,value,u) in enumerate(cases,1):
        project=_project()
        _evidence(project,f"E{index}",fragment)
        _requirement(project,text=req_text,code=code,value=value,unit=u,evidence_ids=[f"E{index}"])
        row=VerificationEngine20(project).run()["decision_rows"][0]
        assert row["kind"]=="VERIFIED_OK", (code,row)


def test_capacity_same_unit_but_different_semantic_level_does_not_close():
    project=_project()
    _evidence(project,"E1","Часовая производительность отделения по технологическому режиму составляет 100 т/ч.")
    _requirement(
        project,
        text="Производительность одной линии должна составлять 100 т/ч",
        code="CAPACITY",value=100,unit="т/ч",evidence_ids=["E1"],
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["automatic_verdict_eligible"] is False
    assert row["metadata"]["canonical_reason_code"]=="PARAMETER_BINDING_NOT_PROVEN"


def test_reserve_topology_match_is_independent_proof():
    project=_project()
    _evidence(
        project,"E1",
        "Проектом предусматривается 1 рабочий насос и 1 резервный насос.",
        trusted=True,
    )
    _requirement(
        project,
        text="Предусмотреть 1 рабочий насос и 1 резервный насос",
        code="",value=None,unit="",evidence_ids=["E1"],rtype="SEMANTIC_ENGINEERING",
    )
    result=VerificationEngine20(project).run()
    row=result["decision_rows"][0]
    assert row["kind"]=="VERIFIED_OK"
    assert row["metadata"]["canonical_reason_code"]=="RESERVE_TOPOLOGY_MATCH"
    assert result["reserve_topology_auto"]==1


def test_reserve_topology_mismatch_is_project_finding():
    project=_project()
    _evidence(
        project,"E1",
        "Проектом предусматривается 2 рабочих насоса и 0 резервных насосов.",
        trusted=True,
    )
    _requirement(
        project,
        text="Предусмотреть 1 рабочий насос и 1 резервный насос",
        code="",value=None,unit="",evidence_ids=["E1"],rtype="SEMANTIC_ENGINEERING",
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="PROJECT_FINDING"
    assert row["metadata"]["canonical_reason_code"]=="RESERVE_TOPOLOGY_MISMATCH"


def test_router_finds_only_typed_body_volume_from_saved_page_corpus():
    pages=[
        {
            "document":"ТХ1.pdf","document_type":"ТХ","page":37,
            "text":"Автосамосвал SinoTrack. Проектом принят объем кузова 32 м3. Количество 4 шт."
        },
        {
            "document":"ТХ1.pdf","document_type":"ТХ","page":38,
            "text":"Погрузчик XCMG. Объем ковша 4,5 м3."
        },
    ]
    rows=route_typed_requirement_evidence(
        requirement_text="Автосамосвал SinoTrack принять с объемом кузова 32 м3",
        parameter_code="BODY_VOLUME",
        required_unit="м3",
        expected_sections=["ТХ"],
        page_corpus=pages,
    )
    assert rows
    assert all(row["typed_parameter_code"]=="BODY_VOLUME" for row in rows)
    assert all(float(row["project_value"])==32.0 for row in rows)
    assert all("объем кузова" in row["context"].casefold().replace("ё","е") for row in rows)


def test_router_does_not_turn_bucket_volume_into_body_volume():
    pages=[{
        "document":"ТХ1.pdf","document_type":"ТХ","page":37,
        "text":"Погрузчик XCMG. Объем ковша 4,5 м3. Количество 4 шт."
    }]
    rows=route_typed_requirement_evidence(
        requirement_text="Автосамосвал SinoTrack принять с объемом кузова 32 м3",
        parameter_code="BODY_VOLUME",
        required_unit="м3",
        expected_sections=["ТХ"],
        page_corpus=pages,
    )
    assert rows==[]
