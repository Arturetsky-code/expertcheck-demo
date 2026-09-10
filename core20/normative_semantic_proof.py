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


ENGINE_VERSION = "20.0-alpha9-normative-semantic-proof-multi-evidence"


def _fingerprint(queue: list[dict[str, Any]]) -> str:
    payload=[]
    for packet in queue or []:
        evidence=list(packet.get("evidence") or [])
        payload.append({
            "packet_id":packet.get("packet_id"),
            "requirement_id":packet.get("requirement_id"),
            "requirement":packet.get("requirement"),
            "proof_type":packet.get("proof_type"),
            "evidence":[{
                "evidence_id":row.get("evidence_id"),
                "document":row.get("document"),
                "page":row.get("page"),
                "text":str(row.get("text") or "")[:1200],
            } for row in evidence],
        })
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8","ignore")).hexdigest()


def queue_fingerprint(queue:list[dict[str,Any]]|None)->str:
    return _fingerprint(list(queue or []))


def _norm_identity(value:Any)->str:
    return " ".join(str(value or "").strip().casefold().split())


def _independent(
    judge_provider:str,
    critic_provider:str,
    judge_model:str="",
    critic_model:str="",
)->tuple[bool,str]:
    jp=_norm_identity(judge_provider)
    cp=_norm_identity(critic_provider)
    jm=_norm_identity(judge_model)
    cm=_norm_identity(critic_model)
    if not jp or not cp:
        return False,"Фактические провайдеры Judge/Critic не подтверждены."
    if jp==cp:
        return False,"Judge и Critic фактически обслужены одним AI-провайдером."
    if jm and cm and jm==cm:
        return False,"Judge и Critic используют одну и ту же фактическую модель; независимый proof удержан."
    return True,"Провайдеры независимы; при доступных идентификаторах модели также различаются."


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
            "retrieval_score":int(row.get("retrieval_keyword_score") or 100),
            "owner_match":None,
            "property_match":None,
            "entity_binding_state":"NOT_REQUIRED",
            "property_binding_state":"NOT_REQUIRED",
            "required_modality":"TEXT_OR_TABLE",
            "source_modality":"TEXT_OR_TABLE",
            "modality_gate_state":"PASSED",
            "missing_critical_qualifiers":[],
            "contract_ready_for_judgement":True,
            "semantic_token_coverage":float(row.get("retrieval_keyword_coverage") or 1.0),
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
            "Retrieval is not proof. SUPPORTS is allowed only when cited addressable evidence directly proves the whole verified normative requirement. "
            "The Judge may cite one or several candidates. CONTRADICTS or missing evidence is not an automatic project non-compliance in Alpha 9."
        ),
    }


def _selected_evidence(packet:dict[str,Any],ids:list[str])->list[dict[str,Any]]:
    wanted={str(value) for value in ids}
    result=[]
    for row in packet.get("evidence") or []:
        if str(row.get("evidence_id") or "") not in wanted:
            continue
        result.append({
            "evidence_id":row.get("evidence_id") or "",
            "document":row.get("document") or "",
            "page":row.get("page"),
            "source_locator":row.get("source_locator") or "",
            "fragment":str(row.get("text") or "")[:500],
        })
    return result


def run_normative_semantic_proof(
    queue:list[dict[str,Any]]|None,
    *,
    judge_provider:Any=None,
    critic_provider:Any=None,
    limit:int=24,
)->dict[str,Any]:
    """Run bounded independent semantic proof over normative packets.

    Only SUPPORTS accepted by an independent Critic can promote a semantic
    normative contract to VERIFIED_OK. Negative semantic outcomes remain review
    questions until a dedicated machine-readable negative conflict contract is
    available.
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
        "evidence_candidates":sum(len(packet.get("evidence") or []) for packet in packets),
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
    configured_judge_model=str(judge_preflight.get("model") or "")
    configured_critic_model=str(critic_preflight.get("model") or "")
    preflight_independent,preflight_reason=_independent(
        configured_judge,configured_critic,configured_judge_model,configured_critic_model,
    )
    # Missing model IDs do not block preflight; actual generation responses are
    # checked again. Same provider is always a hard stop before project calls.
    if _norm_identity(configured_judge)==_norm_identity(configured_critic):
        base["provider_errors"]=[preflight_reason]
        return base
    if configured_judge_model and configured_critic_model and not preflight_independent:
        base["provider_errors"]=[preflight_reason]
        return base

    public=[_public_packet(packet) for packet in packets]
    raw_judges,judge_errors,_=_call_batches(judge_provider,public,critic=False,batch_size=4,max_calls=24)
    critic_packets=[]
    validated_judges={}
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
        judge_model=str(judge.get("model") or configured_judge_model)
        critic_model=str(critic.get("model") or configured_critic_model)
        independent,independence_reason=_independent(actual_judge,actual_critic,judge_model,critic_model)
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
            if not independent and judge.get("valid") and str(judge.get("verdict") or "").upper()=="SUPPORTS":
                reason=independence_reason
            elif str(judge.get("verdict") or "").upper()!="SUPPORTS":
                reason=str(judge.get("reason") or "Недостаточно доказательств для смыслового подтверждения.")
            else:
                reason=str(critic.get("reason") or "Независимый Critic не подтвердил смысловое доказательство.")
        selected_ids=list(judge.get("evidence_ids") or [])
        decisions[requirement_id]={
            "requirement_id":requirement_id,
            "packet_id":pid,
            "state":state,
            "reason":reason,
            "judge_verdict":str(judge.get("verdict") or "INSUFFICIENT"),
            "judge_confidence":judge.get("confidence") or 0,
            "judge_provider":actual_judge,
            "judge_model":judge_model,
            "critic_accept":bool(critic.get("valid")),
            "critic_confidence":critic.get("confidence") or 0,
            "critic_provider":actual_critic,
            "critic_model":critic_model,
            "independent":independent,
            "independence_reason":independence_reason,
            "evidence_ids":selected_ids,
            "selected_evidence":_selected_evidence(packet,selected_ids),
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
        row["semantic_selected_evidence"]=list(decision.get("selected_evidence") or [])
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
