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


_MATCH_STOPWORDS={"в","во","на","над","под","по","при","для","от","до","из","с","со","к","ко","у","и","или","либо","как","через"}
_MATCH_UNITS={"м","мм","см","кв","квт","м2","м3"}


def _stem_token(token:str)->str:
    token=_norm(token).replace(".",",")
    if re.fullmatch(r"\d+(?:,\d+)?",token):
        return token
    return token[:5] if len(token)>=6 else token


def _keyword_signature(keyword:str)->tuple[list[str],list[str],int]:
    tokens=re.findall(r"[a-zа-я]+|\d+(?:[.,]\d+)?",_norm(keyword))
    alpha=[token for token in tokens if token.isalpha()]
    lexical=[
        _stem_token(token) for token in alpha
        if token not in _MATCH_STOPWORDS and token not in _MATCH_UNITS and len(token)>=4
    ]
    numeric=[_stem_token(token) for token in tokens if re.fullmatch(r"\d+(?:[.,]\d+)?",token)]
    return lexical,numeric,len(alpha)


def _keyword_match(keyword:str,text:str)->tuple[bool,bool,int]:
    normalized=_norm(text)
    phrase=_norm(keyword)
    lexical,numeric,alpha_count=_keyword_signature(keyword)

    # Pure numeric thresholds may support an already anchored textual hit, but
    # they are never allowed to create a normative candidate on their own.
    if numeric and not lexical:
        rendered=normalized.replace(".",",")
        positions=[rendered.find(value) for value in numeric]
        ok=all(pos>=0 for pos in positions)
        return ok,True,min((pos for pos in positions if pos>=0),default=-1)

    exact=normalized.find(phrase)
    if exact>=0:
        return True,False,exact

    if not lexical:
        return False,False,-1

    # Do not turn a phrase such as "через конвейер" into a generic one-word
    # match after dropping the preposition.
    if alpha_count>1 and len(lexical)<2:
        return False,False,-1

    positions=[]
    for stem in lexical:
        stem_positions=[m.start() for m in re.finditer(re.escape(stem),normalized)]
        if not stem_positions:
            return False,False,-1
        positions.append(stem_positions)

    # Order-independent, morphology-tolerant phrase matching, but only inside
    # a local evidence window so distant page terms do not create a concept hit.
    for anchor in positions[0]:
        selected=[anchor]
        for variants in positions[1:]:
            nearest=min(variants,key=lambda pos:abs(pos-anchor))
            selected.append(nearest)
        if max(selected)-min(selected)<=320:
            return True,False,min(selected)
    return False,False,-1


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
    positions=[]
    for hit in hits:
        if not hit:
            continue
        matched,_,position=_keyword_match(hit,low)
        if matched and position>=0:
            positions.append(position)
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


def _applicability_negated(keyword:str,text:str)->bool:
    normalized=_norm(text)
    matched,_,position=_keyword_match(keyword,normalized)
    if not matched or position<0:
        return False
    start=max(0,position-180)
    end=min(len(normalized),position+360)
    window=normalized[start:end]
    negative_markers=(
        "не распространя",
        "не предъявл",
        "не примен",
        "не требуется",
        "не подлеж",
        "не относится",
        "требования отсутств",
    )
    return any(marker in window for marker in negative_markers)


