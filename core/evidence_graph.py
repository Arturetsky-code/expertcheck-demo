from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .normalization import normalize_text

OBJECT_CODES = {'OBJECT_ENTRY','OBJECT_CANDIDATE'}


def _obj_key(item: dict[str, Any]) -> str:
    pos = str(item.get('semantic_anchor_position') or item.get('genplan_position') or '').strip()
    name = normalize_text(item.get('semantic_anchor_name') or item.get('object_hint') or item.get('value_text') or '')
    return f'{pos}|{name}' if pos or name else ''


def build_evidence_graph(findings: Iterable[dict[str, Any]], comparisons: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Compact explainability graph used by passports, risks and reports.

    It deliberately stores references, not raw PDF text, so the graph remains
    small enough for Streamlit Cloud and safe to pass to AI in selected fragments.
    """
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    object_nodes: dict[str, str] = {}

    for idx, item in enumerate(findings):
        key = _obj_key(item)
        if not key:
            continue
        if key not in object_nodes:
            oid = f'OBJ-{len(object_nodes)+1:04d}'
            object_nodes[key] = oid
            nodes[oid] = {
                'kind':'object',
                'name': str(item.get('semantic_anchor_name') or item.get('object_hint') or item.get('value_text') or '').strip(),
                'position': str(item.get('semantic_anchor_position') or item.get('genplan_position') or '').strip(),
            }
        oid = object_nodes[key]
        if str(item.get('parameter_code') or '') in OBJECT_CODES:
            eid = f'EVD-{idx+1:05d}'
            nodes[eid] = {
                'kind':'evidence','document':item.get('document'),'document_type':item.get('document_type'),
                'page':item.get('page'),'section':item.get('section_title'),'table':item.get('table_title'),
                'source_type':item.get('source_type'),'confidence':item.get('core2_confidence') or item.get('confidence'),
            }
            edges.append({'from':oid,'to':eid,'relation':'supported_by'})
            continue
        code = str(item.get('parameter_code') or '').strip()
        if not code:
            continue
        pid = f'{oid}:P:{code}'
        nodes.setdefault(pid, {'kind':'property','parameter_code':code,'parameter_name':item.get('parameter_name')})
        edges.append({'from':oid,'to':pid,'relation':'has_property'})
        vid = f'VAL-{idx+1:05d}'
        nodes[vid] = {
            'kind':'value','value':item.get('value'),'value_text':item.get('value_text'),'unit':item.get('unit'),
            'document':item.get('document'),'document_type':item.get('document_type'),'page':item.get('page'),
            'binding':item.get('binding_status') or item.get('property_binding_status'),
            'confidence':item.get('core2_confidence') or item.get('confidence'),
        }
        edges.append({'from':pid,'to':vid,'relation':'observed_as'})

    comparison_nodes=[]
    for idx,row in enumerate(comparisons):
        obj=normalize_text(row.get('object') or row.get('Объект') or '')
        pos=str(row.get('genplan_position') or '').strip()
        match=next((oid for key,oid in object_nodes.items() if (pos and key.startswith(pos+'|')) or (obj and key.endswith('|'+obj))),None)
        cid=f'CHK-{idx+1:05d}'
        nodes[cid]={'kind':'comparison','parameter_code':row.get('parameter_code'),'status':row.get('status'),'explanation':row.get('explanation')}
        comparison_nodes.append(cid)
        if match: edges.append({'from':match,'to':cid,'relation':'checked_by'})

    return {'nodes':nodes,'edges':edges,'object_count':len(object_nodes),'comparison_count':len(comparison_nodes)}
