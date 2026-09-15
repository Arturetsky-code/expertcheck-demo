from __future__ import annotations

"""Deterministic validation for ExpertCheck 20.0 Alpha 10 reliability overlay."""

from core20 import alpha10_reliability as a10
from core20.normative_semantic_proof import queue_fingerprint


def packet(rid: str) -> dict:
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


def complete(state: str) -> dict:
    return {
        "state": state,
        "judge_verdict": "SUPPORTS" if state == "VERIFIED_OK" else "INSUFFICIENT",
        "judge_confidence": 0.96,
        "critic_confidence": 0.93 if state == "VERIFIED_OK" else 0,
        "selected_evidence": [],
    }


def main() -> None:
    queue = [packet("R1"), packet("R2"), packet("R3")]
    root = queue_fingerprint(queue)
    proof = {
        "rows": [
            {"requirement_id": "R1", "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"},
            {"requirement_id": "R2", "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"},
            {"requirement_id": "R3", "kind": "REVIEW_QUESTION", "proof_state": "SEMANTIC_PROOF_REQUIRED"},
        ],
        "semantic_queue": queue,
        "semantic_queue_total": 3,
    }
    checkpoint = {
        "version": a10.ENGINE_VERSION,
        "root_fingerprint": root,
        "fingerprint": root,
        "root_queue_total": 3,
        "queue_total": 3,
        "decisions": {
            "R1": complete("VERIFIED_OK"),
            "R2": complete("REVIEW_QUESTION"),
        },
    }

    result = a10.apply_normative_semantic_proof(proof, checkpoint)
    assert result["semantic_queue_full_total"] == 3
    assert result["semantic_queue_processed"] == 2
    assert result["semantic_queue_confirmed"] == 1
    assert result["semantic_queue_reviewed"] == 1
    assert result["semantic_queue_total"] == 1
    assert [x["requirement_id"] for x in result["semantic_queue"]] == ["R3"]
    assert result["semantic_proof_applied"] == 1

    merged = a10._merge_result(
        {
            "decisions": {"R3": complete("VERIFIED_OK")},
            "provider_errors": ["temporary 429"],
        },
        checkpoint,
        root_fingerprint=root,
        root_total=3,
    )
    assert len(merged["decisions"]) == 3
    assert merged["processed_total"] == 3
    assert merged["verified_ok"] == 2
    assert merged["reviewed_total"] == 1
    assert merged["pending_total"] == 0
    assert merged["fingerprint"] == root

    stale = dict(checkpoint)
    stale["root_fingerprint"] = "different"
    stale["fingerprint"] = "different"
    stale_result = a10.apply_normative_semantic_proof(proof, stale)
    assert stale_result["semantic_queue_total"] == 3
    assert stale_result.get("semantic_proof_stale") is True

    failed = {
        "root_fingerprint": root,
        "fingerprint": root,
        "root_queue_total": 3,
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
    failed_result = a10.apply_normative_semantic_proof(proof, failed)
    assert failed_result["semantic_queue_processed"] == 0
    assert failed_result["semantic_queue_total"] == 3

    print("ExpertCheck 20.0 Alpha 10 reliability validation: OK")


if __name__ == "__main__":
    main()
