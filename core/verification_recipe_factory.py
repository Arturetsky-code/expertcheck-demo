from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

from .checklist_compiler import compile_item, infer_verification_level
from .normalization import normalize_text
from .requirement_contracts import build_contract


@dataclass
class VerificationRecipe:
    recipe_id: str
    domain: str
    source_id: str
    title: str
    verification_level: str
    check_method: str
    scope: str
    expected_sections: list[str]
    required_evidence: list[str]
    parameter_codes: list[str]
    owner_terms: list[str]
    positive_policy: str
    negative_policy: str
    abstain_policy: str
    generated_from: str
    confidence: float
    priority_score: float = 0.5
    recipe_status: str = "CANDIDATE"
    critic_score: float = 0.0
    regression_score: float = 0.0
    issues: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row['issues'] = list(self.issues or [])
        return row


def _rid(domain: str, source_id: str, title: str) -> str:
    base=f"{domain}|{source_id}|{normalize_text(title)}".encode('utf-8')
    return f"VR-{domain[:3].upper()}-{hashlib.sha1(base).hexdigest()[:10].upper()}"


def _owner_terms(text: str) -> list[str]:
    low=normalize_text(text)
    # Conservative entity phrases. These are hints only; they never establish ownership.
    patterns=(
        r'(?:для|по|у|на)\s+([а-яa-z0-9][а-яa-z0-9\- ]{3,50}?)(?:\s+(?:проверить|предусмотреть|выполнить|указать|должн)|[,.;:]|$)',
        r'(дск|компрессорн[а-я]*|котельн[а-я]*|насосн[а-я ]*станц[а-я]*|трансформаторн[а-я ]*подстанц[а-я]*|резервуар[а-я ]*|здани[а-я ]*|автодорог[а-я]*)',
    )
    out=[]
    for pattern in patterns:
        for m in re.finditer(pattern,low,re.I):
            value=' '.join((m.group(1) or '').split()).strip()
            if value and value not in out: out.append(value)
            if len(out)>=4:return out
    return out


def recipe_from_checklist(item: dict[str, Any]) -> dict[str, Any]:
    title=str(item.get('question') or '').strip()
    compiled=compile_item(item).to_dict()
    level=compiled.get('verification_level') or infer_verification_level(title)
    method=str(compiled.get('typed_check') or 'SPECIALIST_REVIEW')
    required=list(compiled.get('evidence_types') or [])
    if not required:
        required=['STRUCTURED_VALUE'] if level=='L2_VALUE' else ['STRUCTURED_COMPARISON'] if level=='L3_CROSS_CHECK' else ['ENGINEERING_EVIDENCE']
    section_roles=[str(x) for x in (compiled.get('required_section_roles') or [])]
    source_id=str(item.get('id') or f"{item.get('source_file')}:{item.get('sheet')}:{item.get('row')}")
    # Confidence is intentionally conservative. L4/L5 recipes need stronger evidence/checkers.
    base={'L1_PRESENCE':0.86,'L2_VALUE':0.82,'L3_CROSS_CHECK':0.84,'L4_COMPLETENESS':0.58,'L5_ENGINEERING_COMPLIANCE':0.48}.get(level,0.45)
    if method in {'SPECIALIST_REVIEW','ENGINEERING_SEMANTIC_REVIEW','NORMATIVE_CONTENT_REVIEW'}: base-=0.12
    if compiled.get('parameter_codes'): base+=0.05
    return VerificationRecipe(
        recipe_id=_rid('checklist',source_id,title), domain='checklist', source_id=source_id, title=title,
        verification_level=level, check_method=method, scope='SECTION_OR_OBJECT', expected_sections=section_roles,
        required_evidence=required, parameter_codes=list(compiled.get('parameter_codes') or []), owner_terms=_owner_terms(title),
        positive_policy='Положительный вывод разрешён только при доказательстве, достаточном для уровня проверки.',
        negative_policy='Отрицательный вывод разрешён только при прямом доказательстве невыполнения; отсутствие находки недостаточно.',
        abstain_policy='При неоднозначной принадлежности, неполном охвате или слабом evidence вернуть Не проверено автоматически.',
        generated_from='CHECKLIST', confidence=max(0.05,min(0.98,base)), priority_score=0.5,
    ).to_dict()


def recipe_from_assignment(requirement: dict[str, Any]) -> dict[str, Any]:
    title=str(requirement.get('requirement_text') or requirement.get('requirement') or '').strip()
    contract=requirement.get('evidence_contract_v2') or build_contract(requirement)
    rtype=str(requirement.get('requirement_type') or 'SEMANTIC_ENGINEERING')
    method=str(contract.get('check_method') or rtype)
    level='L2_VALUE' if method=='VALUE_COMPARISON' else 'L3_CROSS_CHECK' if method in {'SET_COMPARISON','TRACE_CHAIN'} else 'L1_PRESENCE' if method in {'CALCULATION_PRESENCE','DRAWING_EVIDENCE'} else 'L5_ENGINEERING_COMPLIANCE'
    source_id=str(requirement.get('requirement_id') or requirement.get('source_row') or title[:40])
    conf=0.88 if method in {'VALUE_COMPARISON','SET_COMPARISON','CALCULATION_PRESENCE'} else 0.68 if method in {'TRACE_CHAIN','DRAWING_EVIDENCE'} else 0.52
    return VerificationRecipe(
        recipe_id=_rid('assignment',source_id,title), domain='assignment', source_id=source_id, title=title,
        verification_level=level, check_method=method, scope=str(contract.get('scope') or 'UNRESOLVED'),
        expected_sections=list(contract.get('expected_sections') or []), required_evidence=list(contract.get('required_evidence') or []),
        parameter_codes=[str(requirement.get('parameter_code'))] if requirement.get('parameter_code') else [], owner_terms=_owner_terms(title),
        positive_policy='Требование считается выполненным только при подтверждении контракта доказательства.',
        negative_policy='Несоответствие допускается только при сопоставимом evidence или прямом противоречии.',
        abstain_policy='NOT_FOUND и неоднозначный semantic match приводят к воздержанию.', generated_from='ASSIGNMENT', confidence=conf,
        priority_score=0.8,
    ).to_dict()


