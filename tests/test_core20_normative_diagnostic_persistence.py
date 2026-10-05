from __future__ import annotations

import json

from core.workspace_store import _normative_diagnostic_changed, session_snapshot, snapshot_signature
from core20.dual_run import compact_normative_diagnostic


def _manifest():
    return {
        "version": "20.0-test",
        "normative_execution": {
            "registered_contracts": 66,
            "active_contracts": 64,
            "inactive_triggered_contracts": 2,
            "verified_ok": 15,
            "project_findings": 0,
            "review_questions": 46,
            "system_limitations": 3,
            "demoted_keyword_only_remaining": 40,
            "semantic_queue_total": 26,
            "semantic_completed_total": 8,
            "semantic_reviewed_no_promotion": 1,
            "semantic_proof_applied": 7,
            "semantic_run": {
                "version": "20.0-alpha10.1-quality-integrity",
                "selected_this_run": 24,
                "pending_before_run": 30,
                "processed_total": 8,
                "completed_before": 4,
                "new_decisions": 4,
                "verified_ok": 7,
                "newly_verified_ok": 3,
                "reviewed_total": 1,
                "pending_total": 22,
                "provider_error_count": 5,
                "provider_error_categories": {"RATE_LIMIT": 3, "TIMEOUT": 2},
                "contract_gate_blocked": 1,
                "decisions": [{
                    "requirement_id": "SP8-TEST",
                    "state": "REVIEW_QUESTION",
                    "judge_verdict": "SUPPORTS",
                    "critic_accept": True,
                    "independent": True,
                    "semantic_contract_configured": True,
                    "semantic_contract_ready": False,
                    "semantic_contract_missing_groups": ["APPLIED_NORMATIVE_BASIS"],
                    "blocker": "SEMANTIC_CONTRACT_GATE",
                    "reason": "project-sensitive model explanation",
                }],
            },
            "set_completeness_queue_total": 3,
            "visual_queue_total": 2,
            "evidence_coverage_pct": 78.1,
            "proof_frontier": {
                "blocker_counts": {
                    "SEMANTIC_PENDING": 26,
                    "SET_COMPLETENESS_REQUIRED": 3,
                    "VISUAL_PROOF_REQUIRED": 2,
                },
                "semantic_pending": {
                    "total": 26,
                    "by_source": {"ПП №87": 12, "СП 4.13130.2013": 4},
                    "by_section": {"ПЗУ": 9, "АР": 5},
                    "by_evidence_candidates": {"0": 6, "4+": 8},
                    "by_retrieval_admission": {"STRICT_RETRIEVAL": 18, "STRONG_NEAR_MISS": 8},
                    "rows": [{
                        "requirement_id": "PP87-TEST-01",
                        "source": "ПП №87",
                        "paragraph": "п. 12",
                        "sections": "ПЗУ",
                        "topic": "Состав ПЗУ",
                        "retrieval_admission": "STRICT_RETRIEVAL",
                        "retrieval_candidate_count": 4,
                        "fragment": "project text",
                    }],
                },
                "set_completeness": {
                    "total": 3,
                    "by_source": {"ПП №87": 3},
                    "by_section": {"ИОС": 3},
                    "rows": [{"requirement_id": "SET-X", "evidence": [{"fragment": "secret"}]}],
                },
                "visual_pending": {
                    "total": 2,
                    "by_kind": {"AR_FLOOR_PLANS": 2},
                    "by_section": {"АР": 2},
                    "rows": [{"candidate_pages": [{"fragment": "secret"}]}],
                },
                "retained_fail_closed": {
                    "total": 4,
                    "by_reason": {"NORMATIVE_APPLICABILITY_NOT_PROVEN": 4},
                    "by_source": {"СП 4.13130.2013": 4},
                    "by_section": {"ПЗУ": 4},
                    "rows": [{"reason": "project-sensitive text"}],
                },
            },
        },
    }


