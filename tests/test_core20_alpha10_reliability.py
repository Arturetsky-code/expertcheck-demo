from __future__ import annotations

from core20 import alpha10_reliability as a10
from core20 import normative_semantic_proof as semantic
from core20.normative_semantic_proof import queue_fingerprint
from core20.quality_integrity import as_list, consensus_counts
from core.expert_review_engine import _enrich, _text


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
    selected = []
    if state == "VERIFIED_OK":
        selected = [{
            "evidence_id": "E-R1",
            "document": "PZ.pdf",
            "page": 10,
            "source_locator": "PZ.pdf, стр. 10",
            "fragment": "addressable project evidence",
        }]
    return {
        "state": state,
        "judge_verdict": "SUPPORTS" if state == "VERIFIED_OK" else "INSUFFICIENT",
        "judge_confidence": 0.96,
        "critic_confidence": 0.93 if state == "VERIFIED_OK" else 0,
        "selected_evidence": selected,
    }


def _selected_ok(packet: dict, state: str = "VERIFIED_OK") -> dict:
    decision = _ok(state)
    if state != "VERIFIED_OK":
        return decision
    decision["packet_fingerprint"] = semantic._packet_fingerprint(packet)
    decision["requirement_fingerprint"] = semantic._requirement_fingerprint(packet)
    decision["selected_proof_fingerprint"] = semantic._selected_proof_fingerprint(
        packet,
        decision["selected_evidence"],
    )
    return decision



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
    confirmed = next(row for row in result["rows"] if row["requirement_id"] == "R1")
    assert confirmed["evidence_document"] == "PZ.pdf"
    assert confirmed["evidence_page"] == 10
    assert confirmed["canonical_evidence_source"] == "SEMANTIC_SELECTED_EVIDENCE"


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
    matrix, normative, total = consensus_counts(
        {"semantic_consensus_completed": 0},
        {"semantic_proof_applied": 12},
    )
    assert matrix == 0
    assert normative == 12
    assert total == 12


def test_alpha10_1_cross_section_legacy_values_normalize_safely():
    assert as_list(float("nan")) == []
    assert as_list("ПЗ") == ["ПЗ"]
    assert as_list(["ПЗ", "ПЗУ"]) == ["ПЗ", "ПЗУ"]


def test_alpha10_queue_root_change_keeps_reusable_selected_evidence_processed():
    old_packet = _packet("R1")
    old_queue = [old_packet, _packet("R2")]
    old_root = queue_fingerprint(old_queue)

    current_r1 = _packet("R1")
    current_r1["evidence"].append({
        "evidence_id": "E-R1-ALT",
        "document": "KR.pdf",
        "page": 24,
        "text": "alternative addressable project evidence",
    })
    current_queue = [current_r1, _packet("R2")]
    current_root = queue_fingerprint(current_queue)
    assert current_root != old_root

    proof = {
        "rows": [
            {"requirement_id": rid, "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"}
            for rid in ("R1", "R2")
        ],
        "semantic_queue": current_queue,
        "semantic_queue_total": 2,
    }
    checkpoint = {
        "root_fingerprint": old_root,
        "fingerprint": old_root,
        "root_queue_total": 2,
        "queue_total": 2,
        "decisions": {"R1": _selected_ok(old_packet)},
    }

    result = a10.apply_normative_semantic_proof(proof, checkpoint)

    assert result["semantic_proof_applied"] == 1
    assert result["semantic_queue_processed"] == 1
    assert result["semantic_queue_total"] == 1
    assert [row["requirement_id"] for row in result["semantic_queue"]] == ["R2"]
    assert result["semantic_proof_summary"]["queue_fingerprint_match"] is False


def test_alpha10_changed_selected_evidence_returns_packet_to_pending():
    old_packet = _packet("R1")
    old_root = queue_fingerprint([old_packet])

    changed = _packet("R1")
    changed["evidence"][0]["text"] = "changed project evidence"
    proof = {
        "rows": [{"requirement_id": "R1", "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"}],
        "semantic_queue": [changed],
        "semantic_queue_total": 1,
    }
    checkpoint = {
        "root_fingerprint": old_root,
        "fingerprint": old_root,
        "root_queue_total": 1,
        "queue_total": 1,
        "decisions": {"R1": _selected_ok(old_packet)},
    }

    result = a10.apply_normative_semantic_proof(proof, checkpoint)

    assert result["semantic_proof_applied"] == 0
    assert result["semantic_queue_processed"] == 0
    assert result["semantic_queue_total"] == 1
    assert result.get("semantic_proof_stale") is True


