from __future__ import annotations

from core20.model import CanonicalProject, Comparison, Evidence, ProjectObject
from core20.verification import VerificationEngine20


def _base() -> CanonicalProject:
    project=CanonicalProject(project_id="PRJ-A3",name="Alpha 3")
    project.add_object(ProjectObject(object_id="OBJ-1",name="Компрессорная"))
    return project


def _evidence(project, eid, section, value, unit="м2"):
    project.add_evidence(Evidence(
        evidence_id=eid,document_name=f"{section}.pdf",section=section,page=1,
        addressable=True,trusted=True,
        metadata={
            "comparison_object_id":"OBJ-1",
            "comparison_parameter_code":"AREA_BUILD",
            "observed_value":value,
            "observed_unit":unit,
        },
    ))


def test_alpha3_legacy_ok_cannot_hide_canonical_conflict():
    project=_base()
    _evidence(project,"E1","ПЗ",54.3)
    _evidence(project,"E2","ПЗУ",48.7)
    project.add_comparison(Comparison(
        comparison_id="C1",object_id="OBJ-1",parameter_code="AREA_BUILD",
        unit="м2",evidence_ids=["E1","E2"],proof_kind="STRUCTURED_AGREEMENT",
        conflict_confirmed=False,metadata={"verification_kind":"VERIFIED_OK"},
    ))
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="PROJECT_FINDING"
    assert row["metadata"]["proof_source"]=="CANONICAL_RECOMPUTED"
    assert row["metadata"]["legacy_disagreement"] is True
    assert row["correct_value_verified"] is False


def test_alpha3_incompatible_units_fail_closed():
    project=_base()
    _evidence(project,"E1","ПЗ",54.3,"м2")
    _evidence(project,"E2","ПЗУ",54.3,"м3")
    project.add_comparison(Comparison(
        comparison_id="C1",object_id="OBJ-1",parameter_code="AREA_BUILD",
        unit="м2",evidence_ids=["E1","E2"],proof_kind="STRUCTURED_AGREEMENT",
    ))
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["automatic_verdict_eligible"] is False
    assert row["metadata"]["canonical_reason_code"]=="UNIT_CONTRACT_MISMATCH"


def test_alpha3_same_value_unit_aliases_recompute_agreement():
    project=_base()
    _evidence(project,"E1","ПЗ",89.9,"м²")
    _evidence(project,"E2","ПЗУ",89.9,"м2")
    project.add_comparison(Comparison(
        comparison_id="C1",object_id="OBJ-1",parameter_code="AREA_BUILD",
        unit="м2",evidence_ids=["E1","E2"],proof_kind="",
    ))
    result=VerificationEngine20(project).run()
    row=result["decision_rows"][0]
    assert row["kind"]=="VERIFIED_OK"
    assert result["canonical_proofs_recomputed"]==1
