from __future__ import annotations

import json

from core.workspace_store import session_snapshot
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
            "semantic_proof_applied": 7,
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
                    "rows": [{"requirement_id": "SECRET", "fragment": "project text"}],
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
    assert diagnostic["review_questions"] == 46
    assert diagnostic["evidence_coverage_pct"] == 78.1
    assert diagnostic["blocker_counts"]["SEMANTIC_PENDING"] == 26
    assert diagnostic["semantic_pending"]["by_source"]["ПП №87"] == 12
    assert diagnostic["retained_fail_closed"]["by_reason"]["NORMATIVE_APPLICABILITY_NOT_PROVEN"] == 4

    serialized = json.dumps(diagnostic, ensure_ascii=False)
    assert "project text" not in serialized
    assert "project-sensitive text" not in serialized
    assert "fragment" not in serialized
    assert "rows" not in serialized


def test_workspace_snapshot_includes_compact_diagnostic():
    diagnostic = compact_normative_diagnostic(_manifest())
    payload = session_snapshot({
        "project_name": "Тест",
        "canonical_core_20_diagnostic": diagnostic,
    })

    assert payload["canonical_core_20_diagnostic"]["active_contracts"] == 64
    assert payload["canonical_core_20_diagnostic"]["semantic_queue_total"] == 26
