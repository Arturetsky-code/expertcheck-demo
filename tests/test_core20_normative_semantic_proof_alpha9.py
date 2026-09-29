import json
from types import SimpleNamespace

from core20.normative_proof import NormativeProofEngine20
from core20.normative_semantic_proof import (
    apply_normative_semantic_proof,
    run_normative_semantic_proof,
)


class FakeProvider:
    def __init__(self, name, model=None):
        self.name = name
        self.model = model or f"{name}-model"

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
                    "reason": "Адресные фрагменты прямо подтверждают всё переданное атомарное требование.",
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
            model=self.model,
            status_code=200,
            error="",
        )


def _proof_result(*, multi=False):
    row={
        "requirement_id": "PP87-X-SEM",
        "source": "ПП РФ №87",
        "paragraph": "п. X",
        "topic": "Инженерная защита",
        "sections": ["ПЗУ"],
        "check_kind": "SEMANTIC",
        "requirement": "В ПЗУ должны быть обоснованы решения по инженерной защите территории.",
        "kind": "VERIFIED_OK",
        "state": "Подтверждено",
        "evidence_id": "NORM-E-PP87-X-SEM-01",
        "evidence_document": "ПЗУ.pdf",
        "evidence_page": 10,
        "evidence_fragment": "Решения по инженерной защите территории обоснованы расчётами отвода поверхностного стока.",
    }
    if multi:
        row["evidence_candidates"]=[
            {
                "evidence_id":"NORM-E-PP87-X-SEM-01",
                "document":"ПЗУ.pdf","page":10,"section":"ПЗУ",
                "fragment":"Решения по инженерной защите территории обоснованы расчётами отвода поверхностного стока.",
                "matched_keywords":["инженерной защите","обоснованы"],
                "retrieval_keyword_score":2,
                "retrieval_keyword_coverage":0.67,
            },
            {
                "evidence_id":"NORM-E-PP87-X-SEM-02",
                "document":"ПЗУ.pdf","page":11,"section":"ПЗУ",
                "fragment":"Расчёт поверхностного стока и принятая схема водоотведения приведены в подразделе инженерной подготовки.",
                "matched_keywords":["инженерной","решения"],
                "retrieval_keyword_score":2,
                "retrieval_keyword_coverage":0.50,
            },
        ]
        row["retrieval_candidate_count"]=2
    return NormativeProofEngine20().run([row])


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
    assert row["semantic_proof"]["independent"] is True
    assert applied["project_findings"] == 0


def test_alpha9_multi_evidence_packet_preserves_addressable_candidates_and_trace():
    proof = _proof_result(multi=True)
    assert proof["semantic_queue_total"] == 1
    assert len(proof["semantic_queue"][0]["evidence"]) == 2
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    assert semantic["evidence_candidates"] == 2
    decision=semantic["decisions"]["PP87-X-SEM"]
    assert len(decision["selected_evidence"]) == 2
    assert {row["page"] for row in decision["selected_evidence"]} == {10,11}
    applied=apply_normative_semantic_proof(proof,semantic)
    assert len(applied["rows"][0]["semantic_selected_evidence"]) == 2


def test_alpha9_same_provider_cannot_create_independent_normative_proof():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Same-AI","model-a"),
        critic_provider=FakeProvider("Same-AI","model-b"),
        limit=8,
    )
    assert semantic["verified_ok"] == 0
    assert semantic["provider_errors"]
    applied = apply_normative_semantic_proof(proof, semantic)
    assert applied["rows"][0]["kind"] == "REVIEW_QUESTION"


def test_alpha9_same_actual_model_is_not_independent_even_across_providers():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Provider-A","shared-model"),
        critic_provider=FakeProvider("Provider-B","shared-model"),
        limit=8,
    )
    assert semantic["verified_ok"] == 0
    decision=semantic["decisions"]["PP87-X-SEM"]
    assert decision["independent"] is False
    assert "одну и ту же" in decision["independence_reason"]
    applied=apply_normative_semantic_proof(proof,semantic)
    assert applied["rows"][0]["kind"] == "REVIEW_QUESTION"


