from __future__ import annotations
from typing import Any
from .project_evidence_database import build_project_evidence_database
from .evidence_retrieval_cascade import retrieve_evidence, rerank_with_judgements
from .adversarial_review import adversarial_gate
from .evidence_retrieval_cascade import retrieval_diagnostics

FINAL_STATES={
    'VERIFIED_OK':'Соответствует',
    'PROJECT_FINDING':'Выявлено несоответствие',
    'REVIEW_QUESTION':'Требует проверки специалистом',
    'SYSTEM_LIMITATION':'Не проверено автоматически',
    'INFORMATIONAL':'Информация',
}

def run_deep_evidence_review(checks:list[dict[str,Any]], documents:list[dict[str,Any]]|None=None, facts:list[dict[str,Any]]|None=None, comparisons:list[dict[str,Any]]|None=None, page_corpus:list[dict[str,Any]]|None=None, judgements:dict[str,list[dict[str,Any]]]|None=None, critics:dict[str,dict[str,Any]]|None=None)->dict[str,Any]:
    db=build_project_evidence_database(documents,facts,comparisons,page_corpus=page_corpus); results=[]
    for check in checks or []:
        cid=str(check.get('plan_id') or check.get('source_id') or len(results)+1)
        candidates=retrieve_evidence(check,db)
        candidates=rerank_with_judgements(check,candidates,(judgements or {}).get(cid))
        base=dict(check); base['evidence_candidates']=candidates; base['evidence_candidate_count']=len(candidates)
        base.update(retrieval_diagnostics(check,db,candidates))
        base=adversarial_gate(base,candidates,(critics or {}).get(cid)); results.append(base)
    return {'version':'1.0','passes':['PROJECT_RECONSTRUCTION','TARGETED_VERIFICATION','ADVERSARIAL_REVIEW'],'evidence_db':db,'results':results,'metrics':{'checks':len(results),'with_candidates':sum(bool(x['evidence_candidates']) for x in results),'adversarial_blocked':sum(x.get('adversarial_state')=='BLOCKED' for x in results)}}


def _apply_final_verdict(row:dict[str,Any], verdict:dict[str,Any])->None:
    """Write the adjudicated verdict back to the domain row.

    Deep Evidence used to be a sidecar payload attached to documents.  Reports
    then rebuilt their metrics from the pre-review rows and silently discarded
    every adversarial downgrade.  The explicit ``final_*`` fields form the
    fail-closed contract consumed by verification_core and the reports.
    """
    kind=str(verdict.get('verification_kind') or 'INFORMATIONAL').upper()
    state=str(verdict.get('verification_state') or FINAL_STATES.get(kind,'Информация'))
    row['pre_deep_evidence_verification_kind']=row.get('verification_kind')
    row['final_verification_kind']=kind
    row['final_verification_state']=state
    row['verification_kind']=kind
    row['verification_state']=state
    row['deep_evidence_state']=verdict.get('adversarial_state') or 'NOT_REQUIRED'
    row['deep_evidence_candidate_count']=int(verdict.get('evidence_candidate_count') or 0)
    row['deep_evidence_reasons']=list(verdict.get('adversarial_reasons') or [])
    row['deep_evidence_candidates']=list(verdict.get('evidence_candidates') or [])[:10]

    if kind=='REVIEW_QUESTION':
        if str(row.get('evidence_level') or '')=='L5':
            row['evidence_level']='L4'
            row['evidence_level_reason']='Адресный пакет сохранён, но итоговый вывод удержан независимой проверкой достаточности.'
        row['status']='Требует проверки'
        reason='; '.join(row['deep_evidence_reasons']) or row.get('decision_basis') or 'Найден адресный кандидат, требующий решения специалиста.'
        row['decision_basis']=reason
        if 'дополнительное действие не требуется' in str(row.get('recommendation') or '').lower() or not row.get('recommendation'):
            row['recommendation']='Проверить указанные доказательства и зафиксировать решение специалиста.'
        # Coverage is a final-verdict property.  A candidate that was initially
        # verified but failed the adversarial pass must not remain counted as
        # automatically completed in the coverage matrix.
        row['coverage_state']='TARGETED_REVIEW'
        row['coverage_reason_code']=(
            'ADVERSARIAL_OR_SEMANTIC_GATE_BLOCKED'
            if verdict.get('adversarial_state')=='BLOCKED'
            else row.get('coverage_reason_code') or 'EVIDENCE_CONTRACT_UNSATISFIED'
        )
        row['coverage_reason']=reason
        if verdict.get('adversarial_state')=='BLOCKED':
            missing=list(row.get('missing_evidence_slots') or [])
            if 'INDEPENDENT_SEMANTIC_CONFIRMATION' not in missing:
                missing.append('INDEPENDENT_SEMANTIC_CONFIRMATION')
            row['missing_evidence_slots']=missing
    elif kind=='SYSTEM_LIMITATION':
        if str(row.get('evidence_level') or '')=='L5':
            row['evidence_level']='L4'
            row['evidence_level_reason']='Доказательство найдено, но строгий итоговый gate не завершён.'
        row['status']='Не проверено системой'
        row['coverage_state']='AUTOMATION_GAP'
        row['coverage_reason_code']=row.get('coverage_reason_code') or 'EVIDENCE_CONTRACT_UNSATISFIED'
        row['coverage_reason']=row.get('decision_basis') or 'Автоматическая проверка не располагает достаточным доказательством.'
    elif kind=='VERIFIED_OK' and str(row.get('status') or '').strip() in {'','Требует проверки','Не проверено системой'}:
        # Deep Evidence is currently allowed to preserve a verified result, not
        # to promote an unresolved check.  This branch only normalises legacy
        # rows whose final verified verdict was supplied by a deterministic pass.
        row['status']='Соответствует'
        row['coverage_state']='AUTOMATED_COMPLETE'
        row['coverage_reason_code']='EVIDENCE_CONTRACT_SATISFIED'


def apply_deep_evidence_decisions(
    review:dict[str,Any],
    *,
    assignment_rows:list[dict[str,Any]]|None=None,
    normative_rows:list[dict[str,Any]]|None=None,
    checklist_review:dict[str,Any]|None=None,
)->dict[str,int]:
    """Merge Deep Evidence verdicts into every source domain by stable plan id."""
    verdicts={str(x.get('plan_id') or ''):x for x in (review.get('results') or []) if x.get('plan_id')}
    applied=blocked=0

    def apply_rows(rows:list[dict[str,Any]], id_for)->None:
        nonlocal applied,blocked
        for index,row in enumerate(rows,1):
            verdict=verdicts.get(str(id_for(row,index)))
            if not verdict:
                continue
            _apply_final_verdict(row,verdict); applied+=1
            blocked+=int(verdict.get('adversarial_state')=='BLOCKED')

    apply_rows(list(assignment_rows or []),lambda row,i:row.get('requirement_id') or f'ASSIGN-{i:03d}')
    apply_rows(list(normative_rows or []),lambda row,i:row.get('requirement_id') or f'NORM-{i:03d}')
    checklist_rows=list((checklist_review or {}).get('results') or [])
    apply_rows(checklist_rows,lambda _row,i:f'CHECK-{i:04d}')
    return {'applied':applied,'blocked':blocked,'unmatched':max(0,len(verdicts)-applied)}
