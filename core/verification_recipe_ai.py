from __future__ import annotations
import json,re
from typing import Any


def _json_obj(text:str)->dict[str,Any]:
    raw=str(text or '').strip()
    if raw.startswith('```'):
        raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S)
    try:
        obj=json.loads(raw); return obj if isinstance(obj,dict) else {}
    except Exception:
        m=re.search(r'\{.*\}',raw,re.S)
        if not m:return {}
        try:
            obj=json.loads(m.group(0)); return obj if isinstance(obj,dict) else {}
        except Exception:return {}


def generate_recipe_with_ai(provider, source:dict[str,Any], domain:str)->tuple[Any,dict[str,Any]]:
    """Ask AI to structure a candidate recipe. Never marks it trusted."""
    system='''Ты проектировщик проверочных алгоритмов ExpertCheck. Верни ТОЛЬКО JSON. Не делай вывод о соответствии проекта. Не придумывай НТД. Если автоматизация ненадёжна, явно укажи abstain.\nJSON: {"check_method":"...","verification_level":"L1_PRESENCE|L2_VALUE|L3_CROSS_CHECK|L4_COMPLETENESS|L5_ENGINEERING_COMPLIANCE","scope":"...","expected_sections":[],"required_evidence":[],"parameter_codes":[],"owner_terms":[],"positive_policy":"...","negative_policy":"...","abstain_policy":"...","confidence":0.0}'''
    prompt='Контур: '+str(domain)+'\nИсточник проверки:\n'+json.dumps(source,ensure_ascii=False)[:10000]
    result=provider.generate(prompt,system)
    return result,_json_obj(getattr(result,'text','') if result else '')


def critique_recipe_with_ai(provider, recipe:dict[str,Any])->tuple[Any,dict[str,Any]]:
    system='''Ты критик инженерного проверочного рецепта. Ищи способы ложноположительного и ложноотрицательного вывода. Верни ТОЛЬКО JSON: {"safe":true|false,"score":0.0,"critical_issues":[],"improvements":[],"must_abstain_when":[]}. Будь консервативен: отсутствие найденного evidence не доказывает нарушение.'''
    prompt=json.dumps(recipe,ensure_ascii=False)[:12000]
    result=provider.generate(prompt,system)
    return result,_json_obj(getattr(result,'text','') if result else '')


def consensus_decision(reviews:list[dict[str,Any]])->dict[str,Any]:
    clean=[x for x in reviews if isinstance(x,dict) and x]
    if not clean:return {'consensus':'NO_DATA','safe':False,'score':0.0}
    safes=[bool(x.get('safe')) for x in clean]
    scores=[float(x.get('score') or 0) for x in clean]
    # Disagreement always resolves conservatively.
    unanimous=all(safes) or not any(safes)
    safe=all(safes) and min(scores,default=0)>=0.75
    return {'consensus':'AGREE' if unanimous else 'DISAGREE','safe':safe,'score':round(min(scores),3),'reviews':clean}
