import inspect
import json
from types import SimpleNamespace

from core20.normative_proof import NormativeProofEngine20
from core20.normative_foundation import default_foundation
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


def _gate2_queue(requirement_id, requirement, evidence, contract):
    return [{
        "packet_id": f"NORM-{requirement_id}",
        "requirement_id": requirement_id,
        "proof_type": "SEMANTIC_REQUIREMENT",
        "source": "Федеральный закон №384-ФЗ",
        "paragraph": "ст. 15",
        "topic": "Semantic Proof Gate 2.0",
        "requirement": requirement,
        "sections": ["ALL"],
        "semantic_proof_contract": contract,
        "evidence": evidence,
    }]


def test_gate2_blocks_responsibility_level_found_only_in_kr_even_when_both_models_support():
    contract = {
        "version": "2.0",
        "source_scope": {
            "label": "Источник доказательства — исходные данные или задание на проектирование",
            "fields": ["document", "section", "text"],
            "any_of": ["исходные данн", "задание на проектир"],
        },
        "required_groups": [{
            "id": "RESPONSIBILITY_IN_INPUT",
            "label": "Уровень ответственности указан именно в исходных данных/задании",
            "scope": "SAME_EVIDENCE",
            "fields": ["document", "section", "text"],
            "all_of_groups": [
                ["уровень ответствен"],
                ["исходные данн", "задание на проектир"],
            ],
        }],
    }
    queue = _gate2_queue(
        "FZ384-15-2-RESP-INPUT",
        "В исходных данных для проектирования должен быть указан уровень ответственности.",
        [{
            "evidence_id": "E-KR",
            "document": "Раздел ПД №4_КР1.pdf",
            "page": 109,
            "section": "КР",
            "text": "Уровень ответственности здания — II, класс сооружения КС-2.",
            "retrieval_keyword_score": 100,
            "retrieval_keyword_coverage": 1.0,
        }],
        contract,
    )
    semantic = run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision = semantic["decisions"]["FZ384-15-2-RESP-INPUT"]
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert decision["semantic_contract_source_scope_satisfied"] is False
    assert decision["semantic_contract_missing_groups"]
    assert "Semantic Proof Gate 2.0" in decision["reason"]


def test_gate2_allows_responsibility_level_when_same_evidence_is_assignment_input():
    contract = {
        "version": "2.0",
        "source_scope": {
            "label": "Источник доказательства — исходные данные или задание на проектирование",
            "fields": ["document", "section", "text"],
            "any_of": ["исходные данн", "задание на проектир"],
        },
        "required_groups": [{
            "id": "RESPONSIBILITY_IN_INPUT",
            "label": "Уровень ответственности указан именно в исходных данных/задании",
            "scope": "SAME_EVIDENCE",
            "fields": ["document", "section", "text"],
            "all_of_groups": [
                ["уровень ответствен"],
                ["исходные данн", "задание на проектир"],
            ],
        }],
    }
    queue = _gate2_queue(
        "FZ384-15-2-RESP-INPUT",
        "В исходных данных для проектирования должен быть указан уровень ответственности.",
        [{
            "evidence_id": "E-TASK",
            "document": "Задание на проектирование (ДСК).pdf",
            "page": 11,
            "section": "Задание",
            "text": "Уровень ответственности проектируемых зданий и сооружений — II.",
            "retrieval_keyword_score": 100,
            "retrieval_keyword_coverage": 1.0,
        }],
        contract,
    )
    semantic = run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision = semantic["decisions"]["FZ384-15-2-RESP-INPUT"]
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["semantic_contract_ready"] is True
    assert decision["state"] == "VERIFIED_OK"


def test_gate2_blocks_mere_384fz_mention_as_safety_justification():
    contract = {
        "version": "2.0",
        "required_groups": [
            {
                "id": "DESIGN_SAFETY_JUSTIFICATION",
                "label": "Обоснование соответствия относится к проектным решениям",
                "scope": "COLLECTIVE",
                "fields": ["text"],
                "all_of_groups": [
                    ["обосн", "соответств"],
                    ["проектн"],
                    ["решен"],
                ],
            },
            {
                "id": "APPLIED_NORMATIVE_BASIS",
                "label": "Указаны применённые положения/документы для соблюдения требований 384-ФЗ",
                "scope": "COLLECTIVE",
                "fields": ["text"],
                "all_of_groups": [
                    ["384-фз", "384 фз", "техническ регламент"],
                    ["положен", "нормативн документ", "документ"],
                    ["примен", "использ", "обеспеч"],
                ],
            },
        ],
    }
    queue = _gate2_queue(
        "FZ384-15-5.1-SAFETY-JUSTIFICATION",
        "Проектная документация должна содержать обоснование соответствия проектных решений требованиям 384-ФЗ.",
        [{
            "evidence_id": "E-PZ-LIST",
            "document": "Раздел ПД №1_ПЗ.pdf",
            "page": 8,
            "section": "ПЗ",
            "text": "Нормативные документы: Федеральный закон № 384-ФЗ «Технический регламент о безопасности зданий и сооружений».",
            "retrieval_keyword_score": 100,
            "retrieval_keyword_coverage": 1.0,
        }],
        contract,
    )
    semantic = run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision = semantic["decisions"]["FZ384-15-5.1-SAFETY-JUSTIFICATION"]
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["semantic_contract_ready"] is False
    assert "Обоснование соответствия" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_accepts_explicit_design_solution_justification_and_applied_basis():
    contract = {
        "version": "2.0",
        "required_groups": [
            {
                "id": "DESIGN_SAFETY_JUSTIFICATION",
                "label": "Обоснование соответствия относится к проектным решениям",
                "scope": "COLLECTIVE",
                "fields": ["text"],
                "all_of_groups": [
                    ["обосн", "соответств"],
                    ["проектн"],
                    ["решен"],
                ],
            },
            {
                "id": "APPLIED_NORMATIVE_BASIS",
                "label": "Указаны применённые положения/документы для соблюдения требований 384-ФЗ",
                "scope": "COLLECTIVE",
                "fields": ["text"],
                "all_of_groups": [
                    ["384-фз", "384 фз", "техническ регламент"],
                    ["положен", "нормативн документ", "документ"],
                    ["примен", "использ", "обеспеч"],
                ],
            },
        ],
    }
    queue = _gate2_queue(
        "FZ384-15-5.1-SAFETY-JUSTIFICATION",
        "Проектная документация должна содержать обоснование соответствия проектных решений требованиям 384-ФЗ.",
        [{
            "evidence_id": "E-PZ-JUST",
            "document": "Раздел ПД №1_ПЗ.pdf",
            "page": 12,
            "section": "ПЗ",
            "text": (
                "Соответствие проектных решений требованиям 384-ФЗ обосновано принятыми решениями. "
                "Для обеспечения соблюдения требований применены положения закона и нормативные документы, "
                "перечисленные в настоящем разделе."
            ),
            "retrieval_keyword_score": 100,
            "retrieval_keyword_coverage": 1.0,
        }],
        contract,
    )
    semantic = run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision = semantic["decisions"]["FZ384-15-5.1-SAFETY-JUSTIFICATION"]
    assert semantic["verified_ok"] == 1
    assert decision["semantic_contract_ready"] is True
    assert decision["state"] == "VERIFIED_OK"


