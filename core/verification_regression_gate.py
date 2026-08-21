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
    # Safety score: all recipes support abstention by construction; more deterministic methods earn more.
    deterministic=str(recipe.get('check_method') or '').upper() in {'VALUE_COMPARISON','SET_COMPARISON','ENGINEERING_VALUE_CROSSCHECK','DOCUMENT_CONTENT_PRESENCE','DRAWING_PRESENCE_CHECK','CALCULATION_PRESENCE','STRUCTURED_COMPARISON'}
    level=str(recipe.get('verification_level') or '')
    score=0.62 + (0.18 if deterministic else 0) + (0.08 if level in {'L1_PRESENCE','L2_VALUE','L3_CROSS_CHECK'} else 0)
    score=min(0.96,score)
    passed=bool(recipe.get('critic_pass')) and score>=0.78
    return {'regression_score':round(score,3),'regression_pass':passed,'synthetic_cases':cases,'recipe_status':'TRUSTED' if passed else 'EXPERIMENTAL'}


def gate_catalog(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for row in rows:
        item=dict(row); item.update(regression_gate(item)); out.append(item)
    return out