def test_alpha9_legacy_stale_semantic_proof_without_selected_proof_fingerprint_is_rejected():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    semantic["fingerprint"] = "stale"
    decision = semantic["decisions"]["PP87-X-SEM"]
    decision["packet_fingerprint"] = "stale-packet"
    decision.pop("requirement_fingerprint", None)
    decision.pop("selected_proof_fingerprint", None)
    applied = apply_normative_semantic_proof(proof, semantic)
    assert applied["semantic_proof_applied"] == 0
    assert applied["semantic_proof_stale"] is True
    assert applied["rows"][0]["kind"] == "REVIEW_QUESTION"


def test_alpha9_existing_semantic_proof_survives_queue_expansion_for_unchanged_packet():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )

    expanded = _proof_result()
    extra = dict(expanded["semantic_queue"][0])
    extra["packet_id"] = "NORM-PP87-Y-SEM"
    extra["requirement_id"] = "PP87-Y-SEM"
    extra["requirement"] = "В ПЗУ должны быть приведены сведения о вертикальной планировке территории."
    extra["evidence"] = [dict(extra["evidence"][0])]
    extra["evidence"][0]["evidence_id"] = "NORM-E-PP87-Y-SEM-01"
    extra["evidence"][0]["page"] = 12
    extra["evidence"][0]["text"] = "Приведено описание вертикальной планировки территории."
    expanded["semantic_queue"] = [*expanded["semantic_queue"], extra]
    expanded["semantic_queue_total"] = 2

    applied = apply_normative_semantic_proof(expanded, semantic)
    assert applied["semantic_proof_applied"] == 1
    assert applied["semantic_proof_stale"] is False
    assert applied["semantic_proof_summary"]["queue_fingerprint_match"] is False
    assert applied["semantic_proof_summary"]["reused_decisions"] == 1
    assert applied["rows"][0]["kind"] == "VERIFIED_OK"


def test_alpha9_selected_evidence_proof_survives_candidate_pool_growth():
    proof = _proof_result(multi=True)
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )

    expanded = _proof_result(multi=True)
    packet = expanded["semantic_queue"][0]
    packet["evidence"].insert(0,{
        "evidence_id":"NORM-E-PP87-X-SEM-00",
        "document":"ПЗУ.pdf",
        "page":9,
        "section":"ПЗУ",
        "text":"Дополнительный адресный кандидат по инженерной защите территории.",
        "source_locator":"ПЗУ.pdf, стр. 9",
        "matched_keywords":["инженерной защите"],
        "retrieval_keyword_score":1,
        "retrieval_keyword_coverage":0.33,
    })
    applied = apply_normative_semantic_proof(expanded, semantic)
    assert applied["semantic_proof_applied"] == 1
    assert applied["semantic_proof_stale"] is False
    assert applied["semantic_proof_summary"]["queue_fingerprint_match"] is False
    assert applied["rows"][0]["kind"] == "VERIFIED_OK"


def test_alpha9_selected_evidence_change_invalidates_proof_even_if_requirement_is_same():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )

    changed = _proof_result()
    changed["semantic_queue"][0]["evidence"][0]["text"] = (
        "На этой странице инженерная защита упоминается, но прежний подтверждённый фрагмент отсутствует."
    )
    applied = apply_normative_semantic_proof(changed, semantic)
    assert applied["semantic_proof_applied"] == 0
    assert applied["semantic_proof_stale"] is True
    assert applied["rows"][0]["kind"] == "REVIEW_QUESTION"


def test_alpha9_requirement_change_invalidates_selected_evidence_proof():
    proof = _proof_result()
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )

    changed = _proof_result()
    changed["semantic_queue"][0]["requirement"] = (
        "В ПЗУ должны быть обоснованы решения по инженерной защите территории и приведён отдельный расчёт."
    )
    applied = apply_normative_semantic_proof(changed, semantic)
    assert applied["semantic_proof_applied"] == 0
    assert applied["semantic_proof_stale"] is True
