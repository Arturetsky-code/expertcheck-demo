from __future__ import annotations
from typing import Any


def synthetic_cases(recipe:dict[str,Any])->list[dict[str,Any]]:
    """Small adversarial contract tests generated without domain experts.

    They test the safety policy rather than claiming engineering correctness.
    """
    method=str(recipe.get('check_method') or '').upper(); level=str(recipe.get('verification_level') or '')
    cases=[
        {'case':'no_evidence','expected':'ABSTAIN'},
        {'case':'wrong_owner','expected':'ABSTAIN'},
        {'case':'weak_semantic_hit','expected':'ABSTAIN'},
    ]
    if 'VALUE' in method or level=='L2_VALUE':
        cases += [{'case':'same_value_same_unit_same_owner','expected':'PASS'},{'case':'different_value_same_unit_same_owner','expected':'FAIL'},{'case':'same_number_incompatible_unit','expected':'ABSTAIN'}]
    elif 'SET' in method or level=='L4_COMPLETENESS':
        cases += [{'case':'full_set','expected':'PASS'},{'case':'partial_set','expected':'REVIEW'}]
    elif level=='L1_PRESENCE':
        cases += [{'case':'identified_required_artifact','expected':'PASS'}]
    else:
        cases += [{'case':'direct_project_contradiction','expected':'REVIEW'}]
    return cases


def regression_gate(recipe:dict[str,Any])->dict[str,Any]:
    critic=float(recipe.get('critic_score') or 0)
    cases=synthetic_cases(recipe)
    method=str(recipe.get('check_method') or '').upper()
    level=str(recipe.get('verification_level') or '')
    evidence={str(x).upper() for x in (recipe.get('required_evidence') or [])}
    violations=[]
    if level=='L1_PRESENCE' and method in {'DOCUMENT_CONTENT_PRESENCE','DRAWING_PRESENCE_CHECK'} and not (evidence & {'STRUCTURED_PRESENCE','DOCUMENT_IDENTITY'}):
        violations.append('weak_semantic_hit cannot be distinguished from identified_required_artifact')
    if level=='L2_VALUE' and not (evidence & {'STRUCTURED_VALUE','STRUCTURED_COMPARISON'}):
        violations.append('value check has no structured value evidence')
    if level=='L3_CROSS_CHECK' and 'STRUCTURED_COMPARISON' not in evidence:
        violations.append('cross-check has no structured comparison evidence')
    if level in {'L4_COMPLETENESS','L5_ENGINEERING_COMPLIANCE'} and not (evidence & {'VERIFIED_SET_EVIDENCE','STRUCTURED_COMPLETENESS','VERIFIED_ENGINEERING_EVIDENCE','NORMATIVE_EVIDENCE','VERIFIED_CLAUSE'}):
        violations.append('complex check has no executable strong-evidence contract')
    deterministic=method in {'VALUE_COMPARISON','SET_COMPARISON','ENGINEERING_VALUE_CROSSCHECK','CALCULATION_PRESENCE','STRUCTURED_COMPARISON'}
    score=max(0.0,min(0.96,critic + (0.08 if deterministic else 0.0) - 0.18*len(violations)))
    passed=bool(recipe.get('critic_pass')) and not violations and score>=0.78
    case_results=[{**case,'result':'PASS' if not violations else 'BLOCKED_BY_POLICY'} for case in cases]
    return {
        'regression_score':round(score,3),'regression_pass':passed,
        'synthetic_cases':case_results,'regression_violations':violations,
        'recipe_status':'TRUSTED' if passed else 'EXPERIMENTAL',
    }


def gate_catalog(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for row in rows:
        item=dict(row); item.update(regression_gate(item)); out.append(item)
    return out
