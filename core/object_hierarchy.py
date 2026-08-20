from __future__ import annotations
from typing import Any
from .normalization import normalize_text


def position_parent(position:str)->str:
    parts=[p for p in str(position or '').strip().split('.') if p]
    return '.'.join(parts[:-1]) if len(parts)>1 else ''


def build_hierarchy(rows:list[dict[str,Any]])->dict[str,Any]:
    nodes={}
    for r in rows or []:
        pos=str(r.get('Позиция по ГП') or r.get('position') or '').strip()
        name=str(r.get('Наименование объекта') or r.get('name') or r.get('object_name') or '').strip()
        if pos:
            nodes[pos]={'position':pos,'name':name,'parent':position_parent(pos),'children':[]}
    for pos,node in nodes.items():
        par=node['parent']
        if par in nodes: nodes[par]['children'].append(pos)
    return {'nodes':nodes,'roots':[p for p,n in nodes.items() if not n['parent'] or n['parent'] not in nodes]}


def group_is_satisfied(position:str, hierarchy:dict[str,Any])->bool:
    node=(hierarchy.get('nodes') or {}).get(str(position or ''))
    if not node: return False
    return bool(node.get('children'))
