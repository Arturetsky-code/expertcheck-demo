from __future__ import annotations

from core20 import alpha10_reliability as a10
from core20.normative_semantic_proof import queue_fingerprint
from core.expert_review_engine import _enrich, _text
from studio.pages.checks import _as_list
from studio.pages.reports import _consensus_counts


def _packet(rid: str) -> dict:
    return {
        "packet_id": f"NORM-{rid}",
        "requirement_id": rid,
        "requirement": f"Requirement {rid}",
        "proof_type": "SEMANTIC_REQUIREMENT",
        "evidence": [{
            "evidence_id": f"E-{rid}",
            "document": "PZ.pdf",
            "page": 10,
            "text": "addressable project evidence",
        }],
    }


def _ok(state: str = "VERIFIED_OK") -> dict:
    return {
        "state": state,
        "judge_verdict": "SUPPORTS" if state == "VERIFIED_OK" else "INSUFFICIENT",
        "judge_confidence": 0.96,
        "critic_confidence": 0.93 if state == "VERIFIED_OK" else 0,
        "selected_evidence": [],
    }


def test_alpha10_removes_processed_packets_from_pending_queue():
    queue = [_packet("R1"), _packet("R2"), _packet("R3")]
    root = queue_fingerprint(queue)
    proof = {
        "rows": [
            {"requirement_id": rid, "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"}
            for rid in ("R1", "R2", "R3")
        ],
        "semantic_queue": queue,
        "semantic_queue_total": 3,
    }
    checkpoint = {
        "root_fingerprint": root,
        "fingerprint": root,
        "root_queue_total": 3,
        "queue_total": 3,
        "decisions": {
            "R1": _ok("VERIFIED_OK"),
            "R2": _ok("REVIEW_QUESTION"),
        },
    }

    result = a10.apply_normative_semantic_proof(proof, checkpoint)

    assert result["semantic_queue_full_total"] == 3
    assert result["semantic_queue_processed"] == 2
    assert result["semantic_queue_confirmed"] == 1
    assert result["semantic_queue_reviewed"] == 1
    assert result["semantic_queue_total"] == 1
    assert [row["requirement_id"] for row in result["semantic_queue"]] == ["R3"]
    assert result["semantic_proof_applied"] == 1


def test_alpha10_merges_multiple_semantic_runs_on_same_root():
    queue = [_packet("R1"), _packet("R2"), _packet("R3")]
    root = queue_fingerprint(queue)
    previous = {
        "root_fingerprint": root,
        "fingerprint": root,
        "root_queue_total": 3,
        "queue_total": 3,
        "decisions": {
            "R1": _ok("VERIFIED_OK"),
            "R2": _ok("REVIEW_QUESTION"),
        },
        "provider_errors": [],
    }

    merged = a10._merge_result(
        {"decisions": {"R3": _ok("VERIFIED_OK")}, "provider_errors": ["temporary 429"]},
        previous,
        root_fingerprint=root,
        root_total=3,
    )

    assert set(merged["decisions"]) == {"R1", "R2", "R3"}
    assert merged["processed_total"] == 3
    assert merged["verified_ok"] == 2
    assert merged["reviewed_total"] == 1
    assert merged["pending_total"] == 0
    assert merged["fingerprint"] == root
    assert merged["provider_errors"] == ["temporary 429"]


def test_alpha10_rejects_checkpoint_from_another_root_queue():
    queue = [_packet("R1"), _packet("R2")]
    proof = {
        "rows": [
            {"requirement_id": rid, "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"}
            for rid in ("R1", "R2")
        ],
        "semantic_queue": queue,
        "semantic_queue_total": 2,
    }
    stale = {
        "root_fingerprint": "another-project",
        "fingerprint": "another-project",
        "decisions": {"R1": _ok("VERIFIED_OK")},
    }

    result = a10.apply_normative_semantic_proof(proof, stale)

    assert result["semantic_queue_total"] == 2
    assert result["semantic_queue_processed"] == 0
    assert result.get("semantic_proof_stale") is True