def _conditional_applicability_decision(
    contract:dict[str,Any],
    documents:list[dict[str,Any]]|None,
    pages:list[dict[str,Any]]|None=None,
)->dict[str,Any]:
    ec=dict(contract.get("evidence_contract") or {})
    if str(ec.get("applicability") or "").upper()!="CONDITIONAL":
        return {
            "applicable":True,
            "reason_code":"SECTION_PRESENT",
            "trace":[],
            "negative_trace":[],
        }

    applicability_keywords=[
        _norm(value) for value in (ec.get("applicability_keywords") or [])
        if _norm(value)
    ]
    if applicability_keywords:
        matched=set()
        trace=[]
        negative_trace=[]
        seen=set()
        for page in pages or []:
            raw_text=str(page.get("text") or page.get("content") or "")
            for keyword in applicability_keywords:
                ok,is_numeric,_=_keyword_match(keyword,raw_text)
                if not ok or is_numeric:
                    continue
                document=str(page.get("document") or "").strip()
                page_no=page.get("page")
                key=(document,str(page_no),keyword)
                if key in seen:
                    continue
                seen.add(key)
                entry={
                    "document":document,
                    "page":page_no,
                    "section":str(page.get("document_type") or page.get("section") or ""),
                    "matched_condition":keyword,
                    "fragment":_fragment(raw_text,[keyword],radius=180),
                }
                if _applicability_negated(keyword,raw_text):
                    negative_trace.append(entry)
                    continue
                matched.add(keyword)
                trace.append(entry)
        minimum=max(1,int(ec.get("applicability_min_hits") or 1))
        if len(matched)>=minimum:
            return {
                "applicable":True,
                "reason_code":"PROJECT_CORPUS_CONDITION_PROVEN",
                "trace":trace[:6],
                "negative_trace":negative_trace[:6],
            }
        return {
            "applicable":False,
            "reason_code":"PROJECT_CORPUS_CONDITION_NOT_PROVEN",
            "trace":trace[:6],
            "negative_trace":negative_trace[:6],
        }

    requirement=_norm(contract.get("requirement") or "")
    profile=_norm(_project_profile(documents))
    if "производственного назначения" in requirement:
        if "объект производственного назначения" in profile:
            return {
                "applicable":True,
                "reason_code":"PROJECT_PROFILE_PRODUCTION",
                "trace":[{
                    "document":"",
                    "page":None,
                    "section":"PROJECT_PROFILE",
                    "matched_condition":"объект производственного назначения",
                    "fragment":_project_profile(documents),
                }],
                "negative_trace":[],
            }
        return {
            "applicable":False,
            "reason_code":"PROJECT_PROFILE_PRODUCTION_NOT_PROVEN",
            "trace":[],
            "negative_trace":[],
        }
    return {
        "applicable":False,
        "reason_code":"CONDITIONAL_APPLICABILITY_NOT_PROVEN",
        "trace":[],
        "negative_trace":[],
    }


def _conditional_applicability(
    contract:dict[str,Any],
    documents:list[dict[str,Any]]|None,
    pages:list[dict[str,Any]]|None=None,
)->tuple[bool,str]:
    """Compatibility wrapper for callers that only need the binary decision."""
    decision=_conditional_applicability_decision(contract,documents,pages)
    return bool(decision.get("applicable")),str(decision.get("reason_code") or "")


def _ios_inventory(documents:list[dict[str,Any]]|None)->list[dict[str,Any]]:
    output=[]
    seen=set()
    for row in documents or []:
        if not isinstance(row,dict):
            continue
        raw_section=str(
            row.get("Тип документа")
            or row.get("document_type")
            or row.get("Раздел")
            or row.get("section")
            or ""
        )
        raw_name=str(
            row.get("Файл")
            or row.get("document")
            or row.get("filename")
            or ""
        ).strip()
        if _section_key(raw_section or raw_name)!="иос":
            continue

        normalized=_norm(f"{raw_section} {raw_name}").replace(" ","")
        codes=[]
        for match in re.finditer(r"иос(\d+(?:\.\d+)*)",normalized):
            code=f"ИОС{match.group(1)}"
            if code not in codes:
                codes.append(code)
        if not codes:
            codes=["ИОС"]

        document=raw_name or raw_section or "ИОС"
        key=(document,tuple(codes))
        if key in seen:
            continue
        seen.add(key)
        output.append({
            "document":document,
            "section":"ИОС",
            "subsections":codes,
        })
    output.sort(key=lambda item:(item["subsections"],item["document"]))
    return output


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


