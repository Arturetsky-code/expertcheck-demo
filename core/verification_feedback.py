from __future__ import annotations
import hashlib
from typing import Any


def labeled_case(*,domain:str, check_id:str, automated_result:str, specialist_result:str, evidence:Any=None, comment:str='')->dict[str,Any]:
    key=f'{domain}|{check_id}|{automated_result}|{specialist_result}'.encode('utf-8')
    agrees=str(automated_result or '').strip().lower()==str(specialist_result or '').strip().lower()
    return {
        'case_id':'LC-'+hashlib.sha1(key).hexdigest()[:12].upper(),'domain':domain,'check_id':check_id,
        'automated_result':automated_result,'specialist_result':specialist_result,'agreement':agrees,
        'evidence':evidence,'comment':comment,'use_for':'REGRESSION_AND_RERANKING',
    }


def feedback_summary(rows:list[dict[str,Any]])->dict[str,Any]:
    total=len(rows or []); agreed=sum(1 for x in rows or [] if x.get('agreement'))
    return {'labeled_cases':total,'agreement_count':agreed,'disagreement_count':total-agreed,'agreement_pct':round(100*agreed/max(1,total),1)}
