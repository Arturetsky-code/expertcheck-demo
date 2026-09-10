from __future__ import annotations

from core20.model import CanonicalProject, Comparison, Evidence, ProjectObject, Requirement
from core20.verification import VerificationEngine20, VerificationRequest


def _project() -> CanonicalProject:
    project = CanonicalProject(project_id="PRJ-1", name="Test")
    project.add_object(ProjectObject(object_id="OBJ-1", name="Компрессорная"))
    return project


def _trusted_evidence(project: CanonicalProject) -> None:
    project.add_evidence(Evidence(
        evidence_id="E-PZ", document_name="ПЗ.pdf", section="ПЗ", page=10,
        addressable=True, trusted=True,
        metadata={"comparison_object_id":"OBJ-1","comparison_parameter_code":"AREA_BUILD","observed_value":54.3,"observed_unit":"м2"},
    ))
    project.add_evidence(Evidence(
        evidence_id="E-PZU", document_name="ПЗУ.pdf", section="ПЗУ", page=5,
        addressable=True, trusted=True,
        metadata={"comparison_object_id":"OBJ-1","comparison_parameter_code":"AREA_BUILD","observed_value":54.3,"observed_unit":"м²"},
    ))


def test_structured_agreement_needs_two_independent_trusted_sources():
    project = _project()
    _trusted_evidence(project)
    project.add_comparison(Comparison(
        comparison_id="CMP-1",
        object_id="OBJ-1",
        parameter_code="AREA_BUILD",
        parameter_name="Площадь застройки",
        evidence_ids=["E-PZ", "E-PZU"],
        proof_kind="STRUCTURED_AGREEMENT",
        evidence_level="L5",
    ))

    result = VerificationEngine20(project).run()
    row = result["decision_rows"][0]

    assert row["kind"] == "VERIFIED_OK"
    assert row["automatic_verdict_eligible"] is True
    assert row["evidence_level"] == "L5"
    assert result["contract_errors"] == 0


def test_agreement_with_one_source_does_not_become_verified_ok():
    project = _project()
    project.add_evidence(Evidence(
        evidence_id="E-PZ", document_name="ПЗ.pdf", section="ПЗ", page=10,
        addressable=True, trusted=True,
        metadata={"comparison_object_id":"OBJ-1","comparison_parameter_code":"AREA_BUILD","observed_value":54.3,"observed_unit":"м2"},
    ))
    project.add_comparison(Comparison(
        comparison_id="CMP-1",
        object_id="OBJ-1",
        parameter_code="AREA_BUILD",
        evidence_ids=["E-PZ"],
        proof_kind="STRUCTURED_AGREEMENT",
        evidence_level="L5",
    ))

    row = VerificationEngine20(project).run()["decision_rows"][0]

    assert row["kind"] == "REVIEW_QUESTION"
    assert row["automatic_verdict_eligible"] is False


def test_confirmed_conflict_is_project_finding_but_correct_value_stays_unknown():
    project = _project()
    _trusted_evidence(project)
    project.evidence["E-PZU"].metadata["observed_value"] = 48.7
    project.add_comparison(Comparison(
        comparison_id="CMP-1",
        object_id="OBJ-1",
        parameter_code="AREA_BUILD",
        evidence_ids=["E-PZ", "E-PZU"],
        proof_kind="STRUCTURED_CONFLICT",
        conflict_confirmed=True,
        correct_value_verified=False,
        evidence_level="L5",
    ))

    row = VerificationEngine20(project).run()["decision_rows"][0]

    assert row["kind"] == "PROJECT_FINDING"
    assert row["automatic_verdict_eligible"] is True
    assert row["conflict_confirmed"] is True
    assert row["correct_value_verified"] is False


def test_missing_evidence_reference_fails_closed():
    project = _project()
    project.add_comparison(Comparison(
        comparison_id="CMP-1",
        object_id="OBJ-1",
        parameter_code="AREA_BUILD",
        evidence_ids=["E-MISSING"],
        proof_kind="STRUCTURED_AGREEMENT",
        evidence_level="L5",
    ))

    result = VerificationEngine20(project).run()
    row = result["decision_rows"][0]

    assert row["kind"] == "SYSTEM_LIMITATION"
    assert row["automatic_verdict_eligible"] is False
    assert "EVIDENCE_REF_MISSING:E-MISSING" in row["contract_violations"]
    assert result["contract_errors"] == 1


def test_requirement_without_addressable_evidence_cannot_accuse_project():
    project = _project()
    project.add_requirement(Requirement(
        requirement_id="REQ-1",
        domain="assignment",
        text="Проверить требование задания",
        target_object_id="OBJ-1",
        verification_kind="PROJECT_FINDING",
        evidence_level="L4",
    ))

    row = VerificationEngine20(project).run()["decision_rows"][0]

    assert row["kind"] == "SYSTEM_LIMITATION"
    assert row["automatic_verdict_eligible"] is False


def test_invalid_object_reference_is_contract_error():
    project = _project()
    request = VerificationRequest(
        verification_id="VER-1",
        domain="comparison",
        claim="test",
        object_id="OBJ-MISSING",
        comparison_id=None,
    )

    row = VerificationEngine20(project).verify(request)

    assert row.kind == "SYSTEM_LIMITATION"
    assert "OBJECT_REF_MISSING" in row.contract_violations
