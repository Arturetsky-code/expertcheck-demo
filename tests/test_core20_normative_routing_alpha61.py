from __future__ import annotations

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
        "expected_evidence_route":["ПЗУ"],
        "evidence_contract":{
            "minimum_sources":1,
            "requires_page_reference":True,
            "sections":["ПЗУ"],
            "expected_sections":["ПЗУ"],
        },
        "verification_kind":"SYSTEM_LIMITATION",
        "verification_state":"Не проверено автоматически",
    }


def _plan():
    return {
        "items":[{
            "plan_id":"PP87-CLAUSE-12-PZU",
            "source_id":"PP87-CLAUSE-12-PZU",
            "domain":"normative",
            "domain_code":"normative",
            "check":"Постановление Правительства РФ от 16.02.2008 № 87 п. 12",
            "method":"STRUCTURE",
            "expected_sections":["ПЗУ"],
            "verification_kind":"SYSTEM_LIMITATION",
            "verification_state":"Не проверено автоматически",
        }]
    }


def _documents():
    row=_normative_row()
    return [
        {
            "document":"Раздел ПД №2_ПЗУ1.pdf",
            "document_type":"ПЗУ",
            "page_count":20,
            "project_review_plan":_plan(),
            "normative_compliance_audit":[row],
        },
        {
            "document":"Раздел ПД №2_ПЗУ2.pdf",
            "document_type":"ПЗУ",
            "page_count":8,
        },
    ]


def test_adapter_preserves_normative_route_from_explicit_contract():
    project=Legacy18Adapter().build(
        project_name="Независимый проект",
        documents=_documents(),
        findings=[],
        comparisons=[],
        assembly_rows=[],
    )
    requirement=project.requirements["PP87-CLAUSE-12-PZU"]
    assert requirement.expected_evidence_route==["ПЗУ"]


def test_adapter_falls_back_to_normative_contract_sections():
    documents=_documents()
    documents[0]["normative_compliance_audit"][0].pop("expected_evidence_route",None)
    documents[0]["normative_compliance_audit"][0]["evidence_contract"].pop("expected_sections",None)
    documents[0]["project_review_plan"]["items"][0]["expected_sections"]=[]
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
    project=Legacy18Adapter().build(
        project_name="Независимый проект",
        documents=_documents(),
        findings=[],
        comparisons=[],
        assembly_rows=[],
    )
    row_out=VerificationEngine20(project).run()["decision_rows"][0]
    assert row_out["kind"]=="VERIFIED_OK"
    assert row_out["automatic_verdict_eligible"] is True
    assert row_out["metadata"]["applicability_state"]=="APPLICABLE_BY_SECTION"
    assert row_out["metadata"]["canonical_reason_code"]=="NORMATIVE_STRUCTURE_VERIFIED"