def test_compact_normative_diagnostic_keeps_counts_not_project_text():
    diagnostic = compact_normative_diagnostic(_manifest())

    assert diagnostic["registered_contracts"] == 66
    assert diagnostic["active_contracts"] == 64
    assert diagnostic["inactive_triggered_contracts"] == 2
    assert diagnostic["verified_ok"] == 15
    assert diagnostic["held_by_proof_control"] == 40
    assert diagnostic["semantic_queue_total"] == 26
    assert diagnostic["semantic_completed_total"] == 8
    assert diagnostic["semantic_reviewed_no_promotion"] == 1
    assert diagnostic["review_questions"] == 46
    assert diagnostic["semantic_run"]["selected_this_run"] == 24
    assert diagnostic["semantic_run"]["provider_error_count"] == 5
    assert diagnostic["semantic_run"]["provider_error_categories"] == {"RATE_LIMIT": 3, "TIMEOUT": 2}
    assert diagnostic["semantic_run"]["decisions"] == [{
        "requirement_id": "SP8-TEST",
        "state": "REVIEW_QUESTION",
        "judge_verdict": "SUPPORTS",
        "critic_accept": True,
        "independent": True,
        "semantic_contract_configured": True,
        "semantic_contract_ready": False,
        "semantic_contract_missing_groups": ["APPLIED_NORMATIVE_BASIS"],
        "blocker": "SEMANTIC_CONTRACT_GATE",
    }]
    assert diagnostic["evidence_coverage_pct"] == 78.1
    assert diagnostic["blocker_counts"]["SEMANTIC_PENDING"] == 26
    assert diagnostic["semantic_pending"]["by_source"]["ПП №87"] == 12
    assert diagnostic["retained_fail_closed"]["by_reason"]["NORMATIVE_APPLICABILITY_NOT_PROVEN"] == 4
    assert diagnostic["semantic_pending"]["rows"] == [{
        "requirement_id": "PP87-TEST-01",
        "source": "ПП №87",
        "paragraph": "п. 12",
        "sections": "ПЗУ",
        "topic": "Состав ПЗУ",
        "retrieval_admission": "STRICT_RETRIEVAL",
        "retrieval_candidate_count": 4,
    }]

    serialized = json.dumps(diagnostic, ensure_ascii=False)
    assert "project text" not in serialized
    assert "project-sensitive text" not in serialized
    assert "fragment" not in serialized
    assert "candidate_pages" not in serialized
    assert "project-sensitive model explanation" not in serialized


def test_workspace_snapshot_includes_compact_diagnostic():
    diagnostic = compact_normative_diagnostic(_manifest())
    payload = session_snapshot({
        "project_name": "Тест",
        "canonical_core_20_diagnostic": diagnostic,
    })

    assert payload["canonical_core_20_diagnostic"]["active_contracts"] == 64
    assert payload["canonical_core_20_diagnostic"]["semantic_queue_total"] == 26


def test_compact_diagnostic_changes_workspace_signature():
    base = session_snapshot({
        "project_name": "Тест",
        "analysis_time": "2026-10-05T12:00:00+03:00",
        "canonical_core_20_diagnostic": {},
    })
    enriched = session_snapshot({
        "project_name": "Тест",
        "analysis_time": "2026-10-05T12:00:00+03:00",
        "canonical_core_20_diagnostic": compact_normative_diagnostic(_manifest()),
    })

    assert snapshot_signature(base) != snapshot_signature(enriched)



def test_history_backfill_refreshes_when_diagnostic_version_or_content_changes():
    old={"normative_diagnostic":{"version":"1.0","semantic_queue_total":47}}
    upgraded={"version":"1.1","semantic_queue_total":47,"semantic_pending":{"rows":[{"requirement_id":"R1"}]}}
    same=dict(upgraded)

    assert _normative_diagnostic_changed(old,upgraded) is True
    assert _normative_diagnostic_changed({"normative_diagnostic":same},upgraded) is False
    assert _normative_diagnostic_changed({},upgraded) is True