def recipe_from_practice(rule: dict[str, Any]) -> dict[str, Any]:
    title=(rule.get('example_texts') or ['Практика экспертизы'])[0]
    strategy=str(rule.get('check_strategy') or 'SEMANTIC').upper()
    method={
        'PRESENCE_AND_COMPLETENESS':'COMPLETENESS_REVIEW','CROSS_SECTION_CONSISTENCY':'STRUCTURED_COMPARISON',
        'CALCULATION_AND_INPUTS':'CALCULATION_REVIEW','NORMATIVE_COMPLIANCE':'NORMATIVE_LINK',
        'VALUE_COMPARISON':'VALUE_COMPARISON',
    }.get(strategy,strategy)
    level='L4_COMPLETENESS' if 'COMPLETENESS' in method else 'L3_CROSS_CHECK' if 'COMPARISON' in method else 'L5_ENGINEERING_COMPLIANCE'
    source_id=str(rule.get('rule_id') or 'practice')
    projects=int(rule.get('project_count') or 0); remarks=int(rule.get('remark_count') or 0)
    priority=min(1.0,0.35+0.04*projects+0.002*remarks)
    return VerificationRecipe(
        recipe_id=_rid('practice',source_id,title),domain='practice',source_id=source_id,title=str(title),
        verification_level=level,check_method=method,scope=str(rule.get('section_family') or 'PROJECT'),
        expected_sections=[str(rule.get('section_family'))] if rule.get('section_family') else [],
        required_evidence=['PROJECT_EVIDENCE','EXPERT_PRACTICE_ANALOG'],parameter_codes=[str(rule.get('target_code'))] if rule.get('target_code') not in {None,'GENERAL'} else [],
        owner_terms=[],positive_policy='Правило практики не может самостоятельно подтвердить соответствие проекта.',
        negative_policy='Замечание формируется только при проектном evidence; исторический аналог лишь повышает приоритет.',
        abstain_policy='При отсутствии проектного evidence — только рекомендация проверки.',generated_from='EXPERT_PRACTICE',confidence=0.55,priority_score=priority,
    ).to_dict()


def recipe_from_normative(row: dict[str, Any]) -> dict[str, Any]:
    title=str(row.get('requirement') or '').strip()
    source_id=str(row.get('id') or row.get('requirement_id') or title[:30])
    verified=str(row.get('verification_status') or '').upper() in {'VERIFIED','VERIFIED_CLAUSE','КУРАТОРСКИ ВЕРИФИЦИРОВАНО'} or bool(row.get('verified_clause'))
    contract=row.get('evidence_contract') or {}
    conf=0.88 if verified else 0.34
    return VerificationRecipe(
        recipe_id=_rid('normative',source_id,title),domain='normative',source_id=source_id,title=title,
        verification_level='L5_ENGINEERING_COMPLIANCE',check_method=str(row.get('check_kind') or 'NORMATIVE_REVIEW'),
        scope=str(row.get('topic') or 'PROJECT'),expected_sections=list(row.get('sections') or []),
        required_evidence=['VERIFIED_CLAUSE','PROJECT_EVIDENCE'],parameter_codes=[],owner_terms=_owner_terms(title),
        positive_policy='Категоричный нормативный вывод разрешён только для верифицированного пункта и проектного evidence.',
        negative_policy='Неверифицированный пункт не создаёт риск проекта.',abstain_policy='При отсутствии верифицированного пункта — пробел нормативного покрытия.',
        generated_from='NORMATIVE_KB',confidence=conf,priority_score=0.85 if verified else 0.45,
    ).to_dict()


def generate_recipe_candidates(root: str | Path, assignment_rows: Iterable[dict[str,Any]] | None = None) -> list[dict[str,Any]]:
    root=Path(root); rows=[]
    def load(name,default):
        try:return json.loads((root/name).read_text(encoding='utf-8'))
        except Exception:return default
    for item in load('checklist_catalog.json',[]):
        if not item.get('is_heading'): rows.append(recipe_from_checklist(item))
    for rule in load('expert_practice_rules_v1.json',[]): rows.append(recipe_from_practice(rule))
    for norm in load('normative_requirements_v3.json',[]): rows.append(recipe_from_normative(norm))
    for req in assignment_rows or []: rows.append(recipe_from_assignment(req))
    return rows