def _diagnostic_terms(contract:dict[str,Any])->list[tuple[str,str]]:
    """Readable lexical terms used only for retrieval near-miss diagnostics."""
    output=[]
    seen=set()
    for keyword in _keywords(contract):
        tokens=re.findall(r"[a-zа-я]+",_norm(keyword))
        for token in tokens:
            if token in _MATCH_STOPWORDS or token in _MATCH_UNITS or len(token)<4:
                continue
            stem=_stem_token(token)
            if stem in seen:
                continue
            seen.add(stem)
            output.append((stem,token))
    return output


def _near_miss_fragment(text:str,stems:list[str],radius:int=260)->str:
    raw=" ".join(str(text or "").split())
    normalized=_norm(raw)
    positions=[normalized.find(stem) for stem in stems if stem and normalized.find(stem)>=0]
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


def _near_miss_candidates(
    contract:dict[str,Any],
    candidates:list[dict[str,Any]],
    *,
    limit:int=3,
)->list[dict[str,Any]]:
    """Rank partial lexical overlaps without changing any verification verdict."""
    terms=_diagnostic_terms(contract)
    if not terms:
        return []
    total=len(terms)
    ranked=[]
    for page in candidates:
        raw_text=str(page.get("text") or page.get("content") or "")
        normalized=_norm(raw_text)
        matched=[(stem,label) for stem,label in terms if stem in normalized]
        if not matched:
            continue
        stems=[stem for stem,_ in matched]
        labels=list(dict.fromkeys(label for _,label in matched))
        ranked.append((
            len(matched),
            len(matched)/max(1,total),
            len(normalized),
            page,
            stems,
            labels,
        ))
    ranked.sort(key=lambda item:(item[0],item[1],item[2]),reverse=True)

    output=[]
    seen=set()
    for overlap,ratio,_,page,stems,labels in ranked:
        document=str(page.get("document") or "").strip()
        page_no=page.get("page")
        key=(document,str(page_no))
        if key in seen:
            continue
        seen.add(key)
        output.append({
            "document":document,
            "page":page_no,
            "section":str(page.get("document_type") or page.get("section") or ""),
            "matched_terms":labels,
            "overlap_count":overlap,
            "query_term_count":total,
            "overlap_ratio":round(ratio,3),
            "fragment":_near_miss_fragment(str(page.get("text") or page.get("content") or ""),stems),
        })
        if len(output)>=max(1,int(limit or 1)):
            break
    return output


def _strong_near_miss_evidence(
    contract:dict[str,Any],
    candidates:list[dict[str,Any]],
    requirement_id:str,
    *,
    limit:int=4,
    minimum_distinct_sections:int=1,
)->list[dict[str,Any]]:
    """Admit only strong partial overlaps as semantic-review candidates.

    This fallback never verifies a requirement by itself. It only creates
    addressable evidence packets so the proof layer can keep the verdict
    fail-closed and, when appropriate, send the packet to semantic review.
    """
    raw=[
        item for item in _near_miss_candidates(contract,candidates,limit=12)
        if int(item.get("overlap_count") or 0)>=3
        and float(item.get("overlap_ratio") or 0)>=0.70
    ]
    if not raw:
        return []

    minimum_distinct_sections=max(1,min(int(minimum_distinct_sections or 1),limit))
    selected=list(raw[:limit])
    if minimum_distinct_sections>1:
        seen={
            _section_key(item.get("section") or item.get("document") or "")
            for item in selected
            if _section_key(item.get("section") or item.get("document") or "")
        }
        for item in raw[limit:]:
            if len(seen)>=minimum_distinct_sections:
                break
            section=_section_key(item.get("section") or item.get("document") or "")
            if not section or section in seen:
                continue
            if selected:
                selected[-1]=item
            else:
                selected.append(item)
            seen.add(section)

    output=[]
    seen_pages=set()
    for item in selected[:limit]:
        document=str(item.get("document") or "").strip()
        page_no=item.get("page")
        fragment=str(item.get("fragment") or "").strip()
        key=(document,str(page_no))
        if not document or page_no in (None,"") or not fragment or key in seen_pages:
            continue
        seen_pages.add(key)
        output.append({
            "evidence_id":f"NORM-E-{requirement_id}-NM-{len(output)+1:02d}",
            "document":document,
            "page":page_no,
            "section":str(item.get("section") or ""),
            "fragment":fragment,
            "matched_keywords":list(item.get("matched_terms") or []),
            "retrieval_keyword_score":int(item.get("overlap_count") or 0),
            "retrieval_keyword_coverage":float(item.get("overlap_ratio") or 0),
            "retrieval_admission":"STRONG_NEAR_MISS",
        })
    return output


