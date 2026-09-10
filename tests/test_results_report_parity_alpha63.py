from __future__ import annotations

from core.report_engine import build_structured_report
from core.result_ledger import build_qualified_result_ledger
from core.result_surface import build_project_surface_rows, build_review_surface_rows
from core.review_queue import build_review_clusters


def _conflict():
    return {
        "check_code":"CORE-XSEC-AREA_BUILD-TEST",
        "category":"Межраздельная сверка",
        "check_type":"Сводная межраздельная проверка",
        "object":"Компрессорная",
        "object_id":"OBJ-1",
        "parameter_code":"AREA_BUILD",
        "parameter_name":"Площадь застройки",
        "unit":"m2",
        "status":"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ",
        "verification_evidence":[
            {
                "document":"ПЗ.pdf","page":45,"section":"ПЗ","value":54.3,
                "unit":"m2","object_id":"OBJ-1","parameter_code":"AREA_BUILD",
                "trusted_for_mismatch":True,
            },
            {
                "document":"ПЗУ.pdf","page":18,"section":"ПЗУ","value":48.7,
                "unit":"m2","object_id":"OBJ-1","parameter_code":"AREA_BUILD",
                "trusted_for_mismatch":True,
            },
        ],
        "independent_trusted_sources":2,
        "trusted_section_families":["ПЗ","ПЗУ"],
        "engineering_binding":{"parameter_expected_for_object":True},
        "dependency_diagnostics":{"owner_present":[],"control_present":[]},
        "document_values":"ПЗ: 54.3 м² | ПЗУ: 48.7 м²",
        "explanation":"Два независимых раздела содержат разные значения.",
    }




def _register_ok():
    return {
        "check_code":"GP-DOC-1",
        "parameter_code":"GP_DOCUMENT_COVERAGE",
        "parameter_name":"Сверка реестра и чертежей",
        "status":"СОВПАДАЕТ",
        "final_verification_kind":"VERIFIED_OK",
        "verification_kind":"VERIFIED_OK",
        "evidence_level":"L5",
        "proof_kind":"STRUCTURED_COMPLETENESS",
        "adversarial_state":"PASSED",
        "verification_evidence":[{"document":"ПЗУ2.pdf","page":1}],
    }


def _assignment_review():
    return {
        "requirement_id":"ASSIGN-REVIEW-1",
        "requirement":"Проверить проектное решение",
        "verification_kind":"REVIEW_QUESTION",
        "final_verification_kind":"REVIEW_QUESTION",
        "verification_state":"Требует проверки специалистом",
        "coverage_reason_code":"SPECIALIST_JUDGEMENT",
        "coverage_reason":"Требуется предметное решение специалиста.",
        "evidence_level":"L3",
        "expected_evidence_route":["ПЗ"],
    }


def test_alpha63_unified_ledger_drives_results_and_report_surfaces():
    ledger=build_qualified_result_ledger(
        assignment_rows=[_assignment_review()],
        normative_rows=[],
        checklist_rows=[],
        comparisons=[_conflict(),_register_ok()],
    )
    plan=ledger["review_plan"]
    report=build_structured_report(
        "Контрольный проект",
        [],
        ledger["comparisons"],
        checklist_results=ledger["checklist_rows"],
    )

    project_rows=build_project_surface_rows(report.get("problems") or [],plan)
    review_rows=build_review_surface_rows(report.get("problems") or [],plan)
    clusters=build_review_clusters(review_rows)

    assert len(project_rows)==1
    assert project_rows[0]["parameter_name"]=="Площадь застройки"
    assert len(review_rows)==1
    assert len(clusters)==1

    plan_items=list(plan.get("items") or [])
    assert sum(x.get("verification_kind")=="PROJECT_FINDING" for x in plan_items)==1
    assert sum(x.get("verification_kind")=="REVIEW_QUESTION" for x in plan_items)==1
    assert sum(x.get("verification_kind")=="VERIFIED_OK" for x in plan_items)==0
    assert len(ledger["register_comparisons"])==1
    assert len(ledger["engineering_comparisons"])==1
    assert ledger["verified_gate"]["blocked"]==0


def test_alpha63_ledger_does_not_mutate_results_input_payload():
    source=[_conflict()]
    ledger=build_qualified_result_ledger(comparisons=source)
    assert "final_verification_kind" not in source[0]
    assert ledger["comparisons"][0]["final_verification_kind"]=="PROJECT_FINDING"
