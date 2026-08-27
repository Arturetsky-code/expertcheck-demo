from __future__ import annotations
from typing import Any
from .verification_core import classify_verification, domain_summary

DOMAIN_LABELS={"assignment":"Задание на проектирование","normative":"НТД","checklist":"Чек-листы"}


def _txt(v:Any)->str:return str(v or '').strip()


def _legacy_status(kind:str)->str:
    return {"VERIFIED_OK":"CONFIRMED","PROJECT_FINDING":"ISSUE","REVIEW_QUESTION":"REVIEW","SYSTEM_LIMITATION":"SYSTEM_LIMITATION"}.get(kind,"UNRESOLVED")


def _first(documents:list[dict[str,Any]]|None)->dict[str,Any]:
    return (documents or [{}])[0] if documents else {}


def build_review_plan(
    documents:list[dict[str,Any]]|None=None,
    checklist_results:list[dict[str,Any]]|None=None,
    *, assignment_rows:list[dict[str,Any]]|None=None,
    normative_rows:list[dict[str,Any]]|None=None,
    checklist_review:dict[str,Any]|None=None,
    comparisons:list[dict[str,Any]]|None=None,
)->dict[str,Any]:
    """Build the project-specific verification programme.

    Backward compatible with the Alpha 5 report API while also accepting the
    pipeline's already computed domain rows directly.
    """
    first=_first(documents)
    assignment=list(assignment_rows if assignment_rows is not None else (first.get('assignment_compliance') or []))
    normative=list(normative_rows if normative_rows is not None else (first.get('normative_compliance_audit') or []))
    if checklist_review is not None:
        checklist=list(checklist_review.get('results') or [])
    elif checklist_results is not None:
        checklist=list(checklist_results or [])
    else:
        checklist=list((first.get('automatic_checklist_review') or {}).get('results') or [])

    items=[]
    for i,row in enumerate(assignment,1):
        q=classify_verification(row,'assignment'); contract=row.get('evidence_contract_v2') or {}
        items.append({
            'plan_id':row.get('requirement_id') or f'ASSIGN-{i:03d}','domain':'Задание на проектирование','domain_code':'assignment',
            'title':_txt(row.get('requirement_text') or row.get('requirement')),'check_type':_txt(row.get('requirement_type') or row.get('check_type')),
            'scope':_txt(row.get('requirement_scope') or contract.get('scope')),'expected_evidence':_txt(row.get('expected_evidence') or contract.get('expected_evidence')),
            'entity':_txt(row.get('object_name') or row.get('entity') or row.get('scope_entity')),
            'metric':_txt(row.get('parameter_code') or row.get('parameter_name') or row.get('metric')),
            'required_value':row.get('required_value'),'unit':_txt(row.get('unit')),
            'proof_kind':_txt(row.get('proof_kind') or row.get('evidence_quality_state')),
            'deep_evidence_state':_txt(row.get('deep_evidence_state')),
            'adversarial_state':_txt(row.get('deep_evidence_state')),
            'deep_evidence_reasons':list(row.get('deep_evidence_reasons') or []),
            'adversarial_reasons':list(row.get('deep_evidence_reasons') or []),
            'evidence_candidate_count':int(row.get('deep_evidence_candidate_count') or 0),
            'expected_sections':contract.get('expected_sections') or [],'status':_legacy_status(q['verification_kind']),**q,
            'source_id':_txt(row.get('requirement_id') or row.get('source_row')),
            'recommendation':_txt(row.get('recommendation')),
            'coverage_archetype':_txt(row.get('coverage_archetype')),
            'coverage_state':_txt(row.get('coverage_state')),
            'coverage_reason_code':_txt(row.get('coverage_reason_code')),
            'coverage_reason':_txt(row.get('coverage_reason')),
            'missing_evidence_slots':list(row.get('missing_evidence_slots') or []),
            'expected_evidence_route':list(row.get('expected_evidence_route') or []),
            'recipe_status':_txt(row.get('recipe_status')),
            'evidence_level':_txt(row.get('evidence_level') or 'L0'),
            'evidence_level_reason':_txt(row.get('evidence_level_reason')),
            'evidence_coverage_pct':row.get('evidence_coverage_pct'),
            'semantic_consensus_state':_txt(row.get('semantic_consensus_state')),
            'semantic_consensus_completed':int(row.get('semantic_consensus_completed') or 0),
            'checker_family':_txt(row.get('checker_family')),
            'checker_mode':_txt(row.get('checker_mode')),
        })
    for i,row in enumerate(normative,1):
        q=classify_verification(row,'normative')
        items.append({
            'plan_id':row.get('requirement_id') or f'NORM-{i:03d}','domain':'НТД','domain_code':'normative',
            'title':f"{_txt(row.get('source') or row.get('reference'))} {_txt(row.get('paragraph') or row.get('clause'))}: {_txt(row.get('requirement'))}".strip(': '),
            'check_type':_txt(row.get('check_kind')),'scope':_txt(row.get('topic')),'expected_evidence':_txt(row.get('decision_basis')),
            'entity':_txt(row.get('object_name') or row.get('entity')),'metric':_txt(row.get('parameter_code') or row.get('topic')),
            'proof_kind':_txt(row.get('proof_kind') or row.get('coverage_state')),
            'deterministic_gate_passed':bool(
                row.get('final_verification_kind')=='VERIFIED_OK'
                and row.get('proof_kind')=='STRUCTURED_COMPLETENESS'
                and (row.get('structural_check') or {}).get('complete')
            ),
            'deep_evidence_state':_txt(row.get('deep_evidence_state')),
            'adversarial_state':_txt(row.get('deep_evidence_state')),
            'deep_evidence_reasons':list(row.get('deep_evidence_reasons') or []),
            'adversarial_reasons':list(row.get('deep_evidence_reasons') or []),
            'evidence_candidate_count':int(row.get('deep_evidence_candidate_count') or 0),
            'expected_sections':(row.get('evidence_contract') or {}).get('sections') or [],'status':_legacy_status(q['verification_kind']),**q,
            'source_id':_txt(row.get('requirement_id')),
            'recommendation':_txt(row.get('recommendation')),
            'coverage_archetype':_txt(row.get('coverage_archetype') or 'NORMATIVE_REQUIREMENT'),
            'coverage_state':_txt(row.get('coverage_state')),
            'coverage_reason_code':_txt(row.get('coverage_reason_code')),
            'coverage_reason':_txt(row.get('coverage_reason')),
            'missing_evidence_slots':list(row.get('missing_evidence_slots') or []),
            'expected_evidence_route':list(row.get('expected_evidence_route') or []),
            'recipe_status':_txt(row.get('recipe_status')),
            'evidence_level':_txt(row.get('evidence_level') or ('L5' if q['verification_kind'] in {'VERIFIED_OK','PROJECT_FINDING'} else 'L0')),
            'evidence_level_reason':_txt(row.get('evidence_level_reason')),
            'evidence_coverage_pct':row.get('evidence_coverage_pct'),
            'semantic_consensus_state':_txt(row.get('semantic_consensus_state')),
            'semantic_consensus_completed':int(row.get('semantic_consensus_completed') or 0),
            'checker_family':_txt(row.get('checker_family')),
            'checker_mode':_txt(row.get('checker_mode')),
        })
    for i,row in enumerate(checklist,1):
        if row.get('is_heading'):continue
        q=classify_verification(row,'checklist')
        items.append({
            'plan_id':f'CHECK-{i:04d}','domain':'Чек-листы','domain_code':'checklist',
            'title':_txt(row.get('question') or row.get('Позиция по чек-листу')),'check_type':_txt(row.get('typed_check') or row.get('execution_class') or row.get('check_type')),
            'scope':_txt(row.get('automatic_section') or row.get('section') or row.get('Раздел')),'expected_evidence':_txt(row.get('expected_evidence') or row.get('required_evidence')),
            'entity':_txt(row.get('object_name') or row.get('entity')),
            'metric':_txt(row.get('parameter_code') or row.get('parameter_name')),
            'proof_kind':_txt(row.get('proof_kind')),
            'deep_evidence_state':_txt(row.get('deep_evidence_state')),
            'adversarial_state':_txt(row.get('deep_evidence_state')),
            'deep_evidence_reasons':list(row.get('deep_evidence_reasons') or []),
            'adversarial_reasons':list(row.get('deep_evidence_reasons') or []),
            'evidence_candidate_count':int(row.get('deep_evidence_candidate_count') or 0),
            'expected_sections':[row.get('automatic_section')] if row.get('automatic_section') else [],'status':_legacy_status(q['verification_kind']),**q,
            'source_id':_txt(row.get('item_no') or row.get('position')),
            'recommendation':_txt(row.get('recommendation')),
            'coverage_archetype':_txt(row.get('coverage_archetype')),
            'coverage_state':_txt(row.get('coverage_state')),
            'coverage_reason_code':_txt(row.get('coverage_reason_code')),
            'coverage_reason':_txt(row.get('coverage_reason')),
            'missing_evidence_slots':list(row.get('missing_evidence_slots') or []),
            'expected_evidence_route':list(row.get('expected_evidence_route') or []),
            'recipe_status':_txt(row.get('recipe_status')),
            'evidence_level':_txt(row.get('evidence_level') or 'L0'),
            'evidence_level_reason':_txt(row.get('evidence_level_reason')),
            'evidence_coverage_pct':row.get('evidence_coverage_pct'),
            'semantic_consensus_state':_txt(row.get('semantic_consensus_state')),
            'semantic_consensus_completed':int(row.get('semantic_consensus_completed') or 0),
            'checker_family':_txt(row.get('checker_family')),
            'checker_mode':_txt(row.get('checker_mode')),
        })

    raw_summaries={
        'assignment':domain_summary(assignment,'assignment'),
        'normative':domain_summary(normative,'normative'),
        'checklist':domain_summary(checklist,'checklist'),
    }
    domains={}
    for code,s in raw_summaries.items():
        legacy={
            'total':s['total'],'completed':s['completed'],'coverage_pct':s['automatic_coverage_pct'],
            'confirmed':s['verified_ok'],'issue':s['project_findings'],'review':s['review_questions'],
            'system_limitation':s['system_limitations'],'unresolved':0,'label':DOMAIN_LABELS[code],
            **s,
        }
        domains[DOMAIN_LABELS[code]]=legacy
        domains[code]=legacy
    return {
        'version':'2.0-coverage-reason-plan','principle':'Сначала контракт покрытия → затем целевое доказательство → затем квалифицированный вывод',
        'items':items,'checks':items,'domains':domains,'total':len(items),'checks_total':len(items),
        'completed':sum(x['completed'] for x in raw_summaries.values()),
        'project_findings':sum(x['project_findings'] for x in raw_summaries.values()),
        'review_questions':sum(x['review_questions'] for x in raw_summaries.values()),
        'system_limitations':sum(x['system_limitations'] for x in raw_summaries.values()),
    }


def user_visible_plan_items(plan:dict[str,Any])->list[dict[str,Any]]:
    return list(plan.get('items') or [])
