from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .verification_recipe_factory import generate_recipe_candidates
from .verification_recipe_critic import critique_catalog
from .verification_regression_gate import gate_catalog


def build_factory_catalog(root:str|Path, assignment_rows:list[dict[str,Any]]|None=None)->dict[str,Any]:
    root=Path(root)
    candidates=generate_recipe_candidates(root,assignment_rows)
    reviewed=critique_catalog(candidates)
    gated=gate_catalog(reviewed)
    trusted=[x for x in gated if x.get('recipe_status')=='TRUSTED']
    experimental=[x for x in gated if x.get('recipe_status')!='TRUSTED']
    by_domain={}
    for row in gated:
        d=row.get('domain','unknown'); by_domain.setdefault(d,{'total':0,'trusted':0,'experimental':0}); by_domain[d]['total']+=1
        by_domain[d]['trusted' if row.get('recipe_status')=='TRUSTED' else 'experimental']+=1
    return {
        'version':'1.0','principle':'AI/knowledge-generated recipes are candidates until critic + regression gate approve them.',
        'total':len(gated),'trusted_count':len(trusted),'experimental_count':len(experimental),'by_domain':by_domain,
        'trusted':trusted,'experimental':experimental,
    }


def save_factory_catalog(root:str|Path, output: str|Path|None=None)->dict[str,Any]:
    root=Path(root); result=build_factory_catalog(root)
    path=Path(output) if output else root/'verification_recipe_library_v1.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def recipe_lookup(factory:dict[str,Any])->dict[str,dict[str,Any]]:
    return {str(x.get('source_id')):x for x in factory.get('trusted') or []}
