from __future__ import annotations

from core.ai_continuation_ledger import (
    LEDGER_VERSION,
    queue_status_from_document,
    reconcile_domain_audit,
)
from core.verification_runtime_patch import _quota_pause_state


def _row(packet_id: str, *, level: str = "L4", eligible: bool = True) -> dict:
    return {
        "semantic_evidence_packet": {
            "packet_id": packet_id,
            "evidence_level": level,
            "checker": {"consensus_eligible": eligible},
        }
    }


def _judge(packet_id: str, verdict: str = "INSUFFICIENT") -> dict:
    return {
        "packet_id": packet_id,
        "verdict": verdict,
        "evidence_ids": [],
        "provider": "Groq",
        "model": "openai/gpt-oss-120b",
    }


def _critic(packet_id: str) -> dict:
    return {
        "packet_id": packet_id,
        "accept": True,
        "provider": "Gemini",
        "model": "gemini-3.7-flash",
    }


def test_reconcile_never_regresses_completed_checkpoint_counts():
    rows = [_row(f"A-{index}") for index in range(1, 11)]
    checkpoint = {
        "judge": {
            f"A-{index}": _judge(
                f"A-{index}",
                "SUPPORTS" if index <= 15 else "INSUFFICIENT",
            )
            for index in range(1, 34)
        },
        "critic": {
            f"A-{index}": _critic(f"A-{index}")
            for index in range(1, 16)
        },
    }
    current = {
        "judge_candidates": 10,
        "judge_responses": 10,
        "critic_responses": 0,
    }
    previous = {
        "judge_candidates": 33,
        "judge_responses": 33,
        "critic_responses": 15,
    }

    audit, ledger = reconcile_domain_audit(
        current,
        rows=rows,
        checkpoint_domain=checkpoint,
        previous_audit=previous,
    )

    assert audit["cumulative_ledger_version"] == LEDGER_VERSION
    assert audit["cumulative_packet_total"] == 33
    assert audit["judge_responses"] == 33
    assert audit["critic_required"] == 15
    assert audit["critic_responses"] == 15
    assert audit["unique_packages_complete"] == 33
    assert audit["unique_packages_pending"] == 0
    assert ledger["judge_done"] == 33
    assert ledger["critic_done"] == 15


def test_test77_style_migration_recovers_83_unique_packages_from_old_checkpoint():
    assignment_rows = [_row(f"A-{index}") for index in range(1, 11)]
    checklist_rows = [_row(f"C-{index}") for index in range(1, 51)]
    checkpoint = {
        "_project_fingerprint": "SNAPSHOT-77",
        "assignment": {
            "judge": {
                f"A-{index}": _judge(
                    f"A-{index}",
                    "SUPPORTS" if index <= 15 else "INSUFFICIENT",
                )
                for index in range(1, 34)
            },
            "critic": {
                f"A-{index}": _critic(f"A-{index}")
                for index in range(1, 16)
            },
        },
        "checklist": {
            "judge": {
                f"C-{index}": _judge(f"C-{index}", "INSUFFICIENT")
                for index in range(1, 11)
            },
            "critic": {},
        },
    }
    doc = {
        "semantic_evidence_engine": {
            "assignment": {
                "judge_candidates": 10,
                "judge_responses": 10,
                "critic_responses": 0,
            },
            "checklist": {
                "judge_candidates": 50,
                "judge_responses": 10,
                "critic_responses": 0,
            },
        },
        "assignment_atomic_compliance": assignment_rows,
        "automatic_checklist_review": {
            "atomic_verification": {"atoms": checklist_rows}
        },
    }

    status = queue_status_from_document(doc, checkpoint)

    assert status["eligible"] == 83
    assert status["judge_done"] == 43
    assert status["judge_remaining"] == 40
    assert status["critic_required"] == 15
    assert status["critic_done"] == 15
    assert status["critic_remaining"] == 0
    assert status["packages_complete"] == 43
    assert status["packages_remaining"] == 40
    assert status["responses"] == 58


def test_critic_pending_does_not_double_count_unique_package_remaining():
    rows = [_row("P-1"), _row("P-2"), _row("P-3")]
    checkpoint = {
        "judge": {
            "P-1": _judge("P-1", "SUPPORTS"),
            "P-2": _judge("P-2", "INSUFFICIENT"),
        },
        "critic": {},
    }
    audit, _ = reconcile_domain_audit(
        {},
        rows=rows,
        checkpoint_domain=checkpoint,
    )
    assert audit["judge_pending"] == 1
    assert audit["critic_pending"] == 1
    assert audit["unique_packages_pending"] == 2


def test_explicit_daily_quota_pauses_without_immediate_retry():
    error = (
        "HTTP 429: tokens per day (TPD) limit 200000, "
        "used 199142, requested 1200"
    )
    assert _quota_pause_state(429, error) == "DAILY_QUOTA_PAUSED"


def test_short_retry_hint_remains_transient_not_daily_pause():
    error = "HTTP 429: rate limit reached; retry after 12s"
    assert _quota_pause_state(429, error) == ""


def test_non_l4_or_non_consensus_packets_are_not_counted_as_ai_queue():
    rows = []
    rows.extend(_row(f"L4-{index}") for index in range(83))
    rows.extend(_row(f"L3-{index}", level="L3") for index in range(500))
    rows.extend(_row(f"NO-{index}", eligible=False) for index in range(146))

    audit, ledger = reconcile_domain_audit(
        {"judge_candidates": 83},
        rows=rows,
        checkpoint_domain={"judge": {}, "critic": {}},
    )

    assert audit["cumulative_packet_total"] == 83
    assert audit["judge_pending"] == 83
    assert ledger["packet_total"] == 83
    assert len(ledger["packet_ids"]) == 83