def test_gate2_contract_change_invalidates_previous_selected_proof():
    proof = _proof_result()
    proof["semantic_queue"][0]["semantic_proof_contract"] = {
        "version": "2.0",
        "required_groups": [{
            "id": "JUSTIFICATION",
            "label": "Обоснование",
            "all_of_groups": [["обосн"]],
        }],
    }
    semantic = run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    changed = _proof_result()
    changed["semantic_queue"][0]["semantic_proof_contract"] = {
        "version": "2.0",
        "required_groups": [{
            "id": "JUSTIFICATION",
            "label": "Обоснование + расчёт",
            "all_of_groups": [["обосн"], ["расчет"]],
        }],
    }
    applied = apply_normative_semantic_proof(changed, semantic)
    assert applied["semantic_proof_applied"] == 0
    assert applied["semantic_proof_stale"] is True
    assert applied["rows"][0]["kind"] == "REVIEW_QUESTION"



def _proof_result_many(count=3):
    rows=[]
    for index in range(count):
        suffix=index+1
        rows.append({
            "requirement_id": f"PP87-X-SEM-{suffix}",
            "source": "ПП РФ №87",
            "paragraph": f"п. X.{suffix}",
            "topic": "Инженерная защита",
            "sections": ["ПЗУ"],
            "check_kind": "SEMANTIC",
            "requirement": f"Требование {suffix}: в ПЗУ должны быть обоснованы решения по инженерной защите территории.",
            "kind": "VERIFIED_OK",
            "state": "Подтверждено",
            "evidence_id": f"NORM-E-PP87-X-SEM-{suffix}-01",
            "evidence_document": "ПЗУ.pdf",
            "evidence_page": 10 + suffix,
            "evidence_fragment": f"Для требования {suffix} решения по инженерной защите территории обоснованы расчётами.",
        })
    return NormativeProofEngine20().run(rows)


def test_alpha9_semantic_proof_resumes_after_first_bounded_wave():
    proof=_proof_result_many(3)

    wave1=run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=2,
    )
    assert wave1["new_decisions"] == 2
    assert wave1["completed_before"] == 0
    assert wave1["pending_unprocessed"] == 1
    assert len(wave1["decisions"]) == 2

    applied1=apply_normative_semantic_proof(proof,wave1)
    assert applied1["semantic_proof_applied"] == 2
    assert applied1["semantic_completed_total"] == 2
    assert applied1["semantic_queue_total"] == 1

    wave2=run_normative_semantic_proof(
        applied1["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=2,
        checkpoint=wave1,
    )
    assert wave2["completed_before"] == 2
    assert wave2["new_decisions"] == 1
    assert wave2["pending_unprocessed"] == 0
    assert len(wave2["decisions"]) == 3
    assert wave2["newly_verified_ok"] == 1
    assert wave2["verified_ok"] == 3

    applied2=apply_normative_semantic_proof(proof,wave2)
    assert applied2["semantic_proof_applied"] == 3
    assert applied2["semantic_completed_total"] == 3
    assert applied2["semantic_queue_total"] == 0
    assert all(row["kind"] == "VERIFIED_OK" for row in applied2["rows"])


def test_alpha9_reviewed_semantic_decision_is_completed_not_pending():
    proof=_proof_result_many(2)
    wave=run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=1,
    )
    rid=next(iter(wave["decisions"]))
    wave["decisions"][rid]["state"]="REVIEW_QUESTION"
    wave["decisions"][rid]["reason"]="Evidence reviewed but not sufficient for promotion."

    applied=apply_normative_semantic_proof(proof,wave)

    assert applied["semantic_proof_applied"] == 0
    assert applied["semantic_completed_total"] == 1
    assert applied["semantic_reviewed_no_promotion"] == 1
    assert applied["semantic_queue_total"] == 1
    assert applied["rows"][0]["kind"] == "REVIEW_QUESTION"



