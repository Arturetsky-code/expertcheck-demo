from __future__ import annotations
import re
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code
from .directed_evidence import units_compatible

_STOP={'проект','проектом','проектной','требование','предусмотреть','принять','должен','должна','должны','необходимо','объект','объекта','значение'}

def _tokens(text: Any)->set[str]:
    return {w for w in re.findall(r'[а-яa-z0-9-]{4,}', normalize_text(text), re.I) if w not in _STOP}

def semantic_evidence_score(requirement:dict[str,Any], candidate:dict[str,Any])->dict[str,Any]:
    code=canonical_parameter_code(requirement.get('parameter_code'))
    if code and canonical_parameter_code(candidate.get('parameter_code')) != code:
        return {'eligible':False,'score':0,'reason':'Не совпадает инженерный показатель.'}
    if requirement.get('unit') and candidate.get('unit') and not units_compatible(requirement.get('unit'),candidate.get('unit'),code):
        return {'eligible':False,'score':0,'reason':'Несовместимые единицы измерения.'}
    q=_tokens(' '.join(str(requirement.get(k) or '') for k in ('source_row_title','requirement_text','object_name')))
    c=_tokens(' '.join(str(candidate.get(k) or '') for k in ('context','object','parameter_name')))
    overlap=q & c
    scope=str(requirement.get('requirement_scope') or (requirement.get('evidence_contract_v2') or {}).get('scope') or '')
    owner_required=scope in {'OBJECT_SPECIFIC','EQUIPMENT_SPECIFIC'}
    owner_ok=bool(candidate.get('owner_match')) if owner_required else True
    score=45 + min(25,len(overlap)*5) + (15 if candidate.get('unit_compatible') else 0) + (15 if owner_ok else 0)
    if owner_required and not owner_ok:
        return {'eligible':False,'score':score,'reason':'Не подтверждён владелец показателя.'}
    return {'eligible':score>=70,'score':min(100,score),'reason':'Смысл требования, показатель, единица и область действия совместимы.' if score>=70 else 'Недостаточно смысловых признаков для продвижения доказательства.','matched_terms':sorted(overlap)}

def promote_candidates(requirement:dict[str,Any], candidates:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for raw in candidates or []:
        item=dict(raw); assessment=semantic_evidence_score(requirement,item)
        item['semantic_evidence_score']=assessment['score'];item['semantic_evidence_reason']=assessment['reason']
        item['matched_requirement_terms']=assessment.get('matched_terms') or []
        if assessment['eligible']:
            item['evidence_state']='verified_candidate';item['promotion_method']='SEMANTIC_CONTRACT_MATCH'
        out.append(item)
    return out
