from __future__ import annotations
from typing import Any
from .verification_core import classify_verification


def qualify_checklist_results(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    """Normalize checklist results for the Review Planner and reports.

    Keyword hits remain candidates. Only structured/deterministic evidence can be
    considered an automatic completion; unsupported items are explicitly product
    coverage gaps rather than user action items.
    """
    out=[]
    for row in rows or []:
        item=dict(row)
        proof=str(item.get("proof_kind") or (item.get("compiled_rule") or {}).get("negative_result_policy") or "").upper()
        if item.get("status")=="Требует проверки" and proof in {"CANDIDATE_EVIDENCE","AI_WITH_EVIDENCE","CONSERVATIVE",""}:
            # Candidate evidence is not a completed check.
            item.setdefault("coverage_note","Найден кандидат в доказательства; автоматическое соответствие не установлено.")
            item['specialist_review_ready']=True
        item.update(classify_verification(item,"checklist"))
        if item.get('specialist_review_ready') and item.get('verification_kind')=='SYSTEM_LIMITATION':
            item.update({'verification_kind':'REVIEW_QUESTION','verification_state':'Требует проверки специалистом','finding_type':'REVIEW_QUESTION'})
        out.append(item)
    return out