def test_alpha9_semantic_runner_exposes_checkpoint_for_resumable_waves():
    signature=inspect.signature(run_normative_semantic_proof)
    assert "checkpoint" in signature.parameters



def test_alpha9_semantic_packet_carries_retrieval_quality_metadata():
    proof=_proof_result(multi=True)
    packet=proof["semantic_queue"][0]

    assert packet["retrieval_kind"]=="VERIFIED_OK"
    assert packet["retrieval_candidate_count"]==2
    assert packet["retrieval_reason_code"]



def test_qualified_provider_reuses_benchmark_without_live_preflight_calls():
    class QualifiedProvider(FakeProvider):
        qualification_required=True
        qualification_passed=True

        def __init__(self,name):
            super().__init__(name)
            self.qualification_summary={
                "actual_routes":[{"provider":name,"model":self.model,"calls":8}],
                "completed":True,
                "qualified":True,
            }

        def test_connection(self):
            raise AssertionError("live preflight must not run for qualified provider")

    proof=_proof_result()
    semantic=run_normative_semantic_proof(
        proof["semantic_queue"],
        judge_provider=QualifiedProvider("Judge-A"),
        critic_provider=QualifiedProvider("Critic-B"),
        limit=1,
    )

    assert semantic["verified_ok"] == 1
    assert semantic["preflight"]["judge"]["state"] == "QUALIFICATION_REUSED"
    assert semantic["preflight"]["critic"]["state"] == "QUALIFICATION_REUSED"
    assert semantic["preflight"]["judge"]["contract_probe_requested"] == 0
    assert semantic["preflight"]["critic"]["contract_probe_requested"] == 0



