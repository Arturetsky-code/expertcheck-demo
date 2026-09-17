from __future__ import annotations

import core20  # noqa: F401 - installs the proof-trace overlay
from core20.normative_semantic_proof import apply_normative_semantic_proof, queue_fingerprint


RID = "PP87-12-C-PLANNING"


def _queue():
    return [{
        "packet_id": f"NORM-{RID}",
        "requirement_id": RID,
        "requirement": "В ПЗУ должны быть обоснованы и описаны решения по планировочной организации земельного участка.",
        "proof_type": "SEMANTIC_REQUIREMENT",
        "evidence": [{
            "evidence_id": "NORM-E-PLANNING-01",
            "document": "ПЗУ1.pdf",
            "page": 14,
            "text": "3 Обоснование и описание планировочной организации земельного участка.",
        }],
    }]


def _proof_result():
    return {
        "rows": [{
            "requirement_id": RID,
            "kind": "REVIEW_QUESTION",
            "state": "Вопрос специалисту",
            "proof_state": "SEMANTIC_PROOF_REQUIRED",
            "evidence_id": "RETRIEVAL-29",
            "evidence_document": "ПЗУ1.pdf",
            "evidence_page": 29,
            "evidence_fragment": "9 Обоснование схем транспортных коммуникаций.",
        }],
        "semantic_queue": _queue(),
        "verified_ok": 0,
        "review_questions": 1,
        "system_limitations": 0,
        "project_findings": 0,
    }


def _checkpoint(*, selected=True):
    queue = _queue()
    fingerprint = queue_fingerprint(queue)
    selected_evidence = [{
        "evidence_id": "NORM-E-PLANNING-01",
        "document": "ПЗУ1.pdf",
        "page": 14,
        "source_locator": "ПЗУ1.pdf, стр. 14",
        "fragment": "3 Обоснование и описание планировочной организации земельного участка.",
    }] if selected else []
    return {
        "fingerprint": fingerprint,
        "root_fingerprint": fingerprint,
        "root_queue_total": 1,
        "decisions": {
            RID: {
                "requirement_id": RID,
                "packet_id": f"NORM-{RID}",
                "state": "VERIFIED_OK",
                "reason": "Смысл подтверждён независимым консенсусом.",
                "judge_verdict": "SUPPORTS",
                "judge_confidence": 0.94,
                "judge_provider": "Groq",
                "judge_model": "openai/gpt-oss-120b",
                "critic_accept": True,
                "critic_confidence": 0.91,
                "critic_provider": "Gemini",
                "critic_model": "gemini-3.5-flash-lite",
                "independent": True,
                "selected_evidence": selected_evidence,
            }
        },
    }


def test_semantic_selected_evidence_becomes_canonical_and_retrieval_is_preserved():
    result = apply_normative_semantic_proof(_proof_result(), _checkpoint())
    row = result["rows"][0]

    assert row["kind"] == "VERIFIED_OK"
    assert row["proof_state"] == "SEMANTIC_CONSENSUS_PROOF"
    assert row["evidence_document"] == "ПЗУ1.pdf"
    assert row["evidence_page"] == 14
    assert "планировочной организации" in row["evidence_fragment"]
    assert row["canonical_evidence_source"] == "SEMANTIC_SELECTED_EVIDENCE"
    assert row["canonical_evidence_locator"] == "ПЗУ1.pdf, стр. 14"

    assert row["retrieval_evidence_document"] == "ПЗУ1.pdf"
    assert row["retrieval_evidence_page"] == 29
    assert "транспортных коммуникаций" in row["retrieval_evidence_fragment"]
    assert result["semantic_proof_applied"] == 1
    assert result["semantic_queue_total"] == 0


def test_positive_semantic_decision_without_addressable_selected_evidence_fails_closed():
    result = apply_normative_semantic_proof(_proof_result(), _checkpoint(selected=False))
    row = result["rows"][0]

    assert row["kind"] == "REVIEW_QUESTION"
    assert row["state"] == "Вопрос специалисту"
    assert row["proof_state"] == "SEMANTIC_PROOF_REQUIRED"
    assert row["reason_code"] == "NORMATIVE_SEMANTIC_CANONICAL_EVIDENCE_MISSING"
    assert row["proof_trace_consistent"] is False
    assert result["semantic_proof_applied"] == 0
    assert result["verified_ok"] == 0
    assert result["review_questions"] == 1
