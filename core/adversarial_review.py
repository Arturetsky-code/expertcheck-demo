from __future__ import annotations
from typing import Any

def adversarial_gate(result:dict[str,Any], evidence:list[dict[str,Any]]|None=None, critic:dict[str,Any]|None=None)->dict[str,Any]:
    """Positive conclusions must survive a conservative challenge pass."""
    out=dict(result); evidence=evidence or []
    positive=str(out.get('verification_kind') or '').upper()=='VERIFIED_OK' or str(out.get('status') or '').lower() in {'соответствует','confirmed'}
    if not positive:
        out['adversarial_state']='NOT_REQUIRED'; return out
    strong=[e for e in evidence if e.get('kind')=='STRUCTURED_FACT' and e.get('retrieval_score',0)>=65 and str(e.get('judge_verdict') or '').upper() not in {'OTHER_ENTITY','OTHER_METRIC','CONTRADICTS','INSUFFICIENT'}]
    concerns=list((critic or {}).get('concerns') or [])
    contradiction=any(
        str(e.get('judge_verdict') or '').upper()=='CONTRADICTS'
        or (e.get('kind')=='STRUCTURED_CONFLICT' and e.get('retrieval_score',0)>=65)
        for e in evidence
    )
    if contradiction or concerns or not strong:
        out['verification_kind']='REVIEW_QUESTION'; out['verification_state']='Требует проверки специалистом'
        out['adversarial_state']='BLOCKED'; out['adversarial_reasons']=concerns or (['Найдено противоречащее доказательство'] if contradiction else ['Недостаточно сильного структурированного доказательства'])
    else:
        out['adversarial_state']='PASSED'; out['adversarial_reasons']=[]
    return out
