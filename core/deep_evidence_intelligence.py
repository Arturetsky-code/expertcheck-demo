from __future__ import annotations
from typing import Any
from .project_evidence_database import build_project_evidence_database
from .evidence_retrieval_cascade import retrieve_evidence, rerank_with_judgements
from .adversarial_review import adversarial_gate

def run_deep_evidence_review(checks:list[dict[str,Any]], documents:list[dict[str,Any]]|None=None, facts:list[dict[str,Any]]|None=None, comparisons:list[dict[str,Any]]|None=None, judgements:dict[str,list[dict[str,Any]]]|None=None, critics:dict[str,dict[str,Any]]|None=None)->dict[str,Any]:
    db=build_project_evidence_database(documents,facts,comparisons); results=[]
    for check in checks or []:
        cid=str(check.get('plan_id') or check.get('source_id') or len(results)+1)
        candidates=retrieve_evidence(check,db)
        candidates=rerank_with_judgements(check,candidates,(judgements or {}).get(cid))
        base=dict(check); base['evidence_candidates']=candidates; base['evidence_candidate_count']=len(candidates)
        base=adversarial_gate(base,candidates,(critics or {}).get(cid)); results.append(base)
    return {'version':'1.0','passes':['PROJECT_RECONSTRUCTION','TARGETED_VERIFICATION','ADVERSARIAL_REVIEW'],'evidence_db':db,'results':results,'metrics':{'checks':len(results),'with_candidates':sum(bool(x['evidence_candidates']) for x in results),'adversarial_blocked':sum(x.get('adversarial_state')=='BLOCKED' for x in results)}}
