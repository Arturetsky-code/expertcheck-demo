from __future__ import annotations

from core.ai_continuation_ledger import CURRENT_SEMANTIC_ENGINE_VERSION
from core.ai_queue_universe_patch import (
    PATCH_VERSION,
    install_ai_queue_universe_patch,
    queue_status_current_universe,
)


def _row(packet_id: str) -> dict:
    return {
        "semantic_evidence_packet": {
            "packet_id": packet_id,
            "evidence_level": "L4",
            "checker": {"consensus_eligible": True},
        }
    }


def _judge(packet_id: str) -> dict:
    return {
        "packet_id": packet_id,
        "verdict": "INSUFFICIENT",
        "provider": "Groq",
        "model": "openai/gpt-oss-120b",
    }


def _checkpoint_lane(prefix: str, count: int) -> dict:
    return {f"{prefix}-{index}": _judge(f"{prefix}-{index}") for index in range(1, count + 1)}


def test_test78_historical_175_does_not_create_phantom_92_pending():
    assignment_rows = [_row(f"A-{index}") for index in range(1, 11)]
    checklist_rows = [_row(f"C-{index}") for index in range(1, 61)]

    checkpoint = {
        "_project_fingerprint": "SNAPSHOT-78",
        "_semantic_engine_version": CURRENT_SEMANTIC_ENGINE_VERSION,
        "assignment": {"judge": _checkpoint_lane("A", 10), "critic": {}},
        "checklist": {"judge": _checkpoint_lane("C", 60), "critic": {}},
        "_ledger": {
            "version": "18.5-evidence-quality-ledger-v1",
            "snapshot_id": "SNAPSHOT-78",
            "domains": {
                "assignment": {
                    "packet_total": 33,
                    "packet_ids": [f"A-OLD-{index}" for index in range(1, 34)],
                },
                "checklist": {
                    "packet_total": 142,
                    "packet_ids": [f"C-OLD-{index}" for index in range(1, 143)],
                },
            },
        },
    }
    doc = {
        "analysis_snapshot": {"snapshot_id": "SNAPSHOT-78"},
        "semantic_evidence_engine": {
            "assignment": {
                "cumulative_packet_total": 33,
                "judge_candidates": 33,
                "judge_responses": 23,
                "judge_pending": 10,
            },
            "checklist": {
                "cumulative_packet_total": 142,
                "judge_candidates": 142,
                "judge_responses": 60,
                "judge_pending": 82,
            },
        },
        "assignment_atomic_compliance": assignment_rows,
        "automatic_checklist_review": {
            "atomic_verification": {"atoms": checklist_rows}
        },
    }

    status = queue_status_current_universe(doc, checkpoint)

    assert status["eligible"] == 70
    assert status["judge_done"] == 70
    assert status["judge_remaining"] == 0
    assert status["packages_complete"] == 70
    assert status["packages_remaining"] == 0
    assert status["operation_remaining"] == 0
    assert status["completion_pct"] == 100.0
    assert status["historical_packet_total"] == 175
    assert status["retired_packet_count"] == 105
    assert status["queue_universe_patch_version"] == PATCH_VERSION

    assert checkpoint["_ledger"]["domains"]["assignment"]["packet_total"] == 10
    assert checkpoint["_ledger"]["domains"]["checklist"]["packet_total"] == 60
    assert doc["semantic_evidence_engine"]["assignment"]["current_universe_packet_total"] == 10
    assert doc["semantic_evidence_engine"]["checklist"]["current_universe_packet_total"] == 60


def test_current_universe_can_still_report_real_pending_work():
    rows = [_row(f"A-{index}") for index in range(1, 13)]
    checkpoint = {
        "_semantic_engine_version": CURRENT_SEMANTIC_ENGINE_VERSION,
        "assignment": {"judge": _checkpoint_lane("A", 10), "critic": {}},
        "checklist": {"judge": {}, "critic": {}},
        "_ledger": {
            "domains": {"assignment": {"packet_total": 50}, "checklist": {"packet_total": 0}}
        },
    }
    doc = {
        "semantic_evidence_engine": {
            "assignment": {"cumulative_packet_total": 50, "judge_candidates": 50},
            "checklist": {},
        },
        "assignment_atomic_compliance": rows,
        "automatic_checklist_review": {"atomic_verification": {"atoms": []}},
    }

    status = queue_status_current_universe(doc, checkpoint)

    assert status["eligible"] == 12
    assert status["judge_done"] == 10
    assert status["judge_remaining"] == 2
    assert status["packages_remaining"] == 2
    assert status["operation_remaining"] == 2


def test_stale_engine_keeps_legacy_migration_path():
    # The patch deliberately does not reinterpret checkpoints from an older
    # semantic engine. Existing migration tests therefore retain their meaning.
    rows = [_row("A-1")]
    checkpoint = {
        "_semantic_engine_version": "18.4-old-engine",
        "assignment": {"judge": {"A-OLD": _judge("A-OLD")}, "critic": {}},
        "checklist": {"judge": {}, "critic": {}},
    }
    doc = {
        "semantic_evidence_engine": {
            "assignment": {"judge_candidates": 2},
            "checklist": {},
        },
        "assignment_atomic_compliance": rows,
        "automatic_checklist_review": {"atomic_verification": {"atoms": []}},
    }

    status = queue_status_current_universe(doc, checkpoint)

    assert status["checkpoint_stale"] is True
    assert status["eligible"] >= 1


def test_installer_is_idempotent():
    install_ai_queue_universe_patch()
    install_ai_queue_universe_patch()