def _rank_candidates(
    contract:dict[str,Any],
    candidates:list[dict[str,Any]],
)->list[tuple[int,float,int,dict[str,Any],list[str]]]:
    words=_keywords(contract)
    ranked=[]
    for page in candidates:
        raw_text=str(page.get("text") or page.get("content") or "")
        text=_norm(raw_text)
        lexical_hits=[]
        numeric_hits=[]
        for keyword in words:
            matched,is_numeric,_=_keyword_match(keyword,text)
            if not matched:
                continue
            if is_numeric:
                numeric_hits.append(keyword)
            else:
                lexical_hits.append(keyword)

        # A bare dimension/value is not normative evidence. Numeric thresholds
        # only strengthen a page that already contains a textual concept hit.
        if not lexical_hits:
            continue
        hits=[*lexical_hits,*numeric_hits]
        coverage=len(hits)/max(1,len(words))
        ranked.append((len(hits),coverage,len(text),page,hits,len(lexical_hits)))
    ranked.sort(key=lambda x:(x[5],x[0],x[1],x[2]),reverse=True)
    return [(score,coverage,length,page,hits) for score,coverage,length,page,hits,_ in ranked]


def _diversify_ranked_candidates(
    ranked:list[tuple[int,float,int,dict[str,Any],list[str]]],
    *,
    limit:int=4,
    minimum_distinct_sections:int=1,
)->list[tuple[int,float,int,dict[str,Any],list[str]]]:
    deduped=[]
    seen_ranked=set()
    for item in ranked:
        _,_,_,page,_=item
        document=str(page.get("document") or "").strip()
        page_no=page.get("page")
        key=(document,str(page_no))
        if key in seen_ranked:
            continue
        seen_ranked.add(key)
        deduped.append(item)

    minimum_distinct_sections=max(1,min(int(minimum_distinct_sections or 1),limit))
    if minimum_distinct_sections<=1 or len(deduped)<=1:
        return deduped[:limit]

    # Preserve the strongest existing candidates and use only the remaining
    # slots to widen source/section diversity for cross-document proof.
    protected=max(1,limit-(minimum_distinct_sections-1))
    chosen=list(deduped[:protected])
    chosen_ids={id(item) for item in chosen}
    seen_sections={
        _page_section(item[3]) or _norm(item[3].get("document") or "")
        for item in chosen
    }

    for item in deduped[protected:]:
        if len(chosen)>=limit:
            break
        section=_page_section(item[3]) or _norm(item[3].get("document") or "")
        if section and section not in seen_sections:
            chosen.append(item)
            chosen_ids.add(id(item))
            seen_sections.add(section)
            if len(seen_sections)>=minimum_distinct_sections:
                break

    for item in deduped:
        if len(chosen)>=limit:
            break
        if id(item) not in chosen_ids:
            chosen.append(item)
            chosen_ids.add(id(item))
    return chosen[:limit]


