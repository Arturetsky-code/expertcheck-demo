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
