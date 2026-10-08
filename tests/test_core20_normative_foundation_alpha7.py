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


def test_alpha7_third_normative_wave_mining_lighting_site_is_curated():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}

    for requirement_id in (
        "FNP505-1184-CONVEYOR-GALLERY-FIRE",
        "FNP505-1215-CONVEYOR-CROSSING-SPACING",
        "FNP505-1461-SURFACE-EMERGENCY-LIGHTING",
        "SP52-7.6.1-EMERGENCY-LIGHTING-POWER",
        "SP52-7.6.3-EVACUATION-LIGHTING",
        "SP18-5.37-ENTRANCE-GATE-WIDTH",
        "SP18-5.52-CLOSED-STORM-SEWER",
    ):
        row=contracts[requirement_id]
        assert row["source_verified"] is True
        assert row["trust_state"] == "VERIFIED_CLAUSE"
        assert row["automatic_contract_ready"] is True

    assert foundation.documents_by_id["FNP-MINING"]["status"] == "Действует с изменениями"
    assert foundation.documents_by_id["SP-52.13330.2016"]["status"] == "Действует"
    assert foundation.documents_by_id["SP-18.13330.2019"]["status"] == "Действует"


def test_alpha7_fourth_normative_wave_engineering_fire_water_is_curated():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}

    for requirement_id in (
        "SP6-2025-5.2-SPZ-RELIABILITY",
        "SP6-2025-5.3-SPZ-PANEL",
        "SP8-9.2-WATER-SYSTEM-FIRE-VOLUME",
        "SP8-9.5-WATER-SYSTEM-RESERVOIRS",
        "SP8-11.5-FIRE-WATER-LEVEL",
        "SP10-1.4-VPV-EXEMPTION",
        "SP10-T7.2-PRODUCTION-FLOW",
    ):
        row=contracts[requirement_id]
        assert row["source_verified"] is True
        assert row["trust_state"] == "VERIFIED_CLAUSE"
        assert row["automatic_contract_ready"] is True

    assert foundation.documents_by_id["SP-6.13130.2025"]["status"] == "Действует"
    assert foundation.documents_by_id["SP-8.13130.2020"]["status"] == "Действует"
    assert foundation.documents_by_id["SP-10.13130.2020"]["status"] == "Действует"
def test_alpha7_executable_ntd_coverage_is_reported_separately_from_verification():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    summary=foundation.summary()

    assert summary["atomic_requirements_total"] == 104
    assert summary["verified_clauses"] == 75
    assert summary["executable_contracts"] == 73
    assert summary["executable_verified_coverage_pct"] == 97.3
    assert summary["executable_total_coverage_pct"] == 70.2

    assert summary["hardened_executable_contracts"] == 71
    assert summary["hardened_verified_coverage_pct"] == 94.7
    assert summary["hardened_total_coverage_pct"] == 68.3

    assert summary["generic_semantic_executable_contracts"] == 2
    assert summary["executable_triggered_only_contracts"] == 9
    assert sum(summary["executable_by_proof_type"].values()) == 73

    blockers={
        row["requirement_id"]:row["reason_code"]
        for row in summary["executable_blockers"]
    }
    assert blockers == {
        "PP87-CLAUSE-15-IOS":"SET_CONTRACT_HOLD_ONLY",
        "SP52-7.6.3-EVACUATION-LIGHTING":"SET_CONTRACT_HOLD_ONLY",
    }


