from __future__ import annotations

from core20 import alpha10_reliability as a10
from core20.normative_semantic_proof import queue_fingerprint


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
            "R1": {"state": "VERIFIED_OK", "reason": "ok", "selected_evidence": []},
            "R2": {"state": "REVIEW_QUESTION", "reason": "review", "selected_evidence": []},
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
            "R1": {"state": "VERIFIED_OK"},
            "R2": {"state": "REVIEW_QUESTION"},
        },
        "provider_errors": [],
    }

    merged = a10._merge_result(
        {"decisions": {"R3": {"state": "VERIFIED_OK"}}, "provider_errors": ["temporary 429"]},
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
        "decisions": {"R1": {"state": "VERIFIED_OK"}},
    }

    result = a10.apply_normative_semantic_proof(proof, stale)

    assert result["semantic_queue_total"] == 2
    assert result["semantic_queue_processed"] == 0
    assert result.get("semantic_proof_stale") is True
