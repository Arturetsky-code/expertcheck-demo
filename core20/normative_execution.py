from __future__ import annotations

import re
from typing import Any

from .normative_foundation import NormativeKnowledgeFoundation20, _section_key, default_foundation
from .normative_proof import NormativeProofEngine20
from .normative_semantic_proof import apply_normative_semantic_proof


ENGINE_VERSION="20.0-alpha9-normative-proof-multi-evidence"
KIND_LABELS={
    "VERIFIED_OK":"Подтверждено",
    "PROJECT_FINDING":"Выявлено несоответствие",
    "REVIEW_QUESTION":"Вопрос специалисту",
    "SYSTEM_LIMITATION":"Не проверено системой",
}


def _norm(value:Any)->str:
    return " ".join(str(value or "").replace("ё","е").casefold().replace("\xa0"," ").split())


def _page_section(page:dict[str,Any])->str:
    return _section_key(page.get("document_type") or page.get("section") or page.get("document") or "")


def _keywords(contract:dict[str,Any])->list[str]:
    raw=[_norm(x) for x in (contract.get("keywords") or []) if _norm(x)]
    if raw:
        return raw
    words=[
        w for w in re.findall(r"[a-zа-я0-9-]{5,}",_norm(contract.get("requirement") or ""))
        if w not in {"должна","должны","должен","раздел","части","объекта","проектной","документации"}
    ]
    return list(dict.fromkeys(words[:8]))


def _fragment(text:str,hits:list[str],radius:int=240)->str:
    raw=" ".join(str(text or "").split())
    low=raw.casefold().replace("ё","е")
    positions=[low.find(hit) for hit in hits if hit and low.find(hit)>=0]
    pos=min(positions,default=-1)
    if pos<0:
        return raw[:700]
    start=max(0,pos-radius)
    end=min(len(raw),pos+radius)
    rendered=raw[start:end].strip()
    if start>0:
        rendered="… "+rendered
    if end<len(raw):
        rendered=rendered+" …"
    return rendered[:760]


def _project_profile(documents:list[dict[str,Any]]|None)->str:
    first=(documents or [{}])[0] if documents else {}
    profile=first.get("pp87_project_profile") or {}
    if isinstance(profile,dict):
        return str(profile.get("project_type") or profile.get("profile") or "").strip()
    return ""


def _conditional_applicability(contract:dict[str,Any],documents:list[dict[str,Any]]|None)->tuple[bool,str]:
    ec=dict(contract.get("evidence_contract") or {})
    if str(ec.get("applicability") or "").upper()!="CONDITIONAL":
        return True,"SECTION_PRESENT"
    requirement=_norm(contract.get("requirement") or "")
    profile=_norm(_project_profile(documents))
    if "производственного назначения" in requirement:
        if "объект производственного назначения" in profile:
            return True,"PROJECT_PROFILE_PRODUCTION"
        return False,"PROJECT_PROFILE_PRODUCTION_NOT_PROVEN"
    return False,"CONDITIONAL_APPLICABILITY_NOT_PROVEN"


def _inventory_roles(documents:list[dict[str,Any]]|None,target:str)->set[str]:
    roles=set()
    for row in documents or []:
        if not isinstance(row,dict):
            continue
        section=_section_key(row.get("Тип документа") or row.get("document_type") or row.get("Раздел") or row.get("section") or "")
        if section!=target:
            continue
        name=_norm(row.get("Файл") or row.get("document") or row.get("filename") or "").replace(" ","")
        if target=="пзу":
            if any(x in name for x in ("пзу1","пзу_1","текстов")): roles.add("TEXT_PART")
            if any(x in name for x in ("пзу2","пзу_2","графическ","чертеж")): roles.add("GRAPHIC_PART")
        elif target=="ар":
            if any(x in name for x in ("ар1","ар_1","текстов")): roles.add("TEXT_PART")
            if any(x in name for x in ("ар2","ар_2","графическ","чертеж")): roles.add("GRAPHIC_PART")
    return roles


def _rank_candidates(
    contract:dict[str,Any],
    candidates:list[dict[str,Any]],
)->list[tuple[int,float,int,dict[str,Any],list[str]]]:
    words=_keywords(contract)
    ranked=[]
    for page in candidates:
        raw_text=str(page.get("text") or page.get("content") or "")
        text=_norm(raw_text)
        hits=[kw for kw in words if kw and kw in text]
        if not hits:
            continue
        coverage=len(hits)/max(1,len(words))
        ranked.append((len(hits),coverage,len(text),page,hits))
    ranked.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
    return ranked


