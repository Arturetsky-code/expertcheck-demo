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


ENGINE_VERSION = "20.0-alpha10-semantic-proof-gate2"


def _fingerprint(queue: list[dict[str, Any]]) -> str:
    payload=[]
    for packet in queue or []:
        evidence=list(packet.get("evidence") or [])
        payload.append({
            "packet_id":packet.get("packet_id"),
            "requirement_id":packet.get("requirement_id"),
            "requirement":packet.get("requirement"),
            "proof_type":packet.get("proof_type"),
            "semantic_proof_contract":dict(packet.get("semantic_proof_contract") or {}),
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


def _packet_fingerprint(packet:dict[str,Any])->str:
    evidence=list(packet.get("evidence") or [])
    payload={
        "packet_id":packet.get("packet_id"),
        "requirement_id":packet.get("requirement_id"),
        "requirement":packet.get("requirement"),
        "proof_type":packet.get("proof_type"),
        "semantic_proof_contract":dict(packet.get("semantic_proof_contract") or {}),
        "evidence":[{
            "evidence_id":row.get("evidence_id"),
            "document":row.get("document"),
            "page":row.get("page"),
            "text":str(row.get("text") or "")[:1200],
        } for row in evidence],
    }
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8","ignore")).hexdigest()


def _requirement_fingerprint(packet:dict[str,Any])->str:
    payload={
        "requirement_id":packet.get("requirement_id"),
        "requirement":packet.get("requirement"),
        "proof_type":packet.get("proof_type"),
        "semantic_proof_contract":dict(packet.get("semantic_proof_contract") or {}),
    }
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8","ignore")).hexdigest()


def _selected_proof_fingerprint(
    packet:dict[str,Any],
    selected_evidence:list[dict[str,Any]]|None,
)->str:
    payload={
        "requirement_fingerprint":_requirement_fingerprint(packet),
        "selected_evidence":[{
            "document":row.get("document") or "",
            "page":row.get("page"),
            "fragment":str(row.get("fragment") or row.get("text") or "")[:500],
        } for row in (selected_evidence or [])],
    }
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8","ignore")).hexdigest()


def _selected_evidence_still_available(
    packet:dict[str,Any],
    selected_evidence:list[dict[str,Any]]|None,
)->bool:
    selected=[dict(row) for row in (selected_evidence or []) if isinstance(row,dict)]
    if not selected:
        return False
    current=[dict(row) for row in (packet.get("evidence") or []) if isinstance(row,dict)]
    for old in selected:
        old_doc=str(old.get("document") or "")
        old_page=old.get("page")
        old_fragment=" ".join(str(old.get("fragment") or old.get("text") or "").split())
        if not old_doc or old_page in (None,"") or not old_fragment:
            return False
        found=False
        for row in current:
            if str(row.get("document") or "")!=old_doc or row.get("page")!=old_page:
                continue
            current_text=" ".join(str(row.get("text") or row.get("fragment") or "").split())
            if old_fragment in current_text:
                found=True
                break
        if not found:
            return False
    return True


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


def _norm_contract_text(value:Any)->str:
    return " ".join(
        str(value or "").replace("ё","е").replace("\xa0"," ").casefold().split()
    )


def _evidence_text(row:dict[str,Any],fields:list[str]|None=None)->str:
    requested=list(fields or ["text"])
    values=[]
    for field in requested:
        if field=="text":
            values.append(row.get("text") or row.get("fragment") or "")
        elif field=="document":
            values.append(row.get("document") or "")
        elif field=="section":
            values.append(row.get("section") or "")
        elif field=="source_locator":
            values.append(row.get("source_locator") or "")
        else:
            values.append(row.get(field) or "")
    return _norm_contract_text(" ".join(str(value or "") for value in values))


def _terms_match(text:str,values:list[Any]|None)->bool:
    terms=[_norm_contract_text(value) for value in (values or []) if _norm_contract_text(value)]
    return any(term in text for term in terms) if terms else True


def _group_matches_text(group:dict[str,Any],text:str)->bool:
    any_of=list(group.get("any_of") or [])
    all_of=list(group.get("all_of") or [])
    all_of_groups=[
        list(value) for value in (group.get("all_of_groups") or [])
        if isinstance(value,(list,tuple))
    ]
    configured=bool(any_of or all_of or all_of_groups)
    if not configured:
        return False
    if any_of and not _terms_match(text,any_of):
        return False
    for value in all_of:
        term=_norm_contract_text(value)
        if term and term not in text:
            return False
    for alternatives in all_of_groups:
        if not _terms_match(text,alternatives):
            return False
    return True


def _contract_group_result(
    group:dict[str,Any],
    selected:list[dict[str,Any]],
)->dict[str,Any]:
    fields=[str(value) for value in (group.get("fields") or ["text"]) if str(value)]
    scope=str(group.get("scope") or "COLLECTIVE").upper()
    if scope=="SAME_EVIDENCE":
        matched=any(
            _group_matches_text(group,_evidence_text(row,fields))
            for row in selected
        )
    else:
        matched=_group_matches_text(
            group,
            " ".join(_evidence_text(row,fields) for row in selected),
        )
    return {
        "id":str(group.get("id") or ""),
        "label":str(group.get("label") or group.get("id") or "Обязательный смысловой компонент"),
        "scope":scope,
        "matched":bool(matched),
    }


def _source_scope_result(
    scope:dict[str,Any],
    selected:list[dict[str,Any]],
)->dict[str,Any]:
    if not scope:
        return {"configured":False,"matched":True,"label":""}
    fields=[str(value) for value in (scope.get("fields") or ["document","section","text"]) if str(value)]
    mode=str(scope.get("mode") or "ANY_SELECTED_EVIDENCE").upper()
    matcher={
        "any_of":list(scope.get("any_of") or []),
        "all_of":list(scope.get("all_of") or []),
        "all_of_groups":list(scope.get("all_of_groups") or []),
    }
    per_row=[
        _group_matches_text(matcher,_evidence_text(row,fields))
        for row in selected
    ]
    matched=all(per_row) if mode=="ALL_SELECTED_EVIDENCE" else any(per_row)
    return {
        "configured":True,
        "matched":bool(matched),
        "label":str(scope.get("label") or "Допустимый источник доказательства"),
        "mode":mode,
        "fields":fields,
    }


def _semantic_contract_gate(
    packet:dict[str,Any],
    evidence_ids:list[str]|None,
)->dict[str,Any]:
    contract=dict(packet.get("semantic_proof_contract") or {})
    if not contract:
        return {
            "configured":False,
            "version":"",
            "ready":True,
            "selected_evidence_count":len(evidence_ids or []),
            "minimum_selected_evidence":0,
            "source_scope_satisfied":True,
            "missing_groups":[],
            "group_results":[],
            "reason":"Для требования не задан дополнительный декларативный semantic proof-contract.",
        }

    wanted={str(value) for value in (evidence_ids or []) if str(value)}
    selected=[
        dict(row) for row in (packet.get("evidence") or [])
        if str(row.get("evidence_id") or "") in wanted
    ]
    minimum=max(1,int(contract.get("minimum_selected_evidence") or 1))
    source_result=_source_scope_result(dict(contract.get("source_scope") or {}),selected)
    group_results=[
        _contract_group_result(dict(group),selected)
        for group in (contract.get("required_groups") or [])
        if isinstance(group,dict)
    ]
    missing=[
        str(row.get("label") or row.get("id") or "")
        for row in group_results
        if not row.get("matched")
    ]
    count_ok=len(selected)>=minimum
    ready=bool(
        count_ok
        and source_result.get("matched")
        and not missing
    )
    reasons=[]
    if not count_ok:
        reasons.append(
            f"выбрано доказательств {len(selected)}, требуется не менее {minimum}"
        )
    if not source_result.get("matched"):
        reasons.append(
            "не подтверждён допустимый источник: "
            + str(source_result.get("label") or "источник доказательства")
        )
    if missing:
        reasons.append("не доказаны обязательные компоненты: " + "; ".join(missing))
    return {
        "configured":True,
        "version":str(contract.get("version") or "2.0"),
        "ready":ready,
        "selected_evidence_count":len(selected),
        "minimum_selected_evidence":minimum,
        "source_scope_satisfied":bool(source_result.get("matched")),
        "source_scope":source_result,
        "missing_groups":missing,
        "group_results":group_results,
        "reason":(
            "Semantic Proof Gate 2.0 пройден."
            if ready else
            "Semantic Proof Gate 2.0 удержал автоматическое подтверждение: "
            + "; ".join(reasons)
            + "."
        ),
    }


def _semantic_contract_qualifiers(contract:dict[str,Any])->list[str]:
    values=[]
    source_scope=dict(contract.get("source_scope") or {})
    source_label=str(source_scope.get("label") or "").strip()
    if source_label:
        values.append(source_label)
    for group in contract.get("required_groups") or []:
        if not isinstance(group,dict):
            continue
        label=str(group.get("label") or group.get("id") or "").strip()
        if label:
            values.append(label)
    return list(dict.fromkeys(values))


def _as_semantic_packet(packet:dict[str,Any])->dict[str,Any]:
    semantic_contract=dict(packet.get("semantic_proof_contract") or {})
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
            "set_element_id":str(row.get("set_element_id") or ""),
            "set_element_label":str(row.get("set_element_label") or ""),
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
        "critical_qualifiers":_semantic_contract_qualifiers(semantic_contract),
        "semantic_proof_contract":semantic_contract,
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
            "The Judge may cite one or several candidates. A declarative Semantic Proof Gate 2.0 is applied after Judge selection and before Critic promotion. CONTRADICTS or missing evidence is not an automatic project non-compliance."
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
    checkpoint:dict[str,Any]|None=None,
)->dict[str,Any]:
    """Run bounded independent semantic proof over normative packets.

    Only SUPPORTS accepted by an independent Critic can promote a semantic
    normative contract to VERIFIED_OK. Negative semantic outcomes remain review
    questions until a dedicated machine-readable negative conflict contract is
    available.
    """
    source=[dict(x) for x in (queue or []) if isinstance(x,dict)]
    fp=_fingerprint(source)
    pending_ids={
        str(packet.get("requirement_id") or str(packet.get("packet_id") or "").removeprefix("NORM-"))
        for packet in source
        if str(packet.get("requirement_id") or packet.get("packet_id") or "")
    }
    previous=dict(checkpoint or {})
    previous_decisions={
        str(key):dict(value)
        for key,value in (previous.get("decisions") or {}).items()
        if isinstance(value,dict)
    }
    # The queue supplied by NormativeExecutionEngine is already the pending-only
    # queue after checkpoint validation. Therefore any previous decision whose
    # requirement is absent from this queue is a completed/reusable decision and
    # must survive the next bounded wave.
    preserved_decisions={
        rid:decision
        for rid,decision in previous_decisions.items()
        if rid not in pending_ids
    }
    source_packet_fingerprints={
        str(packet.get("packet_id") or ""):_packet_fingerprint(packet)
        for packet in source
        if str(packet.get("packet_id") or "")
    }
    selected_source=source[:max(0,int(limit or 0))]
    packets=[_as_semantic_packet(x) for x in selected_source]
    packets=[x for x in packets if x.get("evidence")]
    base={
        "version":ENGINE_VERSION,
        "fingerprint":fp,
        "queue_total":len(source),
        "selected":len(packets),
        "evidence_candidates":sum(len(packet.get("evidence") or []) for packet in packets),
        "decisions":dict(preserved_decisions),
        "completed_before":len(preserved_decisions),
        "new_decisions":0,
        "pending_unprocessed":len(source),
        "newly_verified_ok":0,
        "verified_ok":sum(
            str(value.get("state") or "").upper()=="VERIFIED_OK"
            for value in preserved_decisions.values()
        ),
        "review_questions":sum(
            str(value.get("state") or "").upper()=="REVIEW_QUESTION"
            for value in preserved_decisions.values()
        )+len(source),
        "provider_errors":[],
        "preflight":{},
        "contract_gate_blocked":0,
        "principle":"Only independent Judge/Critic SUPPORTS that also pass Semantic Proof Gate 2.0 may promote semantic normative proof; completed decisions are preserved across bounded resumable waves; no automatic negative verdict is emitted.",
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
    semantic_contract_gates={}
    for packet in packets:
        pid=packet["packet_id"]
        judge=_validate_judge(packet,raw_judges.get(pid))
        validated_judges[pid]=judge
        contract_gate=_semantic_contract_gate(packet,list(judge.get("evidence_ids") or []))
        semantic_contract_gates[pid]=contract_gate
        if (
            judge.get("valid")
            and str(judge.get("verdict") or "").upper()=="SUPPORTS"
        ):
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
        contract_gate=semantic_contract_gates.get(pid) or _semantic_contract_gate(
            packet,list(judge.get("evidence_ids") or [])
        )
        critic=_validate_critic(packet,judge,raw_critics.get(pid))
        actual_judge=str(judge.get("provider") or configured_judge)
        actual_critic=str(critic.get("provider") or configured_critic)
        judge_model=str(judge.get("model") or configured_judge_model)
        critic_model=str(critic.get("model") or configured_critic_model)
        independent,independence_reason=_independent(actual_judge,actual_critic,judge_model,critic_model)
        supports=bool(
            judge.get("valid")
            and str(judge.get("verdict") or "").upper()=="SUPPORTS"
            and contract_gate.get("ready")
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
            if (
                judge.get("valid")
                and str(judge.get("verdict") or "").upper()=="SUPPORTS"
                and not contract_gate.get("ready")
            ):
                reason=str(contract_gate.get("reason") or "Semantic Proof Gate 2.0 не пройден.")
            elif not independent and judge.get("valid") and str(judge.get("verdict") or "").upper()=="SUPPORTS":
                reason=independence_reason
            elif str(judge.get("verdict") or "").upper()!="SUPPORTS":
                reason=str(judge.get("reason") or "Недостаточно доказательств для смыслового подтверждения.")
            else:
                reason=str(critic.get("reason") or "Независимый Critic не подтвердил смысловое доказательство.")
        selected_ids=list(judge.get("evidence_ids") or [])
        selected_evidence=_selected_evidence(packet,selected_ids)
        source_packet=next((row for row in source if str(row.get("packet_id") or "")==pid),{})
        decisions[requirement_id]={
            "requirement_id":requirement_id,
            "packet_id":pid,
            "packet_fingerprint":source_packet_fingerprints.get(pid,""),
            "requirement_fingerprint":_requirement_fingerprint(source_packet),
            "selected_proof_fingerprint":_selected_proof_fingerprint(source_packet,selected_evidence),
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
            "selected_evidence":selected_evidence,
            "blocking_concerns":list(critic.get("blocking_concerns") or []),
            "semantic_contract_configured":bool(contract_gate.get("configured")),
            "semantic_contract_version":str(contract_gate.get("version") or ""),
            "semantic_contract_ready":bool(contract_gate.get("ready")),
            "semantic_contract_source_scope_satisfied":bool(contract_gate.get("source_scope_satisfied")),
            "semantic_contract_missing_groups":list(contract_gate.get("missing_groups") or []),
            "semantic_contract_group_results":list(contract_gate.get("group_results") or []),
            "semantic_contract_reason":str(contract_gate.get("reason") or ""),
        }
    merged_decisions=dict(preserved_decisions)
    merged_decisions.update(decisions)
    base["decisions"]=merged_decisions
    base["new_decisions"]=len(decisions)
    base["pending_unprocessed"]=max(0,len(source)-len(decisions))
    base["newly_verified_ok"]=verified
    base["verified_ok"]=sum(
        str(value.get("state") or "").upper()=="VERIFIED_OK"
        for value in merged_decisions.values()
    )
    base["review_questions"]=sum(
        str(value.get("state") or "").upper()=="REVIEW_QUESTION"
        for value in merged_decisions.values()
    )+base["pending_unprocessed"]
    base["contract_gate_blocked"]=sum(
        1 for pid,gate in semantic_contract_gates.items()
        if (
            str((validated_judges.get(pid) or {}).get("verdict") or "").upper()=="SUPPORTS"
            and (validated_judges.get(pid) or {}).get("valid")
            and gate.get("configured")
            and not gate.get("ready")
        )
    )
    base["provider_errors"]=list(dict.fromkeys([*judge_errors,*critic_errors]))
    return base


def apply_normative_semantic_proof(
    proof_result:dict[str,Any],
    semantic_result:dict[str,Any]|None,
)->dict[str,Any]:
    """Apply semantic proof when the judged requirement and cited evidence remain unchanged.

    Candidate-pool growth or re-ranking does not invalidate a proof that still points to
    the same addressable evidence. Requirement or cited-evidence changes remain fail-closed.
    """
    result=dict(proof_result or {})
    rows=[dict(x) for x in (result.get("rows") or [])]
    semantic=dict(semantic_result or {})
    queue=list(result.get("semantic_queue") or [])
    expected=_fingerprint(queue)
    if not semantic:
        result["semantic_proof_applied"]=0
        result["semantic_proof_stale"]=False
        return result

    decisions=dict(semantic.get("decisions") or {})
    exact_queue=semantic.get("fingerprint")==expected
    current_packet_fingerprints={
        str(packet.get("requirement_id") or ""):_packet_fingerprint(packet)
        for packet in queue
        if str(packet.get("requirement_id") or "")
    }
    current_packets={
        str(packet.get("requirement_id") or ""):packet
        for packet in queue
        if str(packet.get("requirement_id") or "")
    }
    if exact_queue:
        reusable=decisions
        stale_count=0
    else:
        reusable={}
        stale_count=0
        for rid,decision in decisions.items():
            if not isinstance(decision,dict):
                stale_count+=1
                continue
            stored_fp=str(decision.get("packet_fingerprint") or "")
            current_fp=current_packet_fingerprints.get(str(rid))
            if stored_fp and current_fp and stored_fp==current_fp:
                reusable[rid]=decision
                continue

            packet=current_packets.get(str(rid))
            stored_requirement_fp=str(decision.get("requirement_fingerprint") or "")
            stored_proof_fp=str(decision.get("selected_proof_fingerprint") or "")
            selected=list(decision.get("selected_evidence") or [])
            if (
                isinstance(packet,dict)
                and stored_requirement_fp
                and stored_proof_fp
                and _requirement_fingerprint(packet)==stored_requirement_fp
                and _selected_evidence_still_available(packet,selected)
                and _selected_proof_fingerprint(packet,selected)==stored_proof_fp
            ):
                reusable[rid]=decision
            else:
                stale_count+=1
        if not reusable:
            result["semantic_proof_applied"]=0
            result["semantic_proof_stale"]=True
            result["semantic_proof_summary"]={
                **{k:v for k,v in semantic.items() if k!="decisions"},
                "queue_fingerprint_match":False,
                "reused_decisions":0,
                "stale_decisions":stale_count,
            }
            return result

    applied=0
    for row in rows:
        rid=str(row.get("requirement_id") or "")
        decision=reusable.get(rid)
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
    completed_ids={str(value) for value in reusable if str(value)}
    pending_queue=[
        dict(packet) for packet in queue
        if str(packet.get("requirement_id") or str(packet.get("packet_id") or "").removeprefix("NORM-"))
        not in completed_ids
    ]
    result["rows"]=rows
    result["semantic_queue"]=pending_queue
    result["semantic_queue_total"]=len(pending_queue)
    result["semantic_completed_total"]=len(completed_ids)
    result["semantic_reviewed_no_promotion"]=sum(
        str((reusable.get(rid) or {}).get("state") or "").upper()=="REVIEW_QUESTION"
        for rid in completed_ids
    )
    result["verified_ok"]=sum(str(x.get("kind") or "").upper()=="VERIFIED_OK" for x in rows)
    result["review_questions"]=sum(str(x.get("kind") or "").upper()=="REVIEW_QUESTION" for x in rows)
    result["system_limitations"]=sum(str(x.get("kind") or "").upper()=="SYSTEM_LIMITATION" for x in rows)
    result["project_findings"]=sum(str(x.get("kind") or "").upper()=="PROJECT_FINDING" for x in rows)
    result["semantic_proof_applied"]=applied
    result["semantic_proof_stale"]=False
    result["semantic_proof_summary"]={
        **{k:v for k,v in semantic.items() if k!="decisions"},
        "queue_fingerprint_match":exact_queue,
        "reused_decisions":len(reusable),
        "stale_decisions":stale_count,
    }
    return result
