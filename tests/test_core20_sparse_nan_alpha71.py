from __future__ import annotations

from core20.legacy_adapter import Legacy18Adapter
from core20.verification import VerificationEngine20


def test_alpha71_sparse_nan_cells_do_not_break_canonical_migration():
    nan=float("nan")
    normative={
        "requirement_id":"LAW-NAN-001",
        "knowledge_kind":"LAW_REQUIREMENT",
        "source":"СП 999.99999",
        "document_id":nan,
        "paragraph":"п. 1.1",
        "topic":"Контроль sparse cells",
        "requirement":"Проверяемое требование.",
        "check_kind":"SEMANTIC",
        "verified_clause":True,
        "categorical_conclusion_allowed":True,
        "expected_evidence_route":["ТХ"],
        "applicability":nan,
        "evidence_contract":nan,
        "structural_check":nan,
        "verification_evidence":nan,
        "verification_kind":"SYSTEM_LIMITATION",
        "verification_state":"Не проверено автоматически",
    }
    plan={"items":[{
        "plan_id":"LAW-NAN-001",
        "source_id":"LAW-NAN-001",
        "domain":"НТД",
        "domain_code":"normative",
        "title":"СП 999.99999 п. 1.1",
        "expected_sections":["ТХ"],
        "verification_kind":"SYSTEM_LIMITATION",
        "verification_state":"Не проверено автоматически",
    }]}
    documents=[{
        "document":"ТХ.pdf",
        "document_type":"ТХ",
        "page_count":10,
        "consolidated_registry":nan,
        "composition_baseline":[],
        "project_review_plan":plan,
        "assignment_compliance":nan,
        "normative_compliance_audit":[normative],
        "analysis_snapshot":{"page_corpus":nan},
    }]
    project=Legacy18Adapter().build(
        project_name="Sparse NaN",
        documents=documents,
        findings=[],
        comparisons=[],
        assembly_rows=[],
    )
    result=VerificationEngine20(project).run()
    assert result["decisions"]==1
    row=result["decision_rows"][0]
    assert row["kind"]=="SYSTEM_LIMITATION"
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_CLAUSE_NOT_VERIFIED"
