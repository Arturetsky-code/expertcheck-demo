from __future__ import annotations

import hashlib
import json
from typing import Any

from core.semantic_evidence_engine import (
    _call_batches,
    _public_packet,
    _validate_critic,
    _validate_judge,
    preflight_provider,
)


ENGINE_VERSION = "20.0-alpha9-normative-semantic-proof"


def _fingerprint(queue: list[dict[str, Any]]) -> str:
    payload=[]
    for packet in queue or []:
        evidence=list(packet.get("evidence") or [])
        payload.append({
            "packet_id":packet.get("packet_id"),
            "requirement_id":packet.get("requirement_id"),
            "requirement":packet.get("requirement"),
            "evidence":[{
                "document":row.get("document"),
                "page":row.get("page"),
                "text":str(row.get("text") or "")[:1200],
            } for row in evidence],
        })
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8","ignore")).hexdigest()


def queue_fingerprint(queue:list[dict[str,Any]]|None)->str:
    return _fingerprint(list(queue or []))


def _as_semantic_packet(packet:dict[str,Any])->dict[str,Any]:
    evidence=[]
    for row in packet.get("evidence") or []:
        evidence.append({
            "evidence_id":str(row.get("evidence_id") or ""),
            "document":str(row.get("document") or ""),
            "page":row.get("page"),
            "section":str(row.get("section") or ""),
            "text":str(row.get("text") or "")[:1200],
            "ai_evidence_text":str(row.get("text") or "")[:1200],
            "source_locator":str(row.get("source_locator") or ""),
            "kind":"NORMATIVE_EVIDENCE",
            "retrieval_score":100,
            "owner_match":None,
            "property_match":None,
            "entity_binding_state":"NOT_REQUIRED",
            "property_binding_state":"NOT_REQUIRED",
            "required_modality":"TEXT_OR_TABLE",
            "source_modality":"TEXT_OR_TABLE",
            "modality_gate_state":"PASSED",
            "missing_critical_qualifiers":[],
            "contract_ready_for_judgement":True,
            "semantic_token_coverage":1.0,
        })
    return {
        "packet_id":str(packet.get("packet_id") or ""),
        "domain":"normative",
        "requirement":str(packet.get("requirement") or ""),
        "atomic_kind":"SEMANTIC_REQUIREMENT",
        "object":"",
        "property_code":"",
        "required_value":None,
        "unit":"",
        "scope":"PROJECT_WIDE",
        "expected_sections":list(packet.get("sections") or []),
        "required_modality":"TEXT_OR_TABLE",
        "critical_qualifiers":[],
        "binding_contract":{
            "scope":"PROJECT_WIDE",
            "requires_same_owner":False,
            "requires_same_parameter":False,
            "expected_entity":"",
            "expected_property_code":"",
        },
        "checker":{
            "checker_family":"NORMATIVE_SEMANTIC_PROOF",
            "checker_mode":"INDEPENDENT_CONSENSUS",
            "consensus_eligible":True,
        },
        "evidence_level":"L4",
        "evidence_contract_state":"SATISFIED" if evidence else "UNSATISFIED",
        "contract_ready_evidence_ids":[row["evidence_id"] for row in evidence if row.get("evidence_id")],
        "evidence":evidence,
        "policy":(
            "Retrieval is not proof. SUPPORTS is allowed only when the cited fragment directly proves the whole verified normative requirement. "
            "CONTRADICTS or missing evidence is not an automatic project non-compliance in Alpha 9."
        ),
    }


