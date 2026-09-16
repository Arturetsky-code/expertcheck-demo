from __future__ import annotations

from core.workspace_signature_normative_patch import PATCH_VERSION
from core.workspace_store import snapshot_signature


def _payload() -> tuple[dict, dict]:
    document = {"core_version": "20.0-alpha10-expert-workflow-reliability"}
    payload = {
        "project_name": "Test 78",
        "analysis_time": "2026-09-16T12:00:00",
        "result": [[document], [], []],
        "object_registry_confirmed": True,
        "object_assembly_rows": [],
        "completeness_user_confirmed": True,
        "completeness_decisions": {},
        "checklist_run": None,
        "checklist_user_results": {},
        "risk_user_decisions": {},
        "object_learning_examples": [],
        "semantic_execution_checkpoint": {},
    }
    return payload, document


def _proof(done: int, remaining: int) -> dict:
    return {
        "engine_version": PATCH_VERSION,
        "queue_total": 12,
        "queue_remaining": remaining,
        "decisions": [
            {
                "requirement_id": f"REQ-{index:02d}",
                "state": "VERIFIED_OK",
                "judge_verdict": "SUPPORTS",
                "critic_verdict": "SUPPORTS",
            }
            for index in range(done)
        ],
    }


def test_snapshot_signature_tracks_partial_and_final_normative_proof_in_place():
    payload, document = _payload()

    baseline = snapshot_signature(payload)
    assert snapshot_signature(payload) == baseline

    document["normative_semantic_proof"] = _proof(done=4, remaining=8)
    after_four = snapshot_signature(payload)
    assert after_four != baseline
    assert snapshot_signature(payload) == after_four

    document["normative_semantic_proof"] = _proof(done=8, remaining=4)
    after_eight = snapshot_signature(payload)
    assert after_eight != after_four

    document["normative_semantic_proof"] = _proof(done=12, remaining=0)
    completed = snapshot_signature(payload)
    assert completed != after_eight

    # Removing the proof returns to the legacy signature.  This also lets
    # autosave detect an explicit proof reset/migration.
    document.pop("normative_semantic_proof")
    assert snapshot_signature(payload) == baseline