def test_alpha7_executable_ntd_contract_tiers_distinguish_generic_hardened_and_blocked():
    foundation=NormativeKnowledgeFoundation20(ROOT)
    contracts={row["requirement_id"]:row for row in foundation.contracts()}

    generic=contracts["FZ123-78-1-FIRE-CHARACTERISTICS"]
    assert generic["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert generic["executable_contract_ready"] is True
    assert generic["hardened_proof_ready"] is False
    assert generic["execution_tier"] == "GENERIC_SEMANTIC"

    hardened=contracts["FZ384-15-5.1-SAFETY-JUSTIFICATION"]
    assert hardened["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert hardened["executable_contract_ready"] is True
    assert hardened["hardened_proof_ready"] is True
    assert hardened["execution_tier"] == "HARDENED"

    for requirement_id in (
        "SP8-9.2-WATER-SYSTEM-FIRE-VOLUME",
        "SP8-9.5-WATER-SYSTEM-RESERVOIRS",
        "SP8-11.5-FIRE-WATER-LEVEL",
    ):
        row=contracts[requirement_id]
        semantic=row["evidence_contract"]["semantic_proof_contract"]
        assert row["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
        assert row["executable_contract_ready"] is True
        assert row["hardened_proof_ready"] is True
        assert row["execution_tier"] == "HARDENED"
        assert semantic["version"] == "2.0"
        assert semantic["required_groups"]

    article31=contracts["FZ123-31-1-CONSTRUCTIVE-FIRE-HAZARD-TAXONOMY"]
    article31_semantic=article31["evidence_contract"]["semantic_proof_contract"]
    assert article31["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert article31["executable_contract_ready"] is True
    assert article31["hardened_proof_ready"] is True
    assert article31["execution_tier"] == "HARDENED"
    assert article31_semantic["version"] == "2.0"
    assert article31_semantic["required_groups"][0]["id"] == "CONSTRUCTIVE_FIRE_HAZARD_CLASS_DECLARATION"

    article30=contracts["FZ123-30-1-FIRE-RESISTANCE-TAXONOMY"]
    article30_semantic=article30["evidence_contract"]["semantic_proof_contract"]
    assert article30["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert article30["executable_contract_ready"] is True
    assert article30["hardened_proof_ready"] is True
    assert article30["execution_tier"] == "HARDENED"
    assert article30_semantic["version"] == "2.0"
    assert article30_semantic["required_groups"][0]["id"] == "FIRE_RESISTANCE_CLASS_DECLARATION"
    assert article30_semantic["required_groups"][0]["regex_any_of"]

    article32=contracts["FZ123-32-1-FUNCTIONAL-FIRE-HAZARD-TAXONOMY"]
    article32_semantic=article32["evidence_contract"]["semantic_proof_contract"]
    assert article32["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert article32["executable_contract_ready"] is True
    assert article32["hardened_proof_ready"] is True
    assert article32["execution_tier"] == "HARDENED"
    assert article32_semantic["version"] == "2.0"
    assert article32_semantic["required_groups"][0]["id"] == "FUNCTIONAL_FIRE_CLASS_WITH_PURPOSE"
    assert article32_semantic["required_groups"][0]["regex_any_of"]

    article61=contracts["FZ123-61-3-AUPT-SELECTION-BASIS"]
    article61_semantic=article61["evidence_contract"]["semantic_proof_contract"]
    assert article61["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert article61["executable_contract_ready"] is True
    assert article61["hardened_proof_ready"] is True
    assert article61["execution_tier"] == "HARDENED"
    assert article61_semantic["version"] == "2.0"
    assert {group["id"] for group in article61_semantic["required_groups"]} == {
        "AUPT_SELECTION_SOLUTION",
        "AUPT_COMBUSTIBLE_BASIS",
        "AUPT_PLANNING_BASIS",
        "AUPT_ENVIRONMENT_BASIS",
    }

    article58=contracts["FZ123-58-2-FIRE-RESISTANCE-LIMITS"]
    article58_semantic=article58["evidence_contract"]["semantic_proof_contract"]
    assert article58["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert article58["executable_contract_ready"] is True
    assert article58["hardened_proof_ready"] is True
    assert article58["execution_tier"] == "HARDENED"
    assert article58_semantic["version"] == "2.0"
    assert {group["id"] for group in article58_semantic["required_groups"]} == {
        "FIRE_RESISTANCE_DEGREE_BASIS",
        "CONSTRUCTION_FIRE_RESISTANCE_LIMIT",
    }

    article57=contracts["FZ123-57-1-CONSTRUCTION-FIRE-PERFORMANCE"]
    article57_semantic=article57["evidence_contract"]["semantic_proof_contract"]
    assert article57["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert article57["executable_contract_ready"] is True
    assert article57["hardened_proof_ready"] is True
    assert article57["execution_tier"] == "HARDENED"
    assert article57_semantic["version"] == "2.0"
    assert {group["id"] for group in article57_semantic["required_groups"]} == {
        "FIRE_RESISTANCE_DEGREE_DECLARATION",
        "CONSTRUCTIVE_FIRE_HAZARD_CLASS_DECLARATION",
        "CONSTRUCTION_FIRE_RESISTANCE_LIMIT_DECLARATION",
        "CONSTRUCTION_FIRE_HAZARD_CLASS_DECLARATION",
    }

    article104=contracts["FZ123-104-1-AUPT-SUPPRESSION-METHOD"]
    article104_semantic=article104["evidence_contract"]["semantic_proof_contract"]
    assert article104["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert article104["executable_contract_ready"] is True
    assert article104["hardened_proof_ready"] is True
    assert article104["execution_tier"] == "HARDENED"
    assert article104_semantic["version"] == "2.0"
    assert article104_semantic["required_groups"][0]["id"] == "AUPT_SUPPRESSION_METHOD_DECLARATION"

    sp12=contracts["SP12-4.1-CATEGORY-TAXONOMY"]
    sp12_semantic=sp12["evidence_contract"]["semantic_proof_contract"]
    assert sp12["resolved_proof_type"] == "SEMANTIC_REQUIREMENT"
    assert sp12["executable_contract_ready"] is True
    assert sp12["hardened_proof_ready"] is True
    assert sp12["execution_tier"] == "HARDENED"
    assert sp12_semantic["version"] == "2.0"
    assert sp12_semantic["required_groups"][0]["id"] == "SP12_CATEGORY_TYPED_DECLARATION"
    assert len(sp12_semantic["required_groups"][0]["regex_any_of"]) == 3

    blocked=contracts["PP87-CLAUSE-15-IOS"]
    assert blocked["resolved_proof_type"] == "SET_COMPLETENESS"
    assert blocked["executable_contract_ready"] is False
    assert blocked["hardened_proof_ready"] is False
    assert blocked["executable_blocker_reason"] == "SET_CONTRACT_HOLD_ONLY"
