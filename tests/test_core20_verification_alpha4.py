from __future__ import annotations

from core20.model import CanonicalProject, Evidence, ProjectObject, Requirement
from core20.verification import VerificationEngine20


def _project() -> CanonicalProject:
    project=CanonicalProject(project_id="PRJ-A4",name="Alpha 4")
    project.add_object(ProjectObject(object_id="OBJ-1",name="ДСК"))
    return project


def _evidence(project: CanonicalProject, eid: str, *, section="ТХ", fragment="", meta=None):
    project.add_evidence(Evidence(
        evidence_id=eid,
        document_name=f"{section}.pdf",
        section=section,
        page=10,
        fragment=fragment,
        addressable=True,
        trusted=True,
        metadata=dict(meta or {}),
    ))


def test_assignment_numeric_value_is_recomputed_without_legacy_verdict():
    project=_project()
    _evidence(project,"E1",meta={"project_value":120.0,"observed_unit":"т/ч"})
    project.add_requirement(Requirement(
        requirement_id="R1",domain="assignment",
        text="Производительность линии должна составлять 120 т/ч",
        target_object_id="OBJ-1",
        expected_parameter_code="CAPACITY",
        expected_evidence_route=["ТХ"],
        evidence_ids=["E1"],
        verification_kind="SYSTEM_LIMITATION",
        evidence_level="L4",
        metadata={"requirement_type":"VALUE_COMPARISON","required_value":120.0,"unit":"т/ч"},
    ))
    result=VerificationEngine20(project).run()
    row=result["decision_rows"][0]
    assert row["kind"]=="VERIFIED_OK"
    assert row["automatic_verdict_eligible"] is True
    assert row["metadata"]["canonical_requirement_state"]=="COMPLIANT"
    assert result["assignment_proofs_recomputed"]==1


def test_assignment_numeric_mismatch_becomes_project_finding():
    project=_project()
    _evidence(project,"E1",meta={"project_value":100.0,"observed_unit":"т/ч"})
    project.add_requirement(Requirement(
        requirement_id="R1",domain="assignment",
        text="Производительность линии должна составлять 120 т/ч",
        target_object_id="OBJ-1",
        expected_evidence_route=["ТХ"],
        evidence_ids=["E1"],
        verification_kind="VERIFIED_OK",
        evidence_level="L4",
        metadata={"requirement_type":"VALUE_COMPARISON","required_value":120.0,"unit":"т/ч"},
    ))
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="PROJECT_FINDING"
    assert row["automatic_verdict_eligible"] is True
    assert row["correct_value_verified"] is True
    assert row["metadata"]["project_value"]==100.0


def test_assignment_presence_requires_project_decision_language():
    project=_project()
    _evidence(
        project,"E1",section="ПЗУ",
        fragment="Территория площадки ДСК ограждается панельным ограждением, предусматриваются ворота и калитка.",
        meta={"concept":"FENCING","evidence_kind":"QUALIFIED_PROJECT_PASSAGE"},
    )
    project.add_requirement(Requirement(
        requirement_id="R1",domain="assignment",
        text="Предусмотреть ограждение территории площадки ДСК",
        target_object_id="OBJ-1",
        expected_evidence_route=["ПЗУ"],
        evidence_ids=["E1"],
        evidence_level="L4",
        metadata={"requirement_type":"PRESENCE_REQUIREMENT"},
    ))
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="VERIFIED_OK"
    assert row["metadata"]["canonical_reason_code"]=="ASSIGNMENT_PRESENCE_CONFIRMED"


def test_assignment_presence_mention_without_decision_does_not_close():
    project=_project()
    _evidence(
        project,"E1",section="ПЗУ",
        fragment="На чертеже показана граница территории и существующее ограждение соседнего объекта.",
        meta={"concept":"FENCING","evidence_kind":"QUALIFIED_PROJECT_PASSAGE"},
    )
    project.add_requirement(Requirement(
        requirement_id="R1",domain="assignment",
        text="Предусмотреть ограждение территории площадки ДСК",
        target_object_id="OBJ-1",
        expected_evidence_route=["ПЗУ"],
        evidence_ids=["E1"],
        evidence_level="L4",
        metadata={"requirement_type":"PRESENCE_REQUIREMENT"},
    ))
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["automatic_verdict_eligible"] is False


def test_normative_without_verified_clause_is_fail_closed_even_with_evidence():
    project=_project()
    _evidence(project,"E1",section="ПЗ",fragment="Проектное решение приведено на странице.")
    project.add_requirement(Requirement(
        requirement_id="N1",domain="normative",
        text="СП 48.13330.2019, пункт 1",
        evidence_ids=["E1"],
        evidence_level="L4",
        metadata={"verified_clause":False},
    ))
    result=VerificationEngine20(project).run()
    row=result["decision_rows"][0]
    assert row["kind"]=="SYSTEM_LIMITATION"
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_CLAUSE_NOT_VERIFIED"
    assert result["normative_checks_guarded"]==1


def test_normative_verified_clause_still_needs_semantic_route():
    project=_project()
    _evidence(project,"E1",section="ПОС",fragment="Проектом предусматривается организация строительной площадки.")
    project.add_requirement(Requirement(
        requirement_id="N1",domain="normative",
        text="СП 48.13330.2019, пункт 1",
        evidence_ids=["E1"],
        evidence_level="L4",
        metadata={"verified_clause":True},
    ))
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["automatic_verdict_eligible"] is False
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_SEMANTIC_ADJUDICATION_PENDING"


def test_equipment_project_quantity_cannot_be_used_as_volume():
    project=_project()
    _evidence(
        project,"E1",section="ТХ",
        fragment="Погрузчик — 4 шт.",
        meta={
            "evidence_kind":"EQUIPMENT_REGISTER_COMPARISON",
            "project_quantity":4,
        },
    )
    project.add_requirement(Requirement(
        requirement_id="R1",domain="assignment",
        text="Объём ковша должен составлять 4,5 м3",
        target_object_id="OBJ-1",
        expected_parameter_code="BUCKET_VOLUME",
        expected_evidence_route=["ТХ"],
        evidence_ids=["E1"],
        evidence_level="L4",
        metadata={"requirement_type":"VALUE_COMPARISON","required_value":4.5,"unit":"м3"},
    ))
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["automatic_verdict_eligible"] is False
    assert row["metadata"]["canonical_reason_code"]=="ASSIGNMENT_PROOF_ROUTE_PENDING"


def test_equipment_project_quantity_can_close_count_requirement_in_pieces():
    project=_project()
    _evidence(
        project,"E1",section="ТХ",
        fragment="Погрузчик — 4 шт.",
        meta={
            "evidence_kind":"EQUIPMENT_REGISTER_COMPARISON",
            "project_quantity":4,
        },
    )
    project.add_requirement(Requirement(
        requirement_id="R1",domain="assignment",
        text="Количество погрузчиков должно составлять 4 шт.",
        target_object_id="OBJ-1",
        expected_parameter_code="EQUIPMENT_COUNT",
        expected_evidence_route=["ТХ"],
        evidence_ids=["E1"],
        evidence_level="L4",
        metadata={"requirement_type":"VALUE_COMPARISON","required_value":4,"unit":"шт"},
    ))
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="VERIFIED_OK"
    assert row["automatic_verdict_eligible"] is True