def test_alpha10_provider_failure_does_not_consume_packet():
    queue = [_packet("R1")]
    root = queue_fingerprint(queue)
    proof = {
        "rows": [{"requirement_id": "R1", "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"}],
        "semantic_queue": queue,
        "semantic_queue_total": 1,
    }
    failed_checkpoint = {
        "root_fingerprint": root,
        "fingerprint": root,
        "root_queue_total": 1,
        "decisions": {
            "R1": {
                "state": "REVIEW_QUESTION",
                "judge_verdict": "INSUFFICIENT",
                "judge_confidence": 0,
                "critic_confidence": 0,
            }
        },
        "provider_errors": ["HTTP 429"],
    }

    result = a10.apply_normative_semantic_proof(proof, failed_checkpoint)

    assert result["semantic_queue_processed"] == 0
    assert result["semantic_queue_total"] == 1
    assert result["semantic_proof_applied"] == 0


def test_alpha10_supports_without_critic_response_stays_pending():
    queue = [_packet("R1")]
    root = queue_fingerprint(queue)
    proof = {
        "rows": [{"requirement_id": "R1", "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"}],
        "semantic_queue": queue,
        "semantic_queue_total": 1,
    }
    critic_failed = {
        "root_fingerprint": root,
        "fingerprint": root,
        "root_queue_total": 1,
        "decisions": {
            "R1": {
                "state": "REVIEW_QUESTION",
                "judge_verdict": "SUPPORTS",
                "judge_confidence": 0.96,
                "critic_confidence": 0,
            }
        },
        "provider_errors": ["Critic HTTP 429"],
    }

    result = a10.apply_normative_semantic_proof(proof, critic_failed)

    assert result["semantic_queue_processed"] == 0
    assert result["semantic_queue_total"] == 1


def test_alpha10_1_nan_identifier_is_not_literal_nan():
    row = {"comparison_id": float("nan"), "rule_id": "", "check_code": "PLAUSIBILITY-001"}
    assert _text(row, "comparison_id", "rule_id", "check_code") == "PLAUSIBILITY-001"


def test_alpha10_1_risk_escalation_is_explainable():
    risk = {
        "score": 38,
        "category": "ТЭП и межраздельные сведения",
        "object": "КПП",
        "parameter": "Высота здания",
        "parameter_code": "BUILDING_HEIGHT",
        "finding": "Требуется проверка высоты",
        "possible_remark": "Проверить высоту",
        "sources": "ПЗ",
        "origin": "CrossCheck Engine",
    }
    scenarios = [{
        "scenario_id": "HEIGHT-001",
        "title": "Высота здания",
        "category": "ТЭП и межраздельные сведения",
        "parameter_codes": ["BUILDING_HEIGHT"],
        "severity": 70,
        "recurrence": 3,
        "triggers": {"keywords": ["высота"], "statuses": []},
        "analogs": ["Проект А"],
    }]

    result = _enrich(risk, scenarios)

    assert result["level"] == "Высокий"
    assert result["risk_score_breakdown"] == {
        "source_score": 38,
        "scenario_severity": 70,
        "base_score": 70,
        "evidence_bonus": 8,
        "recurrence_bonus": 6,
        "final_score": 84,
    }
    assert "Исходная инженерная оценка 38/100" in result["risk_level_reason"]


def test_alpha10_1_report_consensus_includes_normative_semantic_proof():
    matrix, normative, total = _consensus_counts(
        {"semantic_consensus_completed": 0},
        {"semantic_proof_applied": 12},
    )
    assert matrix == 0
    assert normative == 12
    assert total == 12


def test_alpha10_1_cross_section_legacy_values_normalize_safely():
    assert _as_list(float("nan")) == []
    assert _as_list("ПЗ") == ["ПЗ"]
    assert _as_list(["ПЗ", "ПЗУ"]) == ["ПЗ", "ПЗУ"]
