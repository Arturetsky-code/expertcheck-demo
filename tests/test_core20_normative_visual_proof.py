from core.ai_gateway import AIResult
from core20.normative_visual_proof import (
    apply_normative_visual_proof,
    run_normative_visual_proof,
)


class FakeVisionProvider:
    def __init__(self, name, *, judge_verdict="SUPPORTS", critic_accept=True):
        self.name=name
        self.model=f"{name}-vision"
        self.judge_verdict=judge_verdict
        self.critic_accept=critic_accept
        self.calls=[]

    def generate_vision_validated(
        self, prompt, image_base64, mime_type, system, validator, json_schema,
    ):
        import json
        payload=json.loads(prompt)
        self.calls.append(payload)
        if payload["task"]=="visual_evidence_judge":
            body={"items":[{
                "item_id":row["item_id"],
                "verdict":self.judge_verdict,
                "confidence":0.93,
                "observed_features":["видимый требуемый элемент"] if self.judge_verdict=="SUPPORTS" else [],
                "reason":"Проверено по изображению.",
            } for row in payload["items"]]}
        else:
            body={"reviews":[{
                "item_id":row["item_id"],
                "accept":self.critic_accept,
                "confidence":0.91,
                "observed_features":["независимо подтверждено"] if self.critic_accept else [],
                "reason":"Независимая визуальная проверка.",
            } for row in payload["items"]]}
        text=json.dumps(body,ensure_ascii=False)
        assert validator(text)
        return AIResult(True,self.name,text=text,status_code=200,model=self.model)


def _item(item_id="I-1", pages=None):
    return {
        "item_id":item_id,
        "requirement_id":"R-1",
        "element_id":item_id,
        "label":"Границы",
        "visual_kind":"PZU_SITE_LAYOUT",
        "review_question":"Показаны ли границы?",
        "candidate_pages":pages or [
            {"document":"ПЗУ.pdf","page":9},
            {"document":"ПЗУ.pdf","page":70},
        ],
    }


def _cache():
    return {
        "entries":[
            {
                "cache_id":"VIS-9","document":"ПЗУ.pdf","page":9,
                "image_sha256":"sha9","mime_type":"image/jpeg",
                "image_base64":"QUJD","image_bytes":10,
            },
            {
                "cache_id":"VIS-70","document":"ПЗУ.pdf","page":70,
                "image_sha256":"sha70","mime_type":"image/jpeg",
                "image_base64":"REVG","image_bytes":10,
            },
        ]
    }


def _batches():
    return [{
        "document":"ПЗУ.pdf","page":9,"cache_id":"VIS-9",
        "items":[{"item_id":"I-1"}],
    }]


def test_visual_proof_confirms_only_two_independent_positive_models():
    proof=run_normative_visual_proof(
        [_item()],
        page_batches=_batches(),
        visual_cache=_cache(),
        judge_provider=FakeVisionProvider("JudgeVision"),
        critic_provider=FakeVisionProvider("CriticVision"),
        limit_batches=4,
    )
    assert proof["confirmed_total"]==1
    assert proof["newly_confirmed"]==1
    row=proof["decisions"]["I-1"]
    assert row["state"]=="VISUALLY_CONFIRMED"
    assert row["independent"] is True
    assert row["document"]=="ПЗУ.pdf"
    assert row["page"]==9


def test_visual_proof_same_actual_provider_never_confirms():
    proof=run_normative_visual_proof(
        [_item()],
        page_batches=_batches(),
        visual_cache=_cache(),
        judge_provider=FakeVisionProvider("SameVision"),
        critic_provider=FakeVisionProvider("SameVision"),
    )
    assert proof["confirmed_total"]==0
    assert proof["decisions"]["I-1"]["state"]=="FALLBACK_REQUIRED"
    assert "независимый" in proof["decisions"]["I-1"]["reason"]


def test_visual_not_proven_uses_next_cached_candidate_on_next_wave():
    judge=FakeVisionProvider("JudgeVision",judge_verdict="NOT_PROVEN")
    first=run_normative_visual_proof(
        [_item()],
        page_batches=_batches(),
        visual_cache=_cache(),
        judge_provider=judge,
        critic_provider=FakeVisionProvider("CriticVision"),
    )
    assert first["decisions"]["I-1"]["state"]=="FALLBACK_REQUIRED"
    assert judge.calls[0]["page"]==9

    second=run_normative_visual_proof(
        [_item()],
        page_batches=_batches(),
        visual_cache=_cache(),
        judge_provider=FakeVisionProvider("JudgeVision",judge_verdict="SUPPORTS"),
        critic_provider=FakeVisionProvider("CriticVision",critic_accept=True),
        checkpoint=first,
    )
    assert second["decisions"]["I-1"]["state"]=="VISUALLY_CONFIRMED"
    assert second["decisions"]["I-1"]["page"]==70
    assert second["confirmed_total"]==1


def test_visual_negative_never_becomes_project_finding_after_candidates_exhausted():
    one_page=_item(pages=[{"document":"ПЗУ.pdf","page":9}])
    proof=run_normative_visual_proof(
        [one_page],
        page_batches=_batches(),
        visual_cache=_cache(),
        judge_provider=FakeVisionProvider("JudgeVision",judge_verdict="NOT_PROVEN"),
        critic_provider=FakeVisionProvider("CriticVision"),
    )
    assert proof["confirmed_total"]==0
    assert proof["decisions"]["I-1"]["state"]=="REVIEW_QUESTION"
    assert "нарушение не формируется" in proof["decisions"]["I-1"]["reason"]


def test_apply_visual_proof_closes_contract_only_when_all_visual_elements_confirmed():
    item=_item()
    checkpoint=run_normative_visual_proof(
        [item],
        page_batches=_batches(),
        visual_cache=_cache(),
        judge_provider=FakeVisionProvider("JudgeVision"),
        critic_provider=FakeVisionProvider("CriticVision"),
    )
    proof_result={
        "rows":[{
            "requirement_id":"R-1",
            "kind":"SYSTEM_LIMITATION",
            "state":"Не проверено системой",
            "proof_state":"VISUAL_PROOF_REQUIRED",
            "visual_preflight":{
                "structural_review_required_count":0,
                "elements":[{
                    "id":"I-1",
                    "label":"Границы",
                    "verification_mode":"VISUAL_CONTENT",
                    "proof_status":"VISUAL_REVIEW_REQUIRED",
                }],
            },
        }],
        "visual_item_queue":[item],
        "visual_queue":[{"requirement_id":"R-1"}],
    }
    applied=apply_normative_visual_proof(proof_result,checkpoint,_cache())
    row=applied["rows"][0]
    assert applied["visual_proof_applied"]==1
    assert applied["visual_contracts_confirmed"]==1
    assert applied["visual_item_queue_total"]==0
    assert applied["visual_queue_total"]==0
    assert row["kind"]=="VERIFIED_OK"
    assert row["proof_state"]=="INDEPENDENT_VISUAL_PROOF"
    assert row["visual_preflight"]["elements"][0]["proof_status"]=="VISUAL_CONFIRMED"
