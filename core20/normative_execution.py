from __future__ import annotations

import re
from typing import Any

from .normative_foundation import NormativeKnowledgeFoundation20, _section_key, default_foundation
from .normative_proof import NormativeProofEngine20
from .normative_semantic_proof import apply_normative_semantic_proof


ENGINE_VERSION="20.0-alpha9-normative-proof"
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


def _fragment(text:str, hits:list[str], radius:int=240)->str:
    low=_norm(text)
    pos=min((low.find(hit) for hit in hits if hit and low.find(hit)>=0),default=-1)
    if pos<0:
        return " ".join(str(text or "").split())[:700]
    raw=" ".join(str(text or "").split())
    # Normalized and raw offsets are close enough for a diagnostic excerpt; do
    # not use the excerpt position as a legal/addressing fact.
    start=max(0,pos-radius); end=min(len(raw),pos+radius)
    return raw[start:end][:700]


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
    # Energy-efficiency and other conditional clauses require an explicit
    # project-specific applicability proof. Presence of AR/PZU alone is not enough.
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


class NormativeExecutionEngine20:
    """Retrieve evidence for curated, current, verified-clause contracts.

    Alpha 9 explicitly separates retrieval from proof. This module still finds
    and addresses candidate evidence, but NormativeProofEngine20 decides whether
    the evidence type is strong enough for VERIFIED_OK. A persisted semantic
    checkpoint may promote only the exact current semantic queue after an
    independent Judge/Critic proof.
    """

    def __init__(self, foundation:NormativeKnowledgeFoundation20|None=None):
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
            "rows":rows,
            "retrieval":{
                "contracts":len(retrieval_rows),
                "addressed":retrieval_addressed,
                "counts":retrieval_counts,
                "verified_ok":retrieval_counts["VERIFIED_OK"],
                "review_questions":retrieval_counts["REVIEW_QUESTION"],
                "system_limitations":retrieval_counts["SYSTEM_LIMITATION"],
                "evidence_coverage_pct":round(100.0*retrieval_addressed/max(1,len(retrieval_rows)),1),
            },
            "proof_engine":{
                key:value for key,value in proof.items() if key!="rows"
            },
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
        candidates=[
            p for p in pages
            if not expected or _page_section(p) in expected
        ]
        base={
            "requirement_id":contract.get("requirement_id") or "",
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
        }
        applicable,applicability_reason=_conditional_applicability(contract,documents)
        base["applicability_reason_code"]=applicability_reason
        if not applicable:
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Пункт НТД верифицирован, но его условная применимость к текущему проекту не доказана. Автоматический вывод удержан.",
                "reason_code":"NORMATIVE_APPLICABILITY_NOT_PROVEN",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        rid=str(contract.get("requirement_id") or "").upper()
        if rid in {"PP87-CLAUSE-12-PZU","PP87-CLAUSE-13-AR"}:
            target="пзу" if rid=="PP87-CLAUSE-12-PZU" else "ар"
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

        if rid=="PP87-CLAUSE-15-IOS":
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Состав раздела ИОС маршрутизирован по верифицированному пункту 15, но полнота применимых подразделов требует проектно-специфической проверки.",
                "reason_code":"NORMATIVE_IOS_SUBSECTION_APPLICABILITY_PENDING",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        if not candidates:
            return {**base,"kind":"SYSTEM_LIMITATION","state":KIND_LABELS["SYSTEM_LIMITATION"],
                "reason":"Верифицированный пункт применим по маршруту, но в цифровом корпусе нет адресных страниц ожидаемого раздела.",
                "reason_code":"NORMATIVE_SECTION_EVIDENCE_MISSING",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        words=_keywords(contract)
        ec=dict(contract.get("evidence_contract") or {})
        minimum=max(1,int(ec.get("min_keyword_hits") or 2))
        ranked=[]
        for page in candidates:
            text=_norm(page.get("text") or page.get("content") or "")
            hits=[kw for kw in words if kw and kw in text]
            if hits:
                ranked.append((len(hits),len(text),page,hits))
        ranked.sort(key=lambda x:(x[0],x[1]),reverse=True)
        if not ranked:
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Пункт НТД и профильный раздел подтверждены, но адресное положительное доказательство выполнения требования не найдено. Отсутствие совпадения не трактуется как нарушение.",
                "reason_code":"NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        score,_,page,hits=ranked[0]
        evidence={
            "evidence_document":str(page.get("document") or ""),
            "evidence_page":page.get("page"),
            "evidence_fragment":_fragment(str(page.get("text") or page.get("content") or ""),hits),
            "matched_keywords":hits,
            "retrieval_keyword_score":score,
            "retrieval_minimum":minimum,
        }
        if score < minimum:
            return {**base,**evidence,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Найден адресный кандидат доказательства, но совпадение недостаточно сильное для автоматического подтверждения.",
                "reason_code":"NORMATIVE_EVIDENCE_WEAK"}

        return {**base,**evidence,"kind":"VERIFIED_OK","state":KIND_LABELS["VERIFIED_OK"],
            "reason":"Retrieval-контур нашёл адресный положительный кандидат. Окончательный статус определяется proof-контрактом Alpha 9.",
            "reason_code":"NORMATIVE_RETRIEVAL_CANDIDATE_CONFIRMED"}
