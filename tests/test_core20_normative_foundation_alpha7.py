from __future__ import annotations

from pathlib import Path

from core20.normative_foundation import HISTORY_POLICY, NormativeKnowledgeFoundation20
from core20.legacy_adapter import Legacy18Adapter
from core20.verification import VerificationEngine20
from core20.expert_history import ExpertHistoryCorpus20


ROOT=Path(__file__).resolve().parents[1]/"knowledge"


def test_alpha7_foundation_separates_corpus_from_executable_clauses():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    summary=foundation.summary()

    assert summary["document_catalog_total"] >= 1
    assert summary["validity_registry_total"] >= summary["document_catalog_total"]
    assert summary["atomic_requirements_total"] >= 1
    assert summary["verified_clauses"] >= 1
    assert summary["verified_clauses"] <= summary["atomic_requirements_total"]
    assert summary["automatic_contract_ready"] <= summary["verified_clauses"]
    assert summary["history_policy"] == HISTORY_POLICY


def test_alpha7_pp87_verified_clause_is_trusted_but_generic_pp87_rule_is_not():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}

    verified=contracts["PP87-CLAUSE-12-PZU"]
    generic=contracts["NR-PD-001"]

    assert verified["source_verified"] is True
    assert verified["trust_state"] == "VERIFIED_CLAUSE"
    assert verified["automatic_contract_ready"] is True

    assert generic["source_verified"] is True
    assert generic["trust_state"] == "VERIFIED_DOCUMENT_CLAUSE_PENDING"
    assert generic["automatic_contract_ready"] is False


def test_alpha7_project_routing_uses_sections_and_history_only_for_priority():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    routed=foundation.project_routes([
        {"document":"Раздел ПД №2_ПЗУ1.pdf","document_type":"ПЗУ"},
        {"document":"Раздел ПД №2_ПЗУ2.pdf","document_type":"ПЗУ"},
    ])
    rows={row["requirement_id"]:row for row in routed["rows"]}

    pzu=rows["PP87-CLAUSE-12-PZU"]
    assert pzu["project_relevant"] is True
    assert pzu["project_applicability_state"] == "MATCHED_SECTION"
    assert pzu["automatic_contract_ready"] is True

    for row in routed["rows"]:
        assert row["history_policy"] == "PRIORITIZATION_ONLY"
        if row["trust_state"] != "VERIFIED_CLAUSE":
            assert row["automatic_contract_ready"] is False



def test_alpha7_production_adapter_blocks_uncurated_verified_clause():
    row={
        "requirement_id":"LAW-UNKNOWN-1",
        "knowledge_kind":"LAW_REQUIREMENT",
        "source":"СП 999.99999",
        "paragraph":"п. 1.1",
        "topic":"Синтетическая норма",
        "requirement":"Проверяемое требование.",
        "check_kind":"SEMANTIC",
        "verified_clause":True,
        "categorical_conclusion_allowed":True,
        "expected_evidence_route":["ТХ"],
        "evidence_contract":{"sections":["ТХ"],"minimum_sources":1},
        "verification_kind":"SYSTEM_LIMITATION",
        "verification_state":"Не проверено автоматически",
    }
    plan={"items":[{
        "plan_id":"LAW-UNKNOWN-1","source_id":"LAW-UNKNOWN-1",
        "domain":"НТД","domain_code":"normative","title":"СП 999.99999 п. 1.1",
        "expected_sections":["ТХ"],"verification_kind":"SYSTEM_LIMITATION",
        "verification_state":"Не проверено автоматически",
    }]}
    documents=[{
        "document":"ТХ.pdf","document_type":"ТХ","page_count":10,
        "normative_compliance_audit":[row],"project_review_plan":plan,
    }]
    project=Legacy18Adapter().build(
        project_name="Контрольный проект",
        documents=documents,findings=[],comparisons=[],assembly_rows=[],
    )
    out=VerificationEngine20(project).run()["decision_rows"][0]
    assert out["kind"]=="SYSTEM_LIMITATION"
    assert out["metadata"]["canonical_reason_code"]=="NORMATIVE_CLAUSE_NOT_VERIFIED"
    assert out["metadata"]["normative_registry_trust"]=="SOURCE_NOT_CURATED"



def test_alpha7_real_expert_history_is_read_only_training_signal():
    history=ExpertHistoryCorpus20(ROOT)
    summary=history.summary()
    assert summary["projects"] >= 1
    assert summary["records"] >= 1
    assert summary["records_with_response"] >= 1
    assert summary["usage_policy"]=="PRIORITIZATION_AND_ANALOGS_ONLY"
    patterns=history.top_patterns(limit=5)
    assert patterns
    assert all(x["history_policy"]=="PRIORITIZATION_AND_ANALOGS_ONLY" for x in patterns)


def test_alpha7_first_normative_wave_384_and_gost27751_is_curated():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}

    for requirement_id in (
        "FZ384-4-1-ID-FEATURES",
        "FZ384-4-7-RESP-LEVEL",
        "FZ384-4-11-ID-IN-ASSIGNMENT-PD",
        "FZ384-15-2-RESP-INPUT",
        "FZ384-15-5.1-SAFETY-JUSTIFICATION",
        "GOST27751-10.1-CLASS-LEVEL-GAMMA",
        "GOST27751-10.2-ASSIGNMENT",
    ):
        row=contracts[requirement_id]
        assert row["source_verified"] is True
        assert row["trust_state"] == "VERIFIED_CLAUSE"
        assert row["automatic_contract_ready"] is True

    gost=foundation.documents_by_id["GOST-27751-2014"]
    assert gost["source_class"] == "official"
    assert gost["validity_canonical_id"] == "GOST:27751-2014"


def test_alpha7_second_normative_wave_fire_package_is_curated():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}

    for requirement_id in (
        "FZ123-27-3-CATEGORY-BASIS",
        "FZ123-27-22-CATEGORY-IN-PD",
        "FZ123-78-1-FIRE-CHARACTERISTICS",
        "FZ123-92-2-PRODUCTION-FIRE-SECTION",
        "SP12-4.1-CATEGORY-TAXONOMY",
        "SP12-4.2-CATEGORY-INPUTS",
        "SP12-5.2-SEQUENTIAL-CATEGORY",
        "SP4-6.1.2-PRODUCTION-FIRE-DISTANCE",
        "SP4-8.2.1-FIRE-ACCESS-SIDES",
        "SP4-8.2.3-FIRE-ROAD-WIDTH",
        "SP4-8.2.6-ROAD-WALL-DISTANCE",
    ):
        row=contracts[requirement_id]
        assert row["source_verified"] is True
        assert row["trust_state"] == "VERIFIED_CLAUSE"
        assert row["automatic_contract_ready"] is True

    assert foundation.documents_by_id["123-FZ"]["status"] == "Действует с изменениями"
    assert foundation.documents_by_id["SP-4.13130.2013"]["status"] == "Действует"
    assert foundation.documents_by_id["SP-12.13130.2009"]["status"] == "Действует"
