from __future__ import annotations
from typing import Any

WEAK_EVIDENCE={'TEXT_OR_TABLE','RELEVANT_FRAGMENT','ENGINEERING_EVIDENCE','SPECIALIST_REVIEW','NORMATIVE_CONTEXT'}
STRONG_EVIDENCE={'STRUCTURED_VALUE','STRUCTURED_COMPARISON','VERIFIED_SET_EVIDENCE','STRUCTURED_COMPLETENESS','VERIFIED_ENGINEERING_EVIDENCE','NORMATIVE_EVIDENCE','VERIFIED_CLAUSE','DOCUMENT_IDENTITY','PAGE_REFERENCE'}


def critique_recipe(recipe:dict[str,Any])->dict[str,Any]:
    issues=[]; score=float(recipe.get('confidence') or 0.0)
    level=str(recipe.get('verification_level') or '')
    evidence=set(str(x).upper() for x in (recipe.get('required_evidence') or []))
    method=str(recipe.get('check_method') or '').upper()
    if not str(recipe.get('title') or '').strip():
        issues.append('CRITICAL: отсутствует формулировка проверки'); score-=0.5
    if level in {'L4_COMPLETENESS','L5_ENGINEERING_COMPLIANCE'} and not (evidence & STRONG_EVIDENCE):
        issues.append('CRITICAL: сложная проверка не имеет сильного доказательного типа'); score-=0.35
    if level=='L5_ENGINEERING_COMPLIANCE' and method in {'SPECIALIST_REVIEW','ENGINEERING_SEMANTIC_REVIEW','SEMANTIC','NORMATIVE_CONTENT_REVIEW'}:
        issues.append('Смысловой рецепт пока не имеет специализированного checker-а'); score-=0.18
    if recipe.get('domain')=='normative' and 'VERIFIED_CLAUSE' not in evidence:
        issues.append('CRITICAL: нормативная проверка не требует верифицированного пункта'); score-=0.4
    if not recipe.get('expected_sections') and recipe.get('domain') in {'checklist','assignment'}:
        issues.append('Не определены ожидаемые разделы; поиск evidence может быть слишком широким'); score-=0.08
    if not recipe.get('abstain_policy'):
        issues.append('CRITICAL: отсутствует политика воздержания'); score-=0.25
    if recipe.get('domain')=='practice':
        issues.append('Правило экспертной практики используется только как приоритизация, не как самостоятельный вывод')
        score=min(score,0.68)
    score=max(0.0,min(1.0,score))
    critical=any(x.startswith('CRITICAL:') for x in issues)
    return {'critic_score':round(score,3),'critic_pass':score>=0.70 and not critical,'critic_issues':issues}


def critique_catalog(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for row in rows:
        item=dict(row); crit=critique_recipe(item); item.update(crit); item['issues']=crit['critic_issues']; out.append(item)
    return out