def test_alpha10_expanded_root_partial_run_keeps_prior_completed_decisions(monkeypatch):
    old_queue=[_packet("R1"),_packet("R2"),_packet("R3")]
    old_root=queue_fingerprint(old_queue)
    previous={
        "root_fingerprint":old_root,
        "fingerprint":old_root,
        "root_queue_total":3,
        "queue_total":3,
        "decisions":{
            "R1":_ok("VERIFIED_OK"),
            "R2":_ok("REVIEW_QUESTION"),
        },
        "provider_errors":[],
    }
    # After knowledge expansion + apply(), R1/R2 are already resolved and the
    # UI passes a larger pending slice than the old root total.
    pending=[_packet(rid) for rid in ("R3","R4","R5","R6","R7","R8")]

    monkeypatch.setattr(a10,"_previous_checkpoint",lambda:previous)
    monkeypatch.setattr(
        a10,
        "_ORIGINAL_RUN",
        lambda queue,judge_provider=None,critic_provider=None,limit=24:{
            "decisions":{"R3":_ok("VERIFIED_OK")},
            "selected":1,
            "provider_errors":["HTTP 429"],
        },
    )

    merged=a10.run_normative_semantic_proof(
        pending,judge_provider=object(),critic_provider=object(),limit=24,
    )

    assert set(merged["decisions"])=={"R1","R2","R3"}
    assert merged["processed_total"]==3
    assert merged["verified_ok"]==2
    assert merged["reviewed_total"]==1
    assert merged["root_queue_total"]==8
    assert merged["pending_total"]==5
    assert merged["provider_errors"]==["HTTP 429"]


def test_alpha10_pending_requirement_is_not_carried_from_previous_checkpoint(monkeypatch):
    previous={
        "root_fingerprint":"old-root",
        "fingerprint":"old-root",
        "root_queue_total":4,
        "queue_total":4,
        "decisions":{
            "R1":_ok("VERIFIED_OK"),
            "R2":_ok("REVIEW_QUESTION"),
        },
        "provider_errors":[],
    }
    # R2 is pending again, so its old decision must not be silently reused.
    pending=[_packet(rid) for rid in ("R2","R3","R4","R5","R6")]

    monkeypatch.setattr(a10,"_previous_checkpoint",lambda:previous)
    monkeypatch.setattr(
        a10,
        "_ORIGINAL_RUN",
        lambda queue,judge_provider=None,critic_provider=None,limit=24:{
            "decisions":{"R3":_ok("VERIFIED_OK")},
            "selected":1,
            "provider_errors":[],
        },
    )

    merged=a10.run_normative_semantic_proof(
        pending,judge_provider=object(),critic_provider=object(),limit=24,
    )

    assert set(merged["decisions"])=={"R1","R3"}
    assert "R2" not in merged["decisions"]
    assert merged["root_queue_total"]==6



def test_alpha10_recalculates_live_held_frontier_after_accumulated_semantic_decisions():
    queue = [_packet("R1"), _packet("R2"), _packet("R3")]
    root = queue_fingerprint(queue)
    proof = {
        "rows": [
            {
                "requirement_id": rid,
                "kind": "REVIEW_QUESTION",
                "retrieval_kind": "VERIFIED_OK",
                "proof_state": "SEMANTIC_PROOF_REQUIRED",
            }
            for rid in ("R1", "R2", "R3")
        ],
        "semantic_queue": queue,
        "semantic_queue_total": 3,
        "demoted_keyword_only": 3,
        "demoted_keyword_only_initial": 3,
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

    assert result["demoted_keyword_only_initial"] == 3
    assert result["demoted_keyword_only_remaining"] == 2
    assert result["demoted_keyword_only"] == 2
    assert result["proof_frontier"]["held_total"] == 2
    assert result["proof_frontier"]["blocker_counts"]["SEMANTIC_PENDING"] == 1
    assert result["proof_frontier"]["blocker_counts"]["SEMANTIC_REVIEWED_NO_PROMOTION"] == 1
    assert result["proof_frontier"]["semantic_pending"]["total"] == 1
    assert result["proof_frontier"]["semantic_pending"]["rows"][0]["requirement_id"] == "R3"
