from __future__ import annotations
import json
from typing import Any

SYSTEM = """Вы — Evidence Reasoner системы ExpertCheck. Анализируйте ТОЛЬКО переданное требование и переданные проектные доказательства. Не используйте память о проекте и не придумывайте отсутствующие факты. Верните только JSON: {\"applicable\":true|false|null,\"evidence_status\":\"confirmed|contradicted|insufficient|not_applicable\",\"reason\":\"краткое проверяемое объяснение\",\"evidence_indexes\":[],\"confidence\":0.0}. Статус contradicted допустим только при прямом содержательном противоречии в переданных доказательствах. Отсутствие найденного доказательства всегда insufficient, а не contradicted."""

def _parse_json(text:str)->dict[str,Any]|None:
    raw=str(text or '').strip().strip('`')
    if raw.lower().startswith('json'):
        raw=raw[4:].lstrip('\n ')
    try:
        obj=json.loads(raw)
        return obj if isinstance(obj,dict) else None
    except Exception:
        return None

def review_packet(provider:Any, packet:dict[str,Any])->dict[str,Any]:
    if provider is None:
        return {'status':'AI_NOT_CONFIGURED','categorical':False}
    try:
        result=provider.generate(json.dumps(packet,ensure_ascii=False,indent=2),SYSTEM)
    except Exception as exc:
        return {'status':'AI_ERROR','error':str(exc),'categorical':False}
    if not getattr(result,'ok',False):
        return {'status':'AI_ERROR','error':getattr(result,'error',''),'categorical':False}
    parsed=_parse_json(getattr(result,'text',''))
    if not parsed:
        return {'status':'AI_INVALID_RESPONSE','categorical':False}
    state=str(parsed.get('evidence_status') or 'insufficient')
    parsed['categorical']=state=='contradicted' and bool(packet.get('categorical_conclusion_allowed'))
    parsed['policy']='AI не превращает отсутствие находки в нарушение; категоричный вывод требует разрешения Evidence Contract.'
    return parsed

def review_assignment_rows(provider:Any, rows:list[dict[str,Any]], limit:int=12)->dict[str,Any]:
    reviewed=0; confirmed=0; contradicted=0
    for row in rows:
        if reviewed>=limit: break
        contract=row.get('evidence_contract_v2') or {}
        candidates=row.get('evidence_candidates') or []
        if not contract.get('ai_allowed') or not candidates: continue
        packet=dict(row.get('evidence_packet') or {})
        packet['categorical_conclusion_allowed']=False
        verdict=review_packet(provider,packet)
        row['ai_evidence_review']=verdict; reviewed+=1
        state=verdict.get('evidence_status')
        if state=='confirmed':
            confirmed+=1
            # AI confirmation remains review-level unless a deterministic checker exists.
            if row.get('status') in {'Требуется смысловая проверка','Требует проверки'}:
                row['status']='Предварительно подтверждено AI'
                row['decision_basis']='AI сопоставил конкретное требование с переданным evidence packet. Результат не является категоричным без специализированного checker.'
        elif state=='contradicted':
            contradicted+=1
            row['status']='Требует проверки'
            row['decision_basis']='AI обнаружил потенциальное содержательное противоречие в переданном evidence packet; требуется подтверждение специализированным checker/специалистом.'
    return {'reviewed':reviewed,'confirmed':confirmed,'contradicted':contradicted}