def _candidate_payloads(
    ranked:list[tuple[int,float,int,dict[str,Any],list[str]]],
    requirement_id:str,
    *,
    limit:int=4,
)->list[dict[str,Any]]:
    output=[]
    seen=set()
    for score,coverage,_,page,hits in ranked:
        document=str(page.get("document") or "").strip()
        page_no=page.get("page")
        fragment=_fragment(str(page.get("text") or page.get("content") or ""),hits)
        key=(document,str(page_no),fragment[:240])
        if key in seen:
            continue
        seen.add(key)
        index=len(output)+1
        output.append({
            "evidence_id":f"NORM-E-{requirement_id}-{index:02d}",
            "document":document,
            "page":page_no,
            "section":str(page.get("document_type") or page.get("section") or ""),
            "fragment":fragment,
            "matched_keywords":list(hits),
            "retrieval_keyword_score":score,
            "retrieval_keyword_coverage":round(coverage,3),
        })
        if len(output)>=limit:
            break
    return output


class NormativeExecutionEngine20:
    """Retrieve evidence for curated, current, verified-clause contracts.

    Alpha 9 separates retrieval from proof. Retrieval now preserves several
    addressable candidates instead of collapsing the search to one lexical hit.
    The proof engine decides whether those candidates are strong enough for a
    categorical result. Missing proof never becomes a normative finding.
    """

    def __init__(self,foundation:NormativeKnowledgeFoundation20|None=None):
        self.foundation=foundation or default_foundation()

    def run(self,documents:list[dict[str,Any]]|None,page_corpus:list[dict[str,Any]]|None)->dict[str,Any]:
        routes=self.foundation.project_routes(documents)
        pages=[dict(x) for x in (page_corpus or []) if isinstance(x,dict)]
        retrieval_rows=[]
        for contract in routes.get("rows") or []:
            if not contract.get("project_relevant") or not contract.get("automatic_contract_ready"):
                continue
            retrieval_rows.append(self._execute(contract,pages,documents))

        retrieval_counts={kind:sum(1 for row in retrieval_rows if row.get("kind")==kind) for kind in KIND_LABELS}
        retrieval_addressed=sum(
            1 for row in retrieval_rows
            if row.get("evidence_document") and row.get("evidence_page") not in (None,"")
        )
        retrieval_candidates=sum(int(row.get("retrieval_candidate_count") or 0) for row in retrieval_rows)

        proof=NormativeProofEngine20().run(retrieval_rows)
        semantic_checkpoint={}
        if documents and isinstance(documents[0],dict):
            semantic_checkpoint=dict(documents[0].get("normative_semantic_proof") or {})
        proof=apply_normative_semantic_proof(proof,semantic_checkpoint)
        rows=list(proof.get("rows") or [])
        counts={kind:sum(1 for row in rows if row.get("kind")==kind) for kind in KIND_LABELS}
        addressed=sum(
            1 for row in rows
            if row.get("evidence_document") and row.get("evidence_page") not in (None,"")
        )
        return {
            "version":ENGINE_VERSION,
            "contracts":len(rows),
            "addressed":addressed,
            "counts":counts,
            "verified_ok":counts["VERIFIED_OK"],
            "project_findings":counts["PROJECT_FINDING"],
            "review_questions":counts["REVIEW_QUESTION"],
            "system_limitations":counts["SYSTEM_LIMITATION"],
            "evidence_coverage_pct":round(100.0*addressed/max(1,len(rows)),1),
            "retrieval_candidate_count":sum(int(row.get("retrieval_candidate_count") or 0) for row in rows),
            "rows":rows,
            "retrieval":{
                "contracts":len(retrieval_rows),
                "addressed":retrieval_addressed,
                "candidate_evidence":retrieval_candidates,
                "counts":retrieval_counts,
                "verified_ok":retrieval_counts["VERIFIED_OK"],
                "review_questions":retrieval_counts["REVIEW_QUESTION"],
                "system_limitations":retrieval_counts["SYSTEM_LIMITATION"],
                "evidence_coverage_pct":round(100.0*retrieval_addressed/max(1,len(retrieval_rows)),1),
            },
            "proof_engine":{key:value for key,value in proof.items() if key!="rows"},
            "semantic_queue":list(proof.get("semantic_queue") or []),
            "semantic_queue_total":int(proof.get("semantic_queue_total") or 0),
            "semantic_proof_applied":int(proof.get("semantic_proof_applied") or 0),
            "semantic_proof_stale":bool(proof.get("semantic_proof_stale")),
            "semantic_proof_summary":dict(proof.get("semantic_proof_summary") or {}),
            "demoted_keyword_only":int(proof.get("demoted_keyword_only") or 0),
            "proof_type_counts":dict(proof.get("proof_type_counts") or {}),
            "guardrail":(
                "Retrieval is not proof. Ненайденный текст не является доказательством нарушения, а лексическое совпадение "
                "не подтверждает содержательное нормативное требование без подходящего proof-контракта."
            ),
        }

    def _execute(self,contract:dict[str,Any],pages:list[dict[str,Any]],documents:list[dict[str,Any]]|None)->dict[str,Any]:
        expected={_section_key(x) for x in (contract.get("sections") or []) if _section_key(x)}
        expected.discard("all")
        candidates=[p for p in pages if not expected or _page_section(p) in expected]
        rid=str(contract.get("requirement_id") or "")
        base={
            "requirement_id":rid,
            "document_id":contract.get("document_id") or "",
            "source":contract.get("document_title") or "",
            "paragraph":contract.get("paragraph") or "",
            "topic":contract.get("topic") or "",
            "requirement":contract.get("requirement") or "",
            "sections":contract.get("sections") or [],
            "check_kind":contract.get("check_kind") or "",
            "trust_state":contract.get("trust_state") or "",
            "source_status":contract.get("source_status") or "",
            "history_occurrences":int(contract.get("expert_occurrences") or 0),
            "history_projects":int(contract.get("expert_project_count") or 0),
            "priority_score":int(contract.get("priority_score") or 0),
            "retrieval_candidate_count":0,
            "evidence_candidates":[],
        }
        applicable,applicability_reason=_conditional_applicability(contract,documents)
        base["applicability_reason_code"]=applicability_reason
        if not applicable:
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Пункт НТД верифицирован, но его условная применимость к текущему проекту не доказана. Автоматический вывод удержан.",
                "reason_code":"NORMATIVE_APPLICABILITY_NOT_PROVEN",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        rid_upper=rid.upper()
        if rid_upper in {"PP87-CLAUSE-12-PZU","PP87-CLAUSE-13-AR"}:
            target="пзу" if rid_upper=="PP87-CLAUSE-12-PZU" else "ар"
            roles=_inventory_roles(documents,target)
            if {"TEXT_PART","GRAPHIC_PART"} <= roles:
                return {**base,"kind":"VERIFIED_OK","state":KIND_LABELS["VERIFIED_OK"],
                    "reason":"По каноническому инвентарю подтверждены отдельные текстовая и графическая части профильного раздела.",
                    "reason_code":"NORMATIVE_STRUCTURE_VERIFIED",
                    "evidence_document":"","evidence_page":None,
                    "evidence_fragment":"Инвентарь документов: TEXT_PART + GRAPHIC_PART",
                    "matched_keywords":[]}
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Пункт НТД верифицирован, но по именам загруженных документов нельзя надёжно подтвердить полный состав текстовой и графической частей. Отсутствие отдельного файла не считается нарушением.",
                "reason_code":"NORMATIVE_STRUCTURE_PART_NOT_PROVEN",
                "evidence_document":"","evidence_page":None,
                "evidence_fragment":"Распознано ролей: "+", ".join(sorted(roles)),
                "matched_keywords":[]}

        if rid_upper=="PP87-CLAUSE-15-IOS":
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Состав раздела ИОС маршрутизирован по верифицированному пункту 15, но полнота применимых подразделов требует проектно-специфической проверки.",
                "reason_code":"NORMATIVE_IOS_SUBSECTION_APPLICABILITY_PENDING",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        if not candidates:
            return {**base,"kind":"SYSTEM_LIMITATION","state":KIND_LABELS["SYSTEM_LIMITATION"],
                "reason":"Верифицированный пункт применим по маршруту, но в цифровом корпусе нет адресных страниц ожидаемого раздела.",
                "reason_code":"NORMATIVE_SECTION_EVIDENCE_MISSING",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        ec=dict(contract.get("evidence_contract") or {})
        minimum=max(1,int(ec.get("min_keyword_hits") or 2))
        ranked=_rank_candidates(contract,candidates)
        evidence_candidates=_candidate_payloads(ranked,rid,limit=4)
        base["evidence_candidates"]=evidence_candidates
        base["retrieval_candidate_count"]=len(evidence_candidates)
        if not ranked or not evidence_candidates:
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Пункт НТД и профильный раздел подтверждены, но адресное положительное доказательство выполнения требования не найдено. Отсутствие совпадения не трактуется как нарушение.",
                "reason_code":"NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        primary=evidence_candidates[0]
        evidence={
            "evidence_id":primary.get("evidence_id") or "",
            "evidence_document":primary.get("document") or "",
            "evidence_page":primary.get("page"),
            "evidence_fragment":primary.get("fragment") or "",
            "matched_keywords":list(primary.get("matched_keywords") or []),
            "retrieval_keyword_score":int(primary.get("retrieval_keyword_score") or 0),
            "retrieval_keyword_coverage":primary.get("retrieval_keyword_coverage") or 0,
            "retrieval_minimum":minimum,
        }
        if int(primary.get("retrieval_keyword_score") or 0) < minimum:
            return {**base,**evidence,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Найден адресный кандидат доказательства, но совпадение недостаточно сильное для автоматического подтверждения.",
                "reason_code":"NORMATIVE_EVIDENCE_WEAK"}

        return {**base,**evidence,"kind":"VERIFIED_OK","state":KIND_LABELS["VERIFIED_OK"],
            "reason":"Retrieval-контур нашёл адресные положительные кандидаты. Окончательный статус определяется proof-контрактом Alpha 9.",
            "reason_code":"NORMATIVE_RETRIEVAL_CANDIDATE_CONFIRMED"}
