from __future__ import annotations
from typing import Any

def adversarial_gate(result:dict[str,Any], evidence:list[dict[str,Any]]|None=None, critic:dict[str,Any]|None=None)->dict[str,Any]:
    """Every categorical conclusion must survive a conservative challenge pass."""
    out=dict(result); evidence=evidence or []
    kind=str(out.get('verification_kind') or '').upper()
    positive=kind=='VERIFIED_OK' or str(out.get('status') or '').lower() in {'соответствует','confirmed'}
    finding=kind=='PROJECT_FINDING'
    if not (positive or finding):
        out['adversarial_state']='NOT_REQUIRED'; return out
    if positive and out.get('deterministic_gate_passed') and str(out.get('proof_kind') or '').upper() in {
        'STRUCTURED_COMPLETENESS', 'VERIFIED_SET_EVIDENCE'
    }:
        out['adversarial_state']='PASSED'
        out['adversarial_reasons']=[]
        return out
    strong=[e for e in evidence if e.get('kind')=='STRUCTURED_FACT' and e.get('retrieval_score',0)>=65 and str(e.get('judge_verdict') or '').upper() not in {'OTHER_ENTITY','OTHER_METRIC','CONTRADICTS','INSUFFICIENT'}]
    concerns=list((critic or {}).get('concerns') or [])
    contrary_to_conclusion=any(
        str(e.get('judge_verdict') or '').upper()=='CONTRADICTS'
        or (positive and e.get('kind')=='STRUCTURED_CONFLICT' and e.get('retrieval_score',0)>=65)
        for e in evidence
    )
    supporting_conflict=any(e.get('kind')=='STRUCTURED_CONFLICT' and e.get('retrieval_score',0)>=65 for e in evidence)
    if contrary_to_conclusion or concerns or not (strong or (finding and supporting_conflict)):
        out['verification_kind']='REVIEW_QUESTION'; out['verification_state']='Требует проверки специалистом'
        out['adversarial_state']='BLOCKED'; out['adversarial_reasons']=concerns or (['Найдено доказательство, противоречащее выводу'] if contrary_to_conclusion else ['Недостаточно сильного структурированного доказательства'])
    else:
        out['adversarial_state']='PASSED'; out['adversarial_reasons']=[]
    return out
