from __future__ import annotations

from core.project_review_planner import build_review_plan


def test_results_planner_accepts_nan_comparison_service_fields():
    nan=float("nan")
    comparison={
        "check_code":"CORE-XSEC-TEST",
        "object":"Компрессорная",
        "parameter_code":"AREA_BUILD",
        "parameter_name":"Площадь застройки",
        "unit":"m2",
        "status":"Требует проверки",
        "verification_evidence":nan,
        "source_records":nan,
        "dependency_diagnostics":nan,
        "cross_section_gate_reasons":nan,
        "verified_core_gate_reasons":nan,
        "data_owner_sections":nan,
        "dependent_sections":nan,
        "evidence_level":nan,
    }
    plan=build_review_plan(comparisons=[comparison])
    assert plan["total"]==1
    item=plan["items"][0]
    assert item["domain_code"]=="comparison"
    assert item["evidence_candidate_count"]==0
    assert item["expected_sections"]==[]
    assert item["verified_core_gate_reasons"]==[]
    assert item["evidence_level"]=="L0"
