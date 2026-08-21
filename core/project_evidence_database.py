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
        owner=_txt(f.get('object_name') or f.get('owner') or f.get('entity_name'))
        metric=_txt(f.get('metric') or f.get('metric_code') or f.get('indicator') or f.get('parameter'))
        value=f.get('value'); unit=_txt(f.get('unit') or f.get('units'))
        doc=_txt(f.get('document') or f.get('source_document') or f.get('source'))
        page=f.get('page') or f.get('source_page') or ''
        records.append({'evidence_id':_id(doc,page,owner,metric,value,unit),'kind':'STRUCTURED_FACT','document':doc,'page':page,'text':_txt(f.get('evidence') or f.get('source_text') or f.get('raw_text')),'owner':owner,'metric':metric,'value':value,'unit':unit,'trust':_txt(f.get('trust_state') or 'STRUCTURED'),'source_fact_id':_txt(f.get('fact_id') or f.get('evidence_id'))})
    for c in comparisons or []:
        if not bool(c.get('is_conflict') or c.get('conflict') or str(c.get('kind','')).lower() in {'mismatch','conflict'}): continue
        records.append({'evidence_id':_id('CMP',c.get('object_name'),c.get('metric'),c.get('values')),'kind':'STRUCTURED_CONFLICT','document':_txt(c.get('documents')),'page':'','text':_txt(c.get('explanation') or c.get('evidence')),'owner':_txt(c.get('object_name') or c.get('owner')),'metric':_txt(c.get('metric') or c.get('indicator')),'value':c.get('values') or c.get('value'),'unit':_txt(c.get('unit')),'trust':'VERIFIED_CONFLICT'})
    by_owner={}; by_metric={}
    for r in records:
        if r['owner']: by_owner.setdefault(r['owner'].lower(),[]).append(r['evidence_id'])
        if r['metric']: by_metric.setdefault(r['metric'].lower(),[]).append(r['evidence_id'])
    return {'version':'2.0','records':records,'record_count':len(records),'by_owner':by_owner,'by_metric':by_metric}
