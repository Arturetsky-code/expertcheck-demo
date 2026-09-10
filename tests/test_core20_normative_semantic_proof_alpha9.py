import json
from types import SimpleNamespace

from core20.normative_proof import NormativeProofEngine20
from core20.normative_semantic_proof import (
    apply_normative_semantic_proof,
    run_normative_semantic_proof,
)


class FakeProvider:
    def __init__(self, name):
        self.name = name

    def generate(self, prompt, system):
        payload = json.loads(prompt)
        task = payload.get("task")
        packets = payload.get("packets") or []
        if task == "evidence_judge":
            body = {
                "decisions": [{
                    "packet_id": p["packet_id"],
                    "verdict": "SUPPORTS",
                    "evidence_ids": [x["evidence_id"] for x in p.get("evidence") or []],
                    "same_entity": True,
                    "same_property": True,
                    "qualifiers_satisfied": True,
                    "modality_satisfied": True,
                    "confidence": 0.97,
                    "reason": "Адресный фрагмент прямо подтверждает всё переданное атомарное требование.",
                } for p in packets]
            }
        else:
            body = {
                "reviews": [{
                    "packet_id": p["packet_id"],
                    "accept": True,
                    "evidence_ids": list((p.get("judge_decision") or {}).get("evidence_ids") or []),
                    "blocking_concerns": [],
                    "confidence": 0.95,
                    "reason": "Подмены смысла в cited evidence не обнаружено.",
                } for p in packets]
            }
        return SimpleNamespace(
            ok=True,
            text=json.dumps(body, ensure_ascii=False),
            provider=self.name,
            model="fake-model",
            status_code=200,
            error="",
        )


def _proof_result():
    return NormativeProofEngine20().run([{
        "requirement_id": "PP87-X-SEM",
        "source": "ПП РФ №87",
        "paragraph": "п. X",
        "topic": "Инженерная защита",
        "sections": ["ПЗУ"],
        "check_kind": "SEMANTIC",
        "requirement": "В ПЗУ должны быть обоснованы решения по инженерной защите территории.",
        "kind": "VERIFIED_OK",
        "state": "Подтверждено",
        "evidence_document": "ПЗУ.pdf",
        "evidence_page": 10,
        "evidence_fragment": "Решения по инженерной защите территории обоснованы расчётами отвода поверхностного стока.",
    }])


def test_alpha9_independent_judge_critic_can_promote_semantic_proof():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    assert semantic["verified_ok"] == 1
    applied = apply_normative_semantic_proof(proof, semantic)
    row = applied["rows"][0]
    assert row["kind"] == "VERIFIED_OK"
    assert row["proof_state"] == "SEMANTIC_CONSENSUS_PROOF"
    assert row["reason_code"] == "NORMATIVE_SEMANTIC_PROOF_CONFIRMED"
    assert applied["project_findings"] == 0


def test_alpha9_same_provider_cannot_create_independent_normative_proof():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Same-AI"),
        critic_provider=FakeProvider("Same-AI"),
        limit=8,
    )
    assert semantic["verified_ok"] == 0
    assert semantic["provider_errors"]
    applied = apply_normative_semantic_proof(proof, semantic)
    assert applied["rows"][0]["kind"] == "REVIEW_QUESTION"


def test_alpha9_stale_semantic_proof_is_rejected_by_queue_fingerprint():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    semantic["fingerprint"] = "stale"
    applied = apply_normative_semantic_proof(proof, semantic)
    assert applied["semantic_proof_applied"] == 0
    assert applied["semantic_proof_stale"] is True
    assert applied["rows"][0]["kind"] == "REVIEW_QUESTION"