def _candidate_payloads(
    ranked:list[tuple[int,float,int,dict[str,Any],list[str]]],
    requirement_id:str,
    *,
    limit:int=4,
    minimum_distinct_sections:int=1,
)->list[dict[str,Any]]:
    ordered=_diversify_ranked_candidates(
        ranked,
        limit=limit,
        minimum_distinct_sections=minimum_distinct_sections,
    )
    output=[]
    seen=set()
    for score,coverage,_,page,hits in ordered:
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
            "set_completeness_queue":list(proof.get("set_completeness_queue") or []),
            "set_completeness_queue_total":int(proof.get("set_completeness_queue_total") or 0),
            "semantic_proof_applied":int(proof.get("semantic_proof_applied") or 0),
            "semantic_proof_stale":bool(proof.get("semantic_proof_stale")),
            "semantic_proof_summary":dict(proof.get("semantic_proof_summary") or {}),
            "demoted_keyword_only":int(proof.get("demoted_keyword_only") or 0),
            "demoted_keyword_only_initial":int(
                proof.get("demoted_keyword_only_initial")
                or proof.get("demoted_keyword_only")
                or 0
            ),
            "demoted_keyword_only_remaining":int(
                proof.get("demoted_keyword_only_remaining")
                if proof.get("demoted_keyword_only_remaining") is not None
                else proof.get("demoted_keyword_only") or 0
            ),
            "proof_frontier":dict(proof.get("proof_frontier") or {}),
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
            "proof_type_hint":str(
                (contract.get("evidence_contract") or {}).get("proof_type") or ""
            ).strip().upper(),
            "trust_state":contract.get("trust_state") or "",
            "source_status":contract.get("source_status") or "",
            "history_occurrences":int(contract.get("expert_occurrences") or 0),
            "history_projects":int(contract.get("expert_project_count") or 0),
            "priority_score":int(contract.get("priority_score") or 0),
            "retrieval_candidate_count":0,
            "evidence_candidates":[],
            "retrieval_near_misses":[],
        }
        applicability=_conditional_applicability_decision(contract,documents,candidates)
        applicable=bool(applicability.get("applicable"))
        applicability_reason=str(applicability.get("reason_code") or "")
        base["applicability_reason_code"]=applicability_reason
        base["applicability_trace"]=list(applicability.get("trace") or [])
        base["applicability_negative_trace"]=list(applicability.get("negative_trace") or [])
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
            inventory=_ios_inventory(documents)
            if not inventory:
                return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                    "reason":"Пункт 15 применим по маршруту ИОС, но инвентарь загруженных подразделов не распознан. Полнота применимых подразделов не доказана.",
                    "reason_code":"NORMATIVE_IOS_SUBSECTION_APPLICABILITY_PENDING",
                    "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

            inventory_candidates=[]
            for index,item in enumerate(inventory[:4],1):
                codes=", ".join(item.get("subsections") or ["ИОС"])
                inventory_candidates.append({
                    "evidence_id":f"NORM-E-{rid}-INV-{index:02d}",
                    "document":item.get("document") or "ИОС",
                    "page":None,
                    "section":"ИОС",
                    "fragment":f"Инвентарь загруженных подразделов: {codes}. Документ: {item.get('document') or 'ИОС'}.",
                    "matched_keywords":list(item.get("subsections") or []),
                    "retrieval_keyword_score":len(item.get("subsections") or []),
                    "retrieval_keyword_coverage":1.0,
                    "locator_kind":"DOCUMENT_INVENTORY",
                })
            primary=inventory_candidates[0]
            return {
                **base,
                "kind":"VERIFIED_OK",
                "state":KIND_LABELS["VERIFIED_OK"],
                "reason":(
                    "Фактический инвентарь подразделов ИОС распознан и передан в контракт полноты. "
                    "Сам инвентарь не доказывает полноту применимых подразделов и не является итоговым нормативным подтверждением."
                ),
                "reason_code":"NORMATIVE_IOS_INVENTORY_CANDIDATE",
                "evidence_candidates":inventory_candidates,
                "retrieval_candidate_count":len(inventory_candidates),
                "evidence_id":primary.get("evidence_id") or "",
                "evidence_document":primary.get("document") or "",
                "evidence_page":None,
                "evidence_fragment":primary.get("fragment") or "",
                "matched_keywords":list(primary.get("matched_keywords") or []),
            }

        if not candidates:
            return {**base,"kind":"SYSTEM_LIMITATION","state":KIND_LABELS["SYSTEM_LIMITATION"],
                "reason":"Верифицированный пункт применим по маршруту, но в цифровом корпусе нет адресных страниц ожидаемого раздела.",
                "reason_code":"NORMATIVE_SECTION_EVIDENCE_MISSING",
                "evidence_document":"","evidence_page":None,"evidence_fragment":"","matched_keywords":[]}

        ec=dict(contract.get("evidence_contract") or {})
        minimum=max(1,int(ec.get("min_keyword_hits") or 2))
        ranked=_rank_candidates(contract,candidates)
        # Cross-document proof keeps the strongest existing evidence while
        # reserving room for a different section/source when the contract needs it.
        cross_document=str(contract.get("check_kind") or "").upper()=="CROSS_DOCUMENT"
        minimum_sources=max(1,int(ec.get("minimum_sources") or 1))
        evidence_candidates=_candidate_payloads(
            ranked,
            rid,
            limit=4,
            minimum_distinct_sections=(minimum_sources if cross_document else 1),
        )
        base["evidence_candidates"]=evidence_candidates
        base["retrieval_candidate_count"]=len(evidence_candidates)
        if not ranked or not evidence_candidates:
            near_misses=_near_miss_candidates(contract,candidates)
            fallback=_strong_near_miss_evidence(
                contract,
                candidates,
                rid,
                limit=4,
                minimum_distinct_sections=(minimum_sources if cross_document else 1),
            )
            if fallback:
                primary=fallback[0]
                return {
                    **base,
                    "kind":"REVIEW_QUESTION",
                    "state":KIND_LABELS["REVIEW_QUESTION"],
                    "reason":(
                        "Точное фразовое совпадение не прошло retrieval-порог, но найден сильный адресный "
                        "token-level near-miss. Кандидат допускается только к доказательной/смысловой проверке "
                        "и сам по себе не подтверждает выполнение требования."
                    ),
                    "reason_code":"NORMATIVE_STRONG_NEAR_MISS_CANDIDATE",
                    "retrieval_near_misses":near_misses,
                    "evidence_candidates":fallback,
                    "retrieval_candidate_count":len(fallback),
                    "evidence_id":primary.get("evidence_id") or "",
                    "evidence_document":primary.get("document") or "",
                    "evidence_page":primary.get("page"),
                    "evidence_fragment":primary.get("fragment") or "",
                    "matched_keywords":list(primary.get("matched_keywords") or []),
                    "retrieval_keyword_score":int(primary.get("retrieval_keyword_score") or 0),
                    "retrieval_keyword_coverage":primary.get("retrieval_keyword_coverage") or 0,
                    "retrieval_minimum":minimum,
                }
            return {**base,"kind":"REVIEW_QUESTION","state":KIND_LABELS["REVIEW_QUESTION"],
                "reason":"Пункт НТД и профильный раздел подтверждены, но адресное положительное доказательство выполнения требования не найдено. Отсутствие совпадения не трактуется как нарушение.",
                "reason_code":"NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND",
                "retrieval_near_misses":near_misses,
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
                "reason_code":"NORMATIVE_EVIDENCE_WEAK",
                "retrieval_near_misses":_near_miss_candidates(contract,candidates)}

        return {**base,**evidence,"kind":"VERIFIED_OK","state":KIND_LABELS["VERIFIED_OK"],
            "reason":"Retrieval-контур нашёл адресные положительные кандидаты. Окончательный статус определяется proof-контрактом Alpha 9.",
            "reason_code":"NORMATIVE_RETRIEVAL_CANDIDATE_CONFIRMED"}