def _article31_semantic_contract():
    contracts={
        row["requirement_id"]:row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["FZ123-31-1-CONSTRUCTIVE-FIRE-HAZARD-TAXONOMY"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def test_gate2_article31_taxonomy_requires_explicit_c0_c3_value():
    contract=_article31_semantic_contract()
    queue=_gate2_queue(
        "FZ123-31-1-CONSTRUCTIVE-FIRE-HAZARD-TAXONOMY",
        "Класс конструктивной пожарной опасности должен относиться к С0, С1, С2 или С3.",
        [{
            "evidence_id":"E-PB-31-WITHOUT-VALUE",
            "document":"Раздел ПД №9_ПБ.pdf",
            "page":18,
            "section":"ПБ",
            "text":"Для здания проектом установлен класс конструктивной пожарной опасности.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-31-1-CONSTRUCTIVE-FIRE-HAZARD-TAXONOMY"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "С0–С3" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_article31_taxonomy_allows_explicit_c0_c3_value_for_semantic_judgement():
    contract=_article31_semantic_contract()
    queue=_gate2_queue(
        "FZ123-31-1-CONSTRUCTIVE-FIRE-HAZARD-TAXONOMY",
        "Класс конструктивной пожарной опасности должен относиться к С0, С1, С2 или С3.",
        [{
            "evidence_id":"E-PB-31-C0",
            "document":"Раздел ПД №9_ПБ.pdf",
            "page":18,
            "section":"ПБ",
            "text":"Класс конструктивной пожарной опасности здания: С0.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-31-1-CONSTRUCTIVE-FIRE-HAZARD-TAXONOMY"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True



def _article104_semantic_contract():
    contracts={
        row["requirement_id"]:row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["FZ123-104-1-AUPT-SUPPRESSION-METHOD"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def test_gate2_article104_requires_explicit_surface_or_volumetric_method():
    contract=_article104_semantic_contract()
    queue=_gate2_queue(
        "FZ123-104-1-AUPT-SUPPRESSION-METHOD",
        "АУПТ должна обеспечивать ликвидацию пожара поверхностным или объемным способом подачи огнетушащего вещества.",
        [{
            "evidence_id":"E-PB-104-WITHOUT-METHOD",
            "document":"Раздел ПД №9_ПБ.pdf",
            "page":42,
            "section":"ПБ",
            "text":"Для защищаемого помещения предусмотрена автоматическая установка пожаротушения.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-104-1-AUPT-SUPPRESSION-METHOD"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "поверхностный/объёмный" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_article104_allows_explicit_auptr_suppression_method_for_semantic_judgement():
    contract=_article104_semantic_contract()
    queue=_gate2_queue(
        "FZ123-104-1-AUPT-SUPPRESSION-METHOD",
        "АУПТ должна обеспечивать ликвидацию пожара поверхностным или объемным способом подачи огнетушащего вещества.",
        [{
            "evidence_id":"E-PB-104-VOLUMETRIC",
            "document":"Раздел ПД №9_ПБ.pdf",
            "page":42,
            "section":"ПБ",
            "text":"АУПТ обеспечивает тушение пожара объемным способом подачи огнетушащего вещества.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-104-1-AUPT-SUPPRESSION-METHOD"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True



def test_gate2_regex_matcher_accepts_explicit_bounded_pattern():
    contract={
        "version":"2.0",
        "required_groups":[{
            "id":"REGEX_PROBE",
            "label":"Regex probe",
            "scope":"SAME_EVIDENCE",
            "fields":["text"],
            "regex_any_of":[r"степень огнестойкости\s*[:—–-]?\s*ii(?![a-zа-я0-9])"],
        }],
    }
    queue=_gate2_queue(
        "TEST-REGEX-GATE2",
        "Проверка regex-предиката Gate 2.0.",
        [{
            "evidence_id":"E-REGEX-OK",
            "document":"ПБ.pdf",
            "page":1,
            "section":"ПБ",
            "text":"Степень огнестойкости: II.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["TEST-REGEX-GATE2"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["semantic_contract_ready"] is True


def test_gate2_regex_matcher_is_fail_closed_on_invalid_pattern():
    contract={
        "version":"2.0",
        "required_groups":[{
            "id":"BROKEN_REGEX",
            "label":"Broken regex must fail closed",
            "scope":"SAME_EVIDENCE",
            "fields":["text"],
            "regex_any_of":["("],
        }],
    }
    queue=_gate2_queue(
        "TEST-REGEX-GATE2-BROKEN",
        "Проверка fail-closed поведения regex-предиката Gate 2.0.",
        [{
            "evidence_id":"E-REGEX-BROKEN",
            "document":"ПБ.pdf",
            "page":1,
            "section":"ПБ",
            "text":"Любой текст не должен обходить поврежденный regex-контракт.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["TEST-REGEX-GATE2-BROKEN"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert decision["semantic_contract_missing_groups"] == ["Broken regex must fail closed"]



def _article30_semantic_contract():
    contracts={
        row["requirement_id"]:row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["FZ123-30-1-FIRE-RESISTANCE-TAXONOMY"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def test_gate2_article30_rejects_unrelated_roman_numeral_nearby():
    contract=_article30_semantic_contract()
    queue=_gate2_queue(
        "FZ123-30-1-FIRE-RESISTANCE-TAXONOMY",
        "Степень огнестойкости должна относиться к I, II, III, IV или V.",
        [{
            "evidence_id":"E-PB-30-FALSE-ROMAN",
            "document":"Раздел ПД №9_ПБ.pdf",
            "page":21,
            "section":"ПБ",
            "text":(
                "Степень огнестойкости здания определена проектом. "
                "Для другого параметра указан тип II."
            ),
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-30-1-FIRE-RESISTANCE-TAXONOMY"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "I–V" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_article30_accepts_explicit_fire_resistance_degree_with_roman_value():
    contract=_article30_semantic_contract()
    queue=_gate2_queue(
        "FZ123-30-1-FIRE-RESISTANCE-TAXONOMY",
        "Степень огнестойкости должна относиться к I, II, III, IV или V.",
        [{
            "evidence_id":"E-PB-30-II",
            "document":"Раздел ПД №9_ПБ.pdf",
            "page":21,
            "section":"ПБ",
            "text":"Степень огнестойкости проектируемого здания — II.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-30-1-FIRE-RESISTANCE-TAXONOMY"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True



def _article32_semantic_contract():
    contracts={
        row["requirement_id"]:row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["FZ123-32-1-FUNCTIONAL-FIRE-HAZARD-TAXONOMY"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def test_gate2_article32_requires_purpose_with_functional_class():
    contract=_article32_semantic_contract()
    queue=_gate2_queue(
        "FZ123-32-1-FUNCTIONAL-FIRE-HAZARD-TAXONOMY",
        "Класс функциональной пожарной опасности должен соответствовать назначению объекта.",
        [{
            "evidence_id":"E-PB-32-WITHOUT-PURPOSE",
            "document":"Раздел ПД №9_ПБ.pdf",
            "page":22,
            "section":"ПБ",
            "text":"Класс функциональной пожарной опасности: Ф5.1.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-32-1-FUNCTIONAL-FIRE-HAZARD-TAXONOMY"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "назначение объекта" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_article32_allows_explicit_purpose_and_functional_class_for_semantic_judgement():
    contract=_article32_semantic_contract()
    queue=_gate2_queue(
        "FZ123-32-1-FUNCTIONAL-FIRE-HAZARD-TAXONOMY",
        "Класс функциональной пожарной опасности должен соответствовать назначению объекта.",
        [{
            "evidence_id":"E-PB-32-F51",
            "document":"Раздел ПД №9_ПБ.pdf",
            "page":22,
            "section":"ПБ",
            "text":"Назначение объекта: производственное здание. Класс функциональной пожарной опасности: Ф5.1.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-32-1-FUNCTIONAL-FIRE-HAZARD-TAXONOMY"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True



def _article61_semantic_contract():
    contracts={
        row["requirement_id"]:row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["FZ123-61-3-AUPT-SELECTION-BASIS"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def test_gate2_article61_requires_all_selection_basis_groups():
    contract=_article61_semantic_contract()
    queue=_gate2_queue(
        "FZ123-61-3-AUPT-SELECTION-BASIS",
        "Тип АУПТ, огнетушащее вещество и способ подачи должны выбираться с учётом горючих материалов, объёмно-планировочных решений и параметров окружающей среды.",
        [
            {
                "evidence_id":"E-PB-61-SOLUTION",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":44,
                "section":"ПБ",
                "text":"Предусмотрена АУПТ. Огнетушащее вещество — вода. Способ подачи — спринклерный.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-PB-61-LOAD",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":45,
                "section":"ПБ",
                "text":"При выборе установки учтена пожарная нагрузка защищаемого помещения.",
                "retrieval_keyword_score":90,
                "retrieval_keyword_coverage":0.9,
            },
            {
                "evidence_id":"E-PB-61-PLANNING",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":46,
                "section":"ПБ",
                "text":"Учтены объемно-планировочные решения защищаемого помещения.",
                "retrieval_keyword_score":90,
                "retrieval_keyword_coverage":0.9,
            },
        ],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-61-3-AUPT-SELECTION-BASIS"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "параметры окружающей среды" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_article61_allows_distributed_complete_basis_for_semantic_judgement():
    contract=_article61_semantic_contract()
    queue=_gate2_queue(
        "FZ123-61-3-AUPT-SELECTION-BASIS",
        "Тип АУПТ, огнетушащее вещество и способ подачи должны выбираться с учётом горючих материалов, объёмно-планировочных решений и параметров окружающей среды.",
        [
            {
                "evidence_id":"E-PB-61-SOLUTION",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":44,
                "section":"ПБ",
                "text":"Предусмотрена АУПТ. Огнетушащее вещество — вода. Способ подачи — спринклерный.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-PB-61-LOAD",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":45,
                "section":"ПБ",
                "text":"При выборе установки учтена пожарная нагрузка защищаемого помещения.",
                "retrieval_keyword_score":90,
                "retrieval_keyword_coverage":0.9,
            },
            {
                "evidence_id":"E-PB-61-PLANNING",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":46,
                "section":"ПБ",
                "text":"Учтены объемно-планировочные решения защищаемого помещения.",
                "retrieval_keyword_score":90,
                "retrieval_keyword_coverage":0.9,
            },
            {
                "evidence_id":"E-PB-61-ENV",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":47,
                "section":"ПБ",
                "text":"При выборе установки учтены параметры окружающей среды в защищаемой зоне.",
                "retrieval_keyword_score":90,
                "retrieval_keyword_coverage":0.9,
            },
        ],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-61-3-AUPT-SELECTION-BASIS"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True
    assert len(decision["selected_evidence"]) == 4



def _article58_semantic_contract():
    contracts={
        row["requirement_id"]:row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["FZ123-58-2-FIRE-RESISTANCE-LIMITS"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def test_gate2_article58_requires_explicit_fire_resistance_limit_value():
    contract=_article58_semantic_contract()
    queue=_gate2_queue(
        "FZ123-58-2-FIRE-RESISTANCE-LIMITS",
        "Требуемые пределы огнестойкости строительных конструкций выбираются в зависимости от степени огнестойкости объекта.",
        [
            {
                "evidence_id":"E-PB-58-DEGREE",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":23,
                "section":"ПБ",
                "text":"Степень огнестойкости проектируемого здания — II.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-PB-58-NO-LIMIT",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":24,
                "section":"ПБ",
                "text":"Предел огнестойкости несущих строительных конструкций определен проектом.",
                "retrieval_keyword_score":90,
                "retrieval_keyword_coverage":0.9,
            },
        ],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-58-2-FIRE-RESISTANCE-LIMITS"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "R/RE/REI/EI/E" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_article58_allows_distributed_degree_and_limit_for_semantic_judgement():
    contract=_article58_semantic_contract()
    queue=_gate2_queue(
        "FZ123-58-2-FIRE-RESISTANCE-LIMITS",
        "Требуемые пределы огнестойкости строительных конструкций выбираются в зависимости от степени огнестойкости объекта.",
        [
            {
                "evidence_id":"E-PB-58-DEGREE",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":23,
                "section":"ПБ",
                "text":"Степень огнестойкости проектируемого здания — II.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-KR-58-R90",
                "document":"Раздел ПД №4_КР.pdf",
                "page":67,
                "section":"КР",
                "text":"Предел огнестойкости несущих колонн — R 90.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
        ],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-58-2-FIRE-RESISTANCE-LIMITS"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True
    assert len(decision["selected_evidence"]) == 2



def _article57_semantic_contract():
    contracts={
        row["requirement_id"]:row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["FZ123-57-1-CONSTRUCTION-FIRE-PERFORMANCE"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def test_gate2_article57_requires_explicit_construction_fire_hazard_class():
    contract=_article57_semantic_contract()
    queue=_gate2_queue(
        "FZ123-57-1-CONSTRUCTION-FIRE-PERFORMANCE",
        "Пределы огнестойкости и классы пожарной опасности основных строительных конструкций должны соответствовать степени огнестойкости и классу конструктивной пожарной опасности объекта.",
        [
            {
                "evidence_id":"E-PB-57-DEGREE",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":23,
                "section":"ПБ",
                "text":"Степень огнестойкости проектируемого здания — II.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-PB-57-C0",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":24,
                "section":"ПБ",
                "text":"Класс конструктивной пожарной опасности: С0.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-KR-57-R90",
                "document":"Раздел ПД №4_КР.pdf",
                "page":67,
                "section":"КР",
                "text":"Предел огнестойкости несущих колонн — R 90.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-KR-57-NO-K",
                "document":"Раздел ПД №4_КР.pdf",
                "page":68,
                "section":"КР",
                "text":"Класс пожарной опасности строительной конструкции определен проектом.",
                "retrieval_keyword_score":90,
                "retrieval_keyword_coverage":0.9,
            },
        ],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-57-1-CONSTRUCTION-FIRE-PERFORMANCE"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "К0–К3" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_article57_allows_complete_distributed_construction_fire_parameters():
    contract=_article57_semantic_contract()
    queue=_gate2_queue(
        "FZ123-57-1-CONSTRUCTION-FIRE-PERFORMANCE",
        "Пределы огнестойкости и классы пожарной опасности основных строительных конструкций должны соответствовать степени огнестойкости и классу конструктивной пожарной опасности объекта.",
        [
            {
                "evidence_id":"E-PB-57-DEGREE",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":23,
                "section":"ПБ",
                "text":"Степень огнестойкости проектируемого здания — II.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-PB-57-C0",
                "document":"Раздел ПД №9_ПБ.pdf",
                "page":24,
                "section":"ПБ",
                "text":"Класс конструктивной пожарной опасности: С0.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-KR-57-R90",
                "document":"Раздел ПД №4_КР.pdf",
                "page":67,
                "section":"КР",
                "text":"Предел огнестойкости несущих колонн — R 90.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
            {
                "evidence_id":"E-KR-57-K0",
                "document":"Раздел ПД №4_КР.pdf",
                "page":68,
                "section":"КР",
                "text":"Класс пожарной опасности строительной конструкции: К0.",
                "retrieval_keyword_score":100,
                "retrieval_keyword_coverage":1.0,
            },
        ],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["FZ123-57-1-CONSTRUCTION-FIRE-PERFORMANCE"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True
    assert len(decision["selected_evidence"]) == 4



def _sp12_semantic_contract():
    contracts={
        row["requirement_id"]:row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["SP12-4.1-CATEGORY-TAXONOMY"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def test_gate2_sp12_rejects_room_subcategory_for_building():
    contract=_sp12_semantic_contract()
    queue=_gate2_queue(
        "SP12-4.1-CATEGORY-TAXONOMY",
        "Категория должна быть явно задана по соответствующей шкале для помещения, здания или наружной установки.",
        [{
            "evidence_id":"E-TH-SP12-BUILDING-V1",
            "document":"Раздел ПД №5_ТХ.pdf",
            "page":31,
            "section":"ТХ",
            "text":"Категория здания по взрывопожарной и пожарной опасности — В1.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["SP12-4.1-CATEGORY-TAXONOMY"]

    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "допустимой шкалой СП 12" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_sp12_accepts_room_category_v1_for_semantic_judgement():
    contract=_sp12_semantic_contract()
    queue=_gate2_queue(
        "SP12-4.1-CATEGORY-TAXONOMY",
        "Категория должна быть явно задана по соответствующей шкале для помещения, здания или наружной установки.",
        [{
            "evidence_id":"E-TH-SP12-ROOM-V1",
            "document":"Раздел ПД №5_ТХ.pdf",
            "page":31,
            "section":"ТХ",
            "text":"Категория помещения по взрывопожарной и пожарной опасности — В1.",
            "retrieval_keyword_score":100,
            "retrieval_keyword_coverage":1.0,
        }],
        contract,
    )

    semantic=run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    decision=semantic["decisions"]["SP12-4.1-CATEGORY-TAXONOMY"]

    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True



def _sp48_516_semantic_contract():
    contracts = {
        row["requirement_id"]: row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["SP48-5.16-SUPPLY-TRANSPORT-TEP"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def _sp48_516_evidence(text, page):
    return {
        "evidence_id": f"E-POS-SP48-{page}",
        "document": "Раздел ПД №6_ПОС.pdf",
        "page": page,
        "section": "ПОС",
        "text": text,
        "retrieval_keyword_score": 100,
        "retrieval_keyword_coverage": 1.0,
    }


def _sp48_516_decision(evidence):
    queue = _gate2_queue(
        "SP48-5.16-SUPPLY-TRANSPORT-TEP",
        "Транспортная схема доставки основных строительных материалов должна "
        "быть обоснована сравнением технико-экономических показателей вариантов.",
        evidence,
        _sp48_516_semantic_contract(),
    )
    semantic = run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    return semantic, semantic["decisions"]["SP48-5.16-SUPPLY-TRANSPORT-TEP"]


def test_gate2_sp48_516_blocks_delivery_options_without_comparable_numeric_tep():
    semantic, decision = _sp48_516_decision([
        _sp48_516_evidence(
            "Сравнение вариантов доставки строительных материалов: "
            "вариант 1 — карьер Северный; вариант 2 — карьер Южный.", 35,
        ),
        _sp48_516_evidence(
            "По результатам сравнения вариантов поставки основных строительных "
            "материалов принята транспортная схема доставки с карьера Северный.", 36,
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert "технико-экономических" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_sp48_516_blocks_unjustified_selection_despite_cost_comparison():
    semantic, decision = _sp48_516_decision([
        _sp48_516_evidence(
            "Сравнение стоимости вариантов доставки щебня: "
            "вариант 1 — 1300 руб/т, вариант 2 — 1700 руб/т.", 35,
        ),
        _sp48_516_evidence(
            "Принята транспортная схема доставки щебня из карьера Северный.", 36,
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert "результатом сравнения" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_sp48_516_allows_addressable_comparison_and_justified_selection():
    semantic, decision = _sp48_516_decision([
        _sp48_516_evidence(
            "Сравнение стоимости вариантов доставки строительных материалов: "
            "вариант 1 — карьер Северный, стоимость 1300 руб/т; "
            "вариант 2 — карьер Южный, стоимость 1700 руб/т.", 35,
        ),
        _sp48_516_evidence(
            "По результатам сравнения вариантов поставки основных строительных "
            "материалов принята транспортная схема доставки с карьера Северный.", 36,
        ),
    ])
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True
    assert len(decision["selected_evidence"]) == 2


def test_gate2_sp48_516_rejects_evidence_not_owned_by_pos():
    evidence = [
        _sp48_516_evidence(
            "Сравнение стоимости вариантов доставки щебня: "
            "вариант 1 — 1300 руб/т, вариант 2 — 1700 руб/т.", 35,
        ),
        _sp48_516_evidence(
            "По результатам сравнения вариантов поставки принята схема "
            "доставки щебня из карьера Северный.", 36,
        ),
    ]
    for row in evidence:
        row["document"] = "Раздел ПД №2_ПЗУ.pdf"
        row["section"] = "ПЗУ"
    semantic, decision = _sp48_516_decision(evidence)
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_ready"] is False
    assert decision["semantic_contract_source_scope_satisfied"] is False



def _gost27751_101_semantic_contract():
    contracts = {
        row["requirement_id"]: row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["GOST27751-10.1-CLASS-LEVEL-GAMMA"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def _gost27751_101_evidence(text, page, section="КР"):
    return {
        "evidence_id": f"E-GOST27751-{page}",
        "document": f"Раздел ПД №4_{section}.pdf",
        "page": page,
        "section": section,
        "text": text,
        "retrieval_keyword_score": 100,
        "retrieval_keyword_coverage": 1.0,
    }


def _gost27751_101_decision(evidence):
    queue = _gate2_queue(
        "GOST27751-10.1-CLASS-LEVEL-GAMMA",
        "Для одного сооружения должны быть согласованы класс, "
        "уровень ответственности и коэффициент надёжности по ответственности.",
        evidence,
        _gost27751_101_semantic_contract(),
    )
    semantic = run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    return semantic, semantic["decisions"]["GOST27751-10.1-CLASS-LEVEL-GAMMA"]


def test_gate2_gost27751_101_blocks_stray_class_token_without_class_declaration():
    semantic, decision = _gost27751_101_decision([
        _gost27751_101_evidence(
            "В тексте встречается КС-2. Уровень ответственности: нормальный; "
            "коэффициент надежности по ответственности — 1,0.", 24,
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert "КС-1/КС-2/КС-3" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_gost27751_101_blocks_unspecified_responsibility_level():
    semantic, decision = _gost27751_101_decision([
        _gost27751_101_evidence(
            "Класс сооружения КС-2. Уровень ответственности установлен проектом; "
            "коэффициент надежности по ответственности — 1,0.", 24,
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert "явно установленным значением" in "; ".join(
        decision["semantic_contract_missing_groups"]
    )


def test_gate2_gost27751_101_blocks_numeric_value_without_gamma_binding():
    semantic, decision = _gost27751_101_decision([
        _gost27751_101_evidence(
            "Класс сооружения КС-2. Уровень ответственности: нормальный. "
            "Таблица показателей: площадь 1,0 тыс. м2. "
            "Коэффициент надежности по ответственности установлен проектом.", 24,
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert "конкретным числовым значением" in "; ".join(
        decision["semantic_contract_missing_groups"]
    )


def test_gate2_gost27751_101_allows_addressable_distributed_triple_for_judgement():
    semantic, decision = _gost27751_101_decision([
        _gost27751_101_evidence(
            "Для здания проборазделки класс сооружения — КС-2.", 24,
        ),
        _gost27751_101_evidence(
            "Для здания проборазделки уровень ответственности: нормальный; "
            "коэффициент надежности по ответственности — 1,0.", 25,
        ),
    ])
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True
    assert len(decision["selected_evidence"]) == 2


def test_gate2_gost27751_101_accepts_greek_gamma_symbol_as_typed_coefficient():
    semantic, decision = _gost27751_101_decision([
        _gost27751_101_evidence(
            "Для проектируемого склада класс сооружения КС-3. "
            "Уровень ответственности — повышенный; γn = 1,1.", 28,
        ),
    ])
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["semantic_contract_ready"] is True



def _gost27751_102_semantic_contract():
    contracts = {
        row["requirement_id"]: row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["GOST27751-10.2-ASSIGNMENT"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def _gost27751_102_evidence(text, page, document="Задание на проектирование ДСК.pdf", section="Задание на проектирование"):
    return {
        "evidence_id": f"E-GOST27751-102-{page}",
        "document": document,
        "page": page,
        "section": section,
        "text": text,
        "retrieval_keyword_score": 100,
        "retrieval_keyword_coverage": 1.0,
    }


def _gost27751_102_decision(evidence):
    queue = _gate2_queue(
        "GOST27751-10.2-ASSIGNMENT",
        "Класс сооружения, уровень ответственности и коэффициент надежности "
        "должны быть установлены в согласованном с заказчиком задании.",
        evidence,
        _gost27751_102_semantic_contract(),
    )
    semantic = run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    return semantic, semantic["decisions"]["GOST27751-10.2-ASSIGNMENT"]


def test_gate2_gost27751_102_rejects_pd_retelling_even_with_assignment_phrase():
    semantic, decision = _gost27751_102_decision([
        _gost27751_102_evidence(
            "В задании на проектирование класс сооружения — КС-2; "
            "уровень ответственности — нормальный; "
            "коэффициент надежности по ответственности — 1,0; "
            "согласовано с заказчиком.", 12,
            document="Раздел ПД №1_ПЗ.pdf", section="ПЗ",
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_source_scope_satisfied"] is False


def test_gate2_gost27751_102_blocks_missing_client_agreement():
    semantic, decision = _gost27751_102_decision([
        _gost27751_102_evidence(
            "Для навеса класс сооружения — КС-2; "
            "уровень ответственности — нормальный; "
            "коэффициент надежности по ответственности — 1,0.", 10,
        ),
        _gost27751_102_evidence(
            "Заказчик: ООО «Пример». Задание на проектирование.", 2,
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert "Согласование" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_gost27751_102_blocks_untyped_coefficient():
    semantic, decision = _gost27751_102_decision([
        _gost27751_102_evidence(
            "Для навеса класс сооружения — КС-2; "
            "уровень ответственности — нормальный; "
            "площадь объекта — 1,0 тыс. м2. "
            "Коэффициент надежности по ответственности установить проектом.", 10,
        ),
        _gost27751_102_evidence(
            "Согласовано с заказчиком ООО «Пример».", 2,
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert decision["state"] == "REVIEW_QUESTION"
    assert "Числовое значение" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_gost27751_102_blocks_missing_explicit_class_value():
    semantic, decision = _gost27751_102_decision([
        _gost27751_102_evidence(
            "Класс сооружения определить проектом; КС-2 указан в приложении. "
            "Уровень ответственности — нормальный. "
            "Коэффициент надежности по ответственности — 1,0.", 10,
        ),
        _gost27751_102_evidence(
            "Заказчик утвердил задание на проектирование.", 2,
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert "КС-1/КС-2/КС-3" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_gost27751_102_allows_distributed_assignment_evidence_for_semantic_review():
    semantic, decision = _gost27751_102_decision([
        _gost27751_102_evidence(
            "Для навеса класс сооружения — КС-2; "
            "уровень ответственности — нормальный; "
            "коэффициент надежности по ответственности — 1,0.", 10,
        ),
        _gost27751_102_evidence(
            "Согласовано с заказчиком ООО «Пример».", 2,
        ),
    ])
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True
    assert len(decision["selected_evidence"]) == 2


def test_gate2_gost27751_102_allows_technical_assignment_tz_shorthand():
    semantic, decision = _gost27751_102_decision([
        _gost27751_102_evidence(
            "Класс сооружения КС-3; уровень ответственности — повышенный; "
            "γn = 1,1. Заказчик утвердил задание на проектирование.", 7,
            document="ТЗ_ДСК.pdf", section="ТЗ",
        ),
    ])
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True



def _gost21101_731_semantic_contract():
    contracts = {
        row["requirement_id"]: row
        for row in default_foundation().contracts()
    }
    return dict(
        contracts["GOST21101-2026-7.3.1-CHANGE-NUMBER"]
        ["evidence_contract"]["semantic_proof_contract"]
    )


def _gost21101_731_evidence(text, page=1, document="Раздел ПД №1_ПЗ.pdf", section="ПЗ"):
    return {
        "evidence_id": f"E-GOST21101-731-{page}",
        "document": document,
        "page": page,
        "section": section,
        "text": text,
        "retrieval_keyword_score": 100,
        "retrieval_keyword_coverage": 1.0,
    }


def _gost21101_731_decision(evidence):
    queue = _gate2_queue(
        "GOST21101-2026-7.3.1-CHANGE-NUMBER",
        "Обозначение изменения присваивается документу целиком "
        "по одному разрешению; исключение — коды по СТО.",
        evidence,
        _gost21101_731_semantic_contract(),
    )
    semantic = run_normative_semantic_proof(
        queue,
        judge_provider=FakeProvider("Judge-A"),
        critic_provider=FakeProvider("Critic-B"),
        limit=8,
    )
    return semantic, semantic["decisions"]["GOST21101-2026-7.3.1-CHANGE-NUMBER"]


def test_gate2_gost21101_731_rejects_generic_change_summary_not_source_document():
    semantic, decision = _gost21101_731_decision([
        _gost21101_731_evidence(
            "Таблица регистрации изменений. Изм. 2. Изменены листы 4 и 5.",
            document="Журнал_изменений.pdf", section="Журнал",
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert decision["semantic_contract_source_scope_satisfied"] is False


def test_gate2_gost21101_731_rejects_change_mention_without_register_context():
    semantic, decision = _gost21101_731_decision([
        _gost21101_731_evidence("Изм. 2. Скорректированы листы 4 и 5."),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"
    assert "адресной таблице" in "; ".join(decision["semantic_contract_missing_groups"])


def test_gate2_gost21101_731_rejects_register_without_typed_change_number():
    semantic, decision = _gost21101_731_decision([
        _gost21101_731_evidence(
            "Таблица регистрации изменений. Номер документа 5. Дата 08.10.2026."
        ),
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"


def test_gate2_gost21101_731_rejects_change_zero_as_ordinal():
    semantic, decision = _gost21101_731_decision([
        _gost21101_731_evidence("Таблица регистрации изменений. Изм. 0.")
    ])
    assert semantic["verified_ok"] == 0
    assert semantic["contract_gate_blocked"] == 1
    assert decision["state"] == "REVIEW_QUESTION"


def test_gate2_gost21101_731_accepts_number_within_registration_table_for_judgement():
    semantic, decision = _gost21101_731_decision([
        _gost21101_731_evidence(
            "Таблица регистрации изменений. Изм. 2. "
            "Изменены листы 4 и 5 по разрешению 17.",
            document="Раздел ПД №1_ПЗ.pdf", section="ПЗ",
        ),
    ])
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True


def test_gate2_gost21101_731_accepts_organisational_alphanumeric_change_code():
    semantic, decision = _gost21101_731_decision([
        _gost21101_731_evidence(
            "Таблица изменений. Изм. А-2. "
            "Буквенно-цифровые коды изменений установлены СТО организации.",
            document="04_КР.pdf", section="КР",
        ),
    ])
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True


def test_gate2_gost21101_731_accepts_change_stamped_in_drawing_revision_box():
    semantic, decision = _gost21101_731_decision([
        _gost21101_731_evidence(
            "Изм. Кол. уч. Лист № док. Подп. Дата Изм. 1; 2 (Зам.).",
            document="02_АР.pdf", section="АР",
        ),
    ])
    assert semantic["verified_ok"] == 1
    assert semantic["contract_gate_blocked"] == 0
    assert decision["state"] == "VERIFIED_OK"
    assert decision["semantic_contract_ready"] is True
