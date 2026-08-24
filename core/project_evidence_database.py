from __future__ import annotations
from typing import Any
import hashlib, re


def _txt(v: Any) -> str: return str(v or '').strip()
def _id(*parts: Any) -> str:
    raw='|'.join(_txt(x) for x in parts)
    return 'EVD-'+hashlib.sha1(raw.encode('utf-8','ignore')).hexdigest()[:14].upper()

def build_project_evidence_database(documents:list[dict[str,Any]]|None=None, facts:list[dict[str,Any]]|None=None, comparisons:list[dict[str,Any]]|None=None)->dict[str,Any]:
    """Create a read-optimised evidence layer. It never invents owners or facts."""
    records=[]
    for d in documents or []:
        doc=_txt(d.get('short_name') or d.get('name') or d.get('filename') or d.get('document_type'))
        pages=d.get('pages') or d.get('page_texts') or []
        if isinstance(pages,dict): pages=[{'page':k,'text':v} for k,v in pages.items()]
        for i,p in enumerate(pages,1):
            text=_txt(p.get('text') if isinstance(p,dict) else p)
            if not text: continue
            page=(p.get('page') if isinstance(p,dict) else None) or i
            records.append({'evidence_id':_id(doc,page,text[:180]),'kind':'DOCUMENT_TEXT','document':doc,'page':page,'text':text,'owner':'','metric':'','value':'','unit':'','trust':'SOURCE'})
    for f in facts or []:
        admission=_txt(f.get('fact_admission_decision')).upper()
        quality=_txt(f.get('evidence_quality_decision')).upper()
        integrity=_txt(f.get('row_integrity_status')).upper()
        if admission in {'HOLD','REJECT'} or quality in {'HOLD','REJECT','BLOCKED'} or integrity.startswith('BLOCKED') or f.get('comparison_excluded'):
            continue
        owner=_txt(
            f.get('object_name') or f.get('project_understanding_object_name')
            or f.get('object_hint') or f.get('owner') or f.get('entity_name')
            or f.get('semantic_anchor_name')
        )
        metric=_txt(
            f.get('metric') or f.get('metric_code') or f.get('indicator')
            or f.get('parameter') or f.get('parameter_code') or f.get('parameter_name')
        )
        value=f.get('value'); unit=_txt(f.get('unit') or f.get('units'))
        doc=_txt(f.get('document') or f.get('source_document') or f.get('source'))
        page=f.get('page') or f.get('source_page') or ''
        binding=_txt(f.get('binding_status') or f.get('property_binding_status')).upper()
        strong=bool(
            admission=='ADMIT' or quality in {'VERIFIED','SUPPORTED'}
            or binding in {'ROW_LOCKED','POSITION_LOCKED','EXACT_OBJECT'}
            or f.get('directed_evidence')
        )
        kind='STRUCTURED_FACT' if strong else 'CANDIDATE_FACT'
        records.append({'evidence_id':_id(doc,page,owner,metric,value,unit),'kind':kind,'document':doc,'page':page,'text':_txt(f.get('evidence') or f.get('source_text') or f.get('raw_text') or f.get('context') or f.get('table_evidence')),'owner':owner,'metric':metric,'value':value,'unit':unit,'trust':_txt(f.get('trust_state') or quality or admission or 'CANDIDATE'),'source_fact_id':_txt(f.get('fact_id') or f.get('evidence_id'))})
    for c in comparisons or []:
        status=_txt(c.get('status') or c.get('result')).upper()
        conflict=bool(c.get('is_conflict') or c.get('conflict') or str(c.get('kind','')).lower() in {'mismatch','conflict'} or any(x in status for x in ('РАСХОЖД','КОНФЛИКТ','НЕ СООТВЕТ')))
        if not conflict: continue
        owner=_txt(c.get('object_name') or c.get('object') or c.get('owner'))
        metric=_txt(c.get('metric') or c.get('indicator') or c.get('parameter_code') or c.get('parameter_name') or c.get('parameter'))
        records.append({'evidence_id':_id('CMP',owner,metric,c.get('values')),'kind':'STRUCTURED_CONFLICT','document':_txt(c.get('documents') or c.get('sources')),'page':'','text':_txt(c.get('explanation') or c.get('evidence')),'owner':owner,'metric':metric,'value':c.get('values') or c.get('value') or c.get('values_by_section'),'unit':_txt(c.get('unit')),'trust':'VERIFIED_CONFLICT'})
    by_owner={}; by_metric={}
    for r in records:
        if r['owner']: by_owner.setdefault(r['owner'].lower(),[]).append(r['evidence_id'])
        if r['metric']: by_metric.setdefault(r['metric'].lower(),[]).append(r['evidence_id'])
    return {'version':'2.0','records':records,'record_count':len(records),'by_owner':by_owner,'by_metric':by_metric}
