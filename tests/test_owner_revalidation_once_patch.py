from __future__ import annotations

from core.owner_revalidation_once_patch import (
    PATCH_VERSION,
    install_owner_revalidation_once_patch,
)
from core.semantic_continuation import continuation_pending
from core.semantic_evidence_engine import ENGINE_VERSION as SEMANTIC_ENGINE_VERSION


def _site_row(packet_id: str) -> dict:
    return {
        "atom_id": packet_id,
        "requirement_id": packet_id,
        "requirement_text": "Предусмотреть ограждение части площадки.",
        "object_name": "Ограждение",
        "semantic_evidence_packet": {
            "packet_id": packet_id,
            "evidence_level": "L4",
            "checker": {"consensus_eligible": True},
            "binding_contract": {
                "scope": "SITE_SPECIFIC",
                "requires_same_owner": False,
                "requires_same_parameter": False,
            },
        },
    }


def _other_entity(packet_id: str) -> dict:
    return {
        "packet_id": packet_id,
        "verdict": "OTHER_ENTITY",
        "evidence_ids": [],
        "same_entity": False,
        "same_property": True,
        "qualifiers_satisfied": True,
        "modality_satisfied": True,
        "confidence": 0.95,
        "reason": "Доказательство относится к другой сущности.",
        "response_received": True,
        "valid": True,
        "provider": "Groq",
        "model": "openai/gpt-oss-120b",
    }


def test_site_other_entity_revalidation_runs_once_then_fresh_judge_stays_complete():
    install_owner_revalidation_once_patch()
    packet_id = "REQ-FENCE-ONE-SHOT"
    row = _site_row(packet_id)
    doc = {
        "atomic_requirement_graph": {"atoms": [dict(row)]},
        "assignment_atomic_compliance": [row],
        "automatic_checklist_review": {"atomic_verification": {"atoms": []}},
        "semantic_evidence_engine": {"assignment": {"judge_candidates": 1}},
        "analysis_snapshot": {"snapshot_id": "SNAP-ONE-SHOT"},
    }
    checkpoint = {
        "_project_fingerprint": "SNAP-ONE-SHOT",
        "_semantic_engine_version": SEMANTIC_ENGINE_VERSION,
        "assignment": {
            "judge": {packet_id: _other_entity(packet_id)},
            "critic": {},
        },
        "checklist": {"judge": {}, "critic": {}},
    }

    first = continuation_pending(doc, checkpoint)
    assert packet_id not in checkpoint["assignment"]["judge"]
    assert first["contract_revalidation_reopened"] == 1
    assert first["judge_remaining"] == 1
    assert checkpoint["_owner_contract_revalidation_version"] == PATCH_VERSION

    # Simulate the fresh response written by the next continuation run.  The
    # same OTHER_ENTITY verdict is a legitimate completed Judge operation; it
    # must not be deleted again merely because Streamlit rerenders the page.
    checkpoint["assignment"]["judge"][packet_id] = _other_entity(packet_id)

    second = continuation_pending(doc, checkpoint)
    assert packet_id in checkpoint["assignment"]["judge"]
    assert second["contract_revalidation_reopened"] == 0
    assert second["judge_done"] == 1
    assert second["judge_remaining"] == 0
    assert second["packages_remaining"] == 0
    assert second["operation_remaining"] == 0
    assert second["completion_pct"] == 100.0


def test_new_checkpoint_can_run_owner_revalidation_again():
    install_owner_revalidation_once_patch()
    packet_id = "REQ-FENCE-NEW-CHECKPOINT"
    row = _site_row(packet_id)
    doc = {
        "assignment_atomic_compliance": [row],
        "automatic_checklist_review": {"atomic_verification": {"atoms": []}},
        "semantic_evidence_engine": {"assignment": {"judge_candidates": 1}},
        "analysis_snapshot": {"snapshot_id": "SNAP-NEW"},
    }
    checkpoint = {
        "_project_fingerprint": "SNAP-NEW",
        "_semantic_engine_version": SEMANTIC_ENGINE_VERSION,
        "assignment": {"judge": {packet_id: _other_entity(packet_id)}, "critic": {}},
        "checklist": {"judge": {}, "critic": {}},
    }

    status = continuation_pending(doc, checkpoint)
    assert status["contract_revalidation_reopened"] == 1
    assert checkpoint["_owner_contract_revalidation_version"] == PATCH_VERSION
