from __future__ import annotations
from typing import Any
import math,re

from .page_evidence_store import section_matches, source_section

def _tokens(text:str)->set[str]:
    return {x for x in re.findall(r'[a-zа-яё0-9]+',str(text or '').lower()) if len(x)>2}

def _num(value:Any)->float|None:
    try:return float(str(value).replace('\u00a0','').replace(' ','').replace(',','.'))
    except (TypeError,ValueError):return None

def retrieve_evidence(query:dict[str,Any], db:dict[str,Any], limit:int=6)->list[dict[str,Any]]:
    """Multi-strategy deterministic retrieval. AI reranking may be layered on top."""
    qtext=' '.join(str(query.get(k) or '') for k in ('title','requirement','metric','entity','expected_evidence'))
    qt=_tokens(qtext); entity=str(query.get('entity') or '').lower(); metric=str(query.get('metric') or '').lower()
    required_value=_num(query.get('required_value')); required_unit=str(query.get('unit') or '').lower().replace(' ','')
    expected_sections=list(query.get('expected_sections') or [])
    # plan_id is the stable execution contract.  Human source numbers may be
    # repeated across checklists and must not shadow it.
    query_id=str(query.get('plan_id') or query.get('source_id') or '')
    out=[]
    for r in db.get('records') or []:
        actual_section=source_section(r)
        if expected_sections and not section_matches(actual_section,expected_sections):
            continue
        score=0; reasons=[]
        rt=_tokens(' '.join(str(r.get(k) or '') for k in ('text','owner','metric','document')))
        overlap=len(qt & rt)
        if overlap: score+=min(35,overlap*5); reasons.append('semantic_terms')
        if expected_sections and actual_section:
            score+=15; reasons.append('section_contract')
        if entity and entity in str(r.get('owner') or '').lower(): score+=35; reasons.append('entity_match')
        if metric and metric in str(r.get('metric') or '').lower(): score+=40; reasons.append('metric_match')
        if query_id and query_id==str(r.get('requirement_id') or ''):
            score+=70; reasons.append('requirement_contract')
        candidate_value=_num(r.get('value'))
        if required_value is not None and candidate_value is not None and math.isclose(required_value,candidate_value,rel_tol=.0005,abs_tol=.02):
            score+=30; reasons.append('value_match')
        candidate_unit=str(r.get('unit') or '').lower().replace(' ','')
        if required_unit and candidate_unit and (required_unit==candidate_unit or required_unit in candidate_unit or candidate_unit in required_unit):
            score+=10; reasons.append('unit_match')
        if r.get('kind')=='STRUCTURED_FACT': score+=10; reasons.append('structured_fact')
        if r.get('kind')=='STRUCTURED_CONFLICT': score+=25; reasons.append('verified_conflict')
        if score:
            x=dict(r); x['retrieval_score']=min(100,score); x['retrieval_reasons']=reasons; out.append(x)
    out.sort(key=lambda x:(x['retrieval_score'], x.get('kind')=='STRUCTURED_CONFLICT', x.get('kind')=='STRUCTURED_FACT'),reverse=True)
    # Evidence packets contain addresses, not a cloud of repeated page hits.
    deduped=[];seen=set()
    for item in out:
        key=(str(item.get('document') or ''),str(item.get('page') or ''),str(item.get('kind') or ''),str(item.get('owner') or ''),str(item.get('metric') or ''))
        if key in seen:continue
        seen.add(key);deduped.append(item)
        if len(deduped)>=limit:break
    for index,item in enumerate(deduped,1):
        item['evidence_rank']=index
        item['evidence_role']='PRIMARY' if index<=3 else 'SECONDARY'
    return deduped


def retrieval_diagnostics(query:dict[str,Any], db:dict[str,Any], candidates:list[dict[str,Any]])->dict[str,Any]:
    if candidates:
        return {
          'evidence_search_state':'CANDIDATES_FOUND',
          'evidence_search_reason_codes':[],
          'primary_evidence_count':sum(str(x.get('evidence_role') or '')=='PRIMARY' for x in candidates),
        }
    expected=list(query.get('expected_sections') or [])
    records=list(db.get('records') or [])
    reasons=[]
    if expected and not any(section_matches(source_section(r),expected) for r in records):
        reasons.append('EXPECTED_SECTION_NOT_AVAILABLE')
    if query.get('entity') and not any(str(query.get('entity')).lower() in str(r.get('owner') or '').lower() for r in records):
        reasons.append('ENTITY_NOT_RESOLVED')
    if query.get('metric') and not any(str(query.get('metric')).lower() in str(r.get('metric') or '').lower() for r in records):
        reasons.append('METRIC_NOT_EXTRACTED')
    if not records:reasons.append('EVIDENCE_DATABASE_EMPTY')
    if not reasons:reasons.append('NO_ADDRESSABLE_MATCH')
    return {'evidence_search_state':'NO_CANDIDATES','evidence_search_reason_codes':reasons,'primary_evidence_count':0}

def rerank_with_judgements(query:dict[str,Any], candidates:list[dict[str,Any]], judgements:list[dict[str,Any]]|None=None)->list[dict[str,Any]]:
    """Apply external/AI judgements conservatively; disagreement can only lower trust."""
    by_id={str(j.get('evidence_id')):j for j in judgements or []}
    out=[]
    for c in candidates:
        x=dict(c); j=by_id.get(str(c.get('evidence_id')))
        if j:
            verdict=str(j.get('verdict') or '').upper(); conf=float(j.get('confidence') or 0)
            x['judge_verdict']=verdict; x['judge_confidence']=conf
            if verdict=='SUPPORTS' and conf>=0.8: x['retrieval_score']=min(100,x.get('retrieval_score',0)+20)
            elif verdict in {'OTHER_ENTITY','OTHER_METRIC','CONTRADICTS','INSUFFICIENT'}: x['retrieval_score']=max(0,x.get('retrieval_score',0)-35)
        out.append(x)
    return sorted(out,key=lambda x:x.get('retrieval_score',0),reverse=True)
