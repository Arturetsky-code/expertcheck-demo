from __future__ import annotations

from core.review_planner import build_review_plan
from core20.legacy_adapter import Legacy18Adapter
from core20.verification import VerificationEngine20


def _normative_row():
    return {
        "requirement_id":"PP87-CLAUSE-12-PZU",
        "knowledge_kind":"LAW_REQUIREMENT",
        "source":"Постановление Правительства РФ от 16.02.2008 № 87",
        "paragraph":"п. 12",
        "topic":"Состав раздела ПЗУ",
        "requirement":"Раздел 2 ПЗУ должен содержать текстовую и графическую части.",
        "check_kind":"STRUCTURE",
        "verified_clause":True,
        "categorical_conclusion_allowed":True,
        "evidence_contract":{
            "minimum_sources":1,
            "requires_page_reference":True,
            "sections":["ПЗУ"],
        },
        "verification_kind":"SYSTEM_LIMITATION",
        "verification_state":"Не проверено автоматически",
    }


def test_normative_review_plan_preserves_profile_sections():
    row=_normative_row()
    plan=build_review_plan(normative_rows=[row])
    item=plan["checks"][0]
    assert item["domain"]=="normative"
    assert item["expected_sections"]==["ПЗУ"]


def test_adapter_preserves_normative_route_from_contract_sections():
    row=_normative_row()
    plan=build_review_plan(normative_rows=[row])
    documents=[
        {
            "document":"Раздел ПД №2_ПЗУ1.pdf",
            "document_type":"ПЗУ",
            "page_count":20,
            "project_review_plan":{"items":plan["checks"]},
            "normative_compliance_audit":[row],
        },
        {
            "document":"Раздел ПД №2_ПЗУ2.pdf",
            "document_type":"ПЗУ",
            "page_count":8,
        },
    ]
    project=Legacy18Adapter().build(
        project_name="Независимый проект",
        documents=documents,
        findings=[],
        comparisons=[],
        assembly_rows=[],
    )
    requirement=project.requirements["PP87-CLAUSE-12-PZU"]
    assert requirement.expected_evidence_route==["ПЗУ"]


def test_alpha61_end_to_end_pp87_pzu_route_reaches_structure_proof():
    row=_normative_row()
    plan=build_review_plan(normative_rows=[row])
    documents=[
        {
            "document":"Раздел ПД №2_ПЗУ1.pdf",
            "document_type":"ПЗУ",
            "page_count":20,
            "project_review_plan":{"items":plan["checks"]},
            "normative_compliance_audit":[row],
        },
        {
            "document":"Раздел ПД №2_ПЗУ2.pdf",
            "document_type":"ПЗУ",
            "page_count":8,
        },
    ]
    project=Legacy18Adapter().build(
        project_name="Независимый проект",
        documents=documents,
        findings=[],
        comparisons=[],
        assembly_rows=[],
    )
    row_out=VerificationEngine20(project).run()["decision_rows"][0]
    assert row_out["kind"]=="VERIFIED_OK"
    assert row_out["automatic_verdict_eligible"] is True
    assert row_out["metadata"]["applicability_state"]=="APPLICABLE_BY_SECTION"
    assert row_out["metadata"]["canonical_reason_code"]=="NORMATIVE_STRUCTURE_VERIFIED"
