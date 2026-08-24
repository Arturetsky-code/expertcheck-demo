from __future__ import annotations
from typing import Any
import math,re

def _tokens(text:str)->set[str]:
    return {x for x in re.findall(r'[a-zа-яё0-9]+',str(text or '').lower()) if len(x)>2}

def _num(value:Any)->float|None:
    try:return float(str(value).replace('\u00a0','').replace(' ','').replace(',','.'))
    except (TypeError,ValueError):return None

def retrieve_evidence(query:dict[str,Any], db:dict[str,Any], limit:int=12)->list[dict[str,Any]]:
    """Multi-strategy deterministic retrieval. AI reranking may be layered on top."""
    qtext=' '.join(str(query.get(k) or '') for k in ('title','requirement','metric','entity','expected_evidence'))
    qt=_tokens(qtext); entity=str(query.get('entity') or '').lower(); metric=str(query.get('metric') or '').lower()
    required_value=_num(query.get('required_value')); required_unit=str(query.get('unit') or '').lower().replace(' ','')
    out=[]
    for r in db.get('records') or []:
        score=0; reasons=[]
        rt=_tokens(' '.join(str(r.get(k) or '') for k in ('text','owner','metric','document')))
        overlap=len(qt & rt)
        if overlap: score+=min(35,overlap*5); reasons.append('semantic_terms')
        if entity and entity in str(r.get('owner') or '').lower(): score+=35; reasons.append('entity_match')
        if metric and metric in str(r.get('metric') or '').lower(): score+=40; reasons.append('metric_match')
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
    return out[:limit]

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
