from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable
from .normalization import normalize_text


def object_learning_examples(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out=[]
    for row in rows:
        decision=str(row.get('Решение пользователя') or 'Не задано')
        if decision=='Не задано':continue
        out.append({
            'kind':'object_decision',
            'name':str(row.get('Наименование объекта') or ''),
            'position':str(row.get('Позиция по ГП') or ''),
            'included':bool(row.get('Включить')),
            'reason':decision,
            'comment':str(row.get('Комментарий пользователя') or ''),
            'core_decision':str(row.get('Решение Object Intelligence') or ''),
            'source_hint':str(row.get('Основание включения') or ''),
        })
    return out


def merge_examples(existing: list[dict[str, Any]], new: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result=list(existing or []); seen={json.dumps(x,ensure_ascii=False,sort_keys=True) for x in result}
    for row in new:
        key=json.dumps(row,ensure_ascii=False,sort_keys=True)
        if key not in seen:
            result.append(dict(row)); seen.add(key)
    return result[-1000:]


def build_learning_pack(object_examples: list[dict[str, Any]], risk_decisions: dict[str, Any] | None=None) -> dict[str, Any]:
    return {
        'format':'ExpertCheckLearningPack/1.0',
        'generated_at':datetime.now(timezone.utc).isoformat(),
        'object_examples':list(object_examples or []),
        'risk_decisions':dict(risk_decisions or {}),
    }


def learning_pack_bytes(pack: dict[str, Any]) -> bytes:
    return json.dumps(pack,ensure_ascii=False,indent=2).encode('utf-8')


def parse_learning_pack(data: bytes) -> dict[str, Any]:
    obj=json.loads(data.decode('utf-8'))
    if not isinstance(obj,dict) or obj.get('format')!='ExpertCheckLearningPack/1.0':
        raise ValueError('Неподдерживаемый формат learning pack')
    return obj


def apply_learning_examples(findings: Iterable[dict[str, Any]], examples: list[dict[str, Any]]) -> int:
    """Apply only conservative repeated exclusions. One example never creates a global rule."""
    from collections import Counter
    excluded=Counter()
    for ex in examples or []:
        if ex.get('kind')=='object_decision' and not ex.get('included'):
            name=normalize_text(ex.get('name') or '')
            reason=normalize_text(ex.get('reason') or '')
            if name and any(x in reason for x in ('файл','ошибочно','дублиру','оборудование')):
                excluded[name]+=1
    applied=0
    for item in findings:
        if str(item.get('parameter_code') or '') not in {'OBJECT_ENTRY','OBJECT_CANDIDATE'}:continue
        name=normalize_text(item.get('value_text') or item.get('object_hint') or '')
        if excluded.get(name,0) < 2:continue
        item['learning_rule_blocked']=True
        item['learning_rule_reason']=f'Кандидат ранее исключался пользователем {excluded[name]} раз(а) по совпадающему наименованию.'
        item['object_intelligence_decision']='blocked'
        item['object_intelligence_confidence']=0
        item['object_intelligence_reason']='Learning Engine: '+item['learning_rule_reason']
        item['object_trust_score']=-900
        applied+=1
    return applied