def run_normative_semantic_proof(
    queue:list[dict[str,Any]]|None,
    *,
    judge_provider:Any=None,
    critic_provider:Any=None,
    limit:int=24,
)->dict[str,Any]:
    """Run a bounded independent semantic proof over Alpha 9 normative packets.

    Only SUPPORTS accepted by an actually independent Critic can promote a
    normative contract to VERIFIED_OK. CONTRADICTS remains a specialist review
    question until a dedicated negative normative conflict contract is added.
    """
    source=[dict(x) for x in (queue or []) if isinstance(x,dict)]
    fp=_fingerprint(source)
    packets=[_as_semantic_packet(x) for x in source[:max(0,int(limit or 0))]]
    packets=[x for x in packets if x.get("evidence")]
    base={
        "version":ENGINE_VERSION,
        "fingerprint":fp,
        "queue_total":len(source),
        "selected":len(packets),
        "decisions":{},
        "verified_ok":0,
        "review_questions":len(source),
        "provider_errors":[],
        "preflight":{},
        "principle":"Only independent Judge/Critic SUPPORTS may promote semantic normative proof; no automatic negative verdict is emitted.",
    }
    if not packets or judge_provider is None or critic_provider is None:
        return base

    judge_preflight=preflight_provider(judge_provider,"JUDGE",structured=True)
    critic_preflight=preflight_provider(critic_provider,"CRITIC",structured=True)
    base["preflight"]={"judge":judge_preflight,"critic":critic_preflight}
    if not judge_preflight.get("ok") or not critic_preflight.get("ok"):
        base["provider_errors"]=[
            text for text in (
                str(judge_preflight.get("error") or ""),
                str(critic_preflight.get("error") or ""),
            ) if text
        ]
        return base

    configured_judge=str(judge_preflight.get("actual_provider") or judge_preflight.get("configured_provider") or "")
    configured_critic=str(critic_preflight.get("actual_provider") or critic_preflight.get("configured_provider") or "")
    if configured_judge and configured_critic and configured_judge==configured_critic:
        base["provider_errors"]=["Judge и Critic фактически обслужены одним провайдером; независимый нормативный proof запрещён."]
        return base

    public=[_public_packet(packet) for packet in packets]
    raw_judges,judge_errors,_=_call_batches(judge_provider,public,critic=False,batch_size=4,max_calls=24)
    critic_packets=[]
    validated_judges={}
    by_id={packet["packet_id"]:packet for packet in packets}
    for packet in packets:
        pid=packet["packet_id"]
        judge=_validate_judge(packet,raw_judges.get(pid))
        validated_judges[pid]=judge
        if judge.get("valid") and str(judge.get("verdict") or "").upper()=="SUPPORTS":
            cited={str(x) for x in judge.get("evidence_ids") or []}
            critic_packet={**packet,"evidence":[row for row in packet.get("evidence") or [] if str(row.get("evidence_id") or "") in cited]}
            public_critic=_public_packet(critic_packet)
            public_critic["judge_decision"]={
                "packet_id":pid,
                "verdict":"SUPPORTS",
                "evidence_ids":list(judge.get("evidence_ids") or []),
                "same_entity":judge.get("same_entity"),
                "same_property":judge.get("same_property"),
                "qualifiers_satisfied":judge.get("qualifiers_satisfied"),
                "modality_satisfied":judge.get("modality_satisfied"),
                "confidence":judge.get("confidence"),
                "reason":str(judge.get("reason") or ""),
            }
            critic_packets.append(public_critic)

    raw_critics,critic_errors,_=_call_batches(critic_provider,critic_packets,critic=True,batch_size=4,max_calls=24)
    decisions={}
    verified=0
    for packet in packets:
        pid=packet["packet_id"]
        requirement_id=pid.removeprefix("NORM-")
        judge=validated_judges.get(pid) or {}
        critic=_validate_critic(packet,judge,raw_critics.get(pid))
        actual_judge=str(judge.get("provider") or configured_judge)
        actual_critic=str(critic.get("provider") or configured_critic)
        independent=bool(actual_judge and actual_critic and actual_judge!=actual_critic)
        supports=bool(
            judge.get("valid")
            and str(judge.get("verdict") or "").upper()=="SUPPORTS"
            and critic.get("valid")
            and independent
        )
        if supports:
            verified+=1
            state="VERIFIED_OK"
            reason=(
                "Содержательное выполнение verified-clause подтверждено адресным evidence, независимым Judge и Critic "
                "и программным proof-gate."
            )
        else:
            state="REVIEW_QUESTION"
            reason=(
                str(judge.get("reason") or "Недостаточно доказательств для смыслового подтверждения.")
                if str(judge.get("verdict") or "").upper()!="SUPPORTS"
                else str(critic.get("reason") or "Независимый Critic не подтвердил смысловое доказательство.")
            )
        decisions[requirement_id]={
            "requirement_id":requirement_id,
            "packet_id":pid,
            "state":state,
            "reason":reason,
            "judge_verdict":str(judge.get("verdict") or "INSUFFICIENT"),
            "judge_confidence":judge.get("confidence") or 0,
            "judge_provider":actual_judge,
            "judge_model":judge.get("model") or "",
            "critic_accept":bool(critic.get("valid")),
            "critic_confidence":critic.get("confidence") or 0,
            "critic_provider":actual_critic,
            "critic_model":critic.get("model") or "",
            "independent":independent,
            "evidence_ids":list(judge.get("evidence_ids") or []),
            "blocking_concerns":list(critic.get("blocking_concerns") or []),
        }
    base["decisions"]=decisions
    base["verified_ok"]=verified
    base["review_questions"]=max(0,len(source)-verified)
    base["provider_errors"]=list(dict.fromkeys([*judge_errors,*critic_errors]))
    return base


def apply_normative_semantic_proof(
    proof_result:dict[str,Any],
    semantic_result:dict[str,Any]|None,
)->dict[str,Any]:
    """Apply a persisted semantic checkpoint only to the exact current queue."""
    result=dict(proof_result or {})
    rows=[dict(x) for x in (result.get("rows") or [])]
    semantic=dict(semantic_result or {})
    queue=list(result.get("semantic_queue") or [])
    expected=_fingerprint(queue)
    if not semantic or semantic.get("fingerprint")!=expected:
        result["semantic_proof_applied"]=0
        result["semantic_proof_stale"]=bool(semantic)
        return result
    decisions=dict(semantic.get("decisions") or {})
    applied=0
    for row in rows:
        rid=str(row.get("requirement_id") or "")
        decision=decisions.get(rid)
        if not isinstance(decision,dict):
            continue
        row["semantic_proof"]={k:v for k,v in decision.items() if k!="requirement_id"}
        if decision.get("state")=="VERIFIED_OK" and row.get("proof_state")=="SEMANTIC_PROOF_REQUIRED":
            row["kind"]="VERIFIED_OK"
            row["state"]="Подтверждено"
            row["proof_state"]="SEMANTIC_CONSENSUS_PROOF"
            row["reason_code"]="NORMATIVE_SEMANTIC_PROOF_CONFIRMED"
            row["reason"]=str(decision.get("reason") or "Нормативное требование подтверждено независимым semantic proof.")
            applied+=1
    result["rows"]=rows
    result["verified_ok"]=sum(str(x.get("kind") or "").upper()=="VERIFIED_OK" for x in rows)
    result["review_questions"]=sum(str(x.get("kind") or "").upper()=="REVIEW_QUESTION" for x in rows)
    result["system_limitations"]=sum(str(x.get("kind") or "").upper()=="SYSTEM_LIMITATION" for x in rows)
    result["project_findings"]=sum(str(x.get("kind") or "").upper()=="PROJECT_FINDING" for x in rows)
    result["semantic_proof_applied"]=applied
    result["semantic_proof_stale"]=False
    result["semantic_proof_summary"]={k:v for k,v in semantic.items() if k!="decisions"}
    return result
