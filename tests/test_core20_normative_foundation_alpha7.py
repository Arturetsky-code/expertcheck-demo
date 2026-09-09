from __future__ import annotations

from pathlib import Path

from core20.normative_foundation import HISTORY_POLICY, NormativeKnowledgeFoundation20


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
