from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable

from .normalization import normalize_text
from .page_evidence_store import canonical_section, is_assignment_source


ENGINE_VERSION = "1.0-addressable-classification-consistency"

_ROMAN = {"I": "I", "II": "II", "III": "III", "IV": "IV", "1": "I", "2": "II", "3": "III", "4": "IV"}
_RULES = (
    {
        "code": "DANGER_CLASS",
        "name": "Класс опасности ОПО",
        "regex": re.compile(
            r"(?:класс\s+опасности(?:\s+опасного\s+производственного\s+объекта)?"
            r"\s*[:=\-–—]?\s*(?P<value_after>III|IV|II|I|[1-4])\b|"
            r"опасн\w*\s+производственн\w*\s+объект\w*[^.;\n]{0,100}?"
            r"(?:относ\w*\s+к\s+)?(?P<value_before>III|IV|II|I|[1-4])\s+класс\w*\s+опасност\w*)", re.I,
        ),
        "project_owner": "Опасный производственный объект",
    },
    {
        "code": "RELIABILITY_CATEGORY",
        "name": "Категория надёжности электроснабжения",
        "regex": re.compile(
            r"категори[яи]\s+над[её]жности(?:\s+электроснабжения)?[^.;\n]{0,55}?"
            r"(?P<value>III|II|I|[1-3])\b", re.I,
        ),
        "project_owner": "",
    },
    {
        "code": "FIRE_RESISTANCE",
        "name": "Степень огнестойкости",
        "regex": re.compile(r"степен[ьи]\s+огнестойкости[^.;\n]{0,45}?(?P<value>IV|III|II|I|V|[1-5])\b", re.I),
        "project_owner": "",
    },
    {
        "code": "FIRE_CATEGORY",
        "name": "Категория по взрывопожарной и пожарной опасности",
        "regex": re.compile(
            r"категори[яи](?:\s+помещени[яй]|\s+здани[яй])?\s+(?:по\s+)?(?:взрывопожарн\w*\s+и\s+пожарн\w*\s+опасност[ьи])"
            r"[^.;\n]{0,45}?(?P<value>А|Б|В[1-4]?|Г|Д)\b", re.I,
        ),
        "project_owner": "",
    },
)


def _registry_entities(registry:Iterable[dict[str,Any]])->list[dict[str,str]]:
    result=[]
    for row in registry or []:
        name=str(row.get('Наименование объекта') or row.get('Наименование') or row.get('name') or '').strip()
        if not name:continue
        result.append({
            'name':name,'normalized':normalize_text(name),
            'position':str(row.get('Позиция по ГП') or row.get('Позиция') or row.get('position') or '').strip(),
        })
    return result


def _owner(window:str, entities:list[dict[str,str]], project_owner:str)->tuple[str,str,str]:
    low=normalize_text(window)
    matches=[entity for entity in entities if len(entity['normalized'])>=5 and entity['normalized'] in low]
    unique={entity['name']:entity for entity in matches}
    if len(unique)==1:
        entity=next(iter(unique.values()))
        return entity['name'],entity['position'],'EXACT_OBJECT'
    if project_owner and len(unique)==0:
        return project_owner,'','PROJECT_SCOPE'
    return '','','UNRESOLVED' if not unique else 'AMBIGUOUS'


def _value(rule:dict[str,Any], raw:str)->str:
    token=str(raw or '').upper().replace(' ', '')
    if rule['code'] in {'DANGER_CLASS','RELIABILITY_CATEGORY','FIRE_RESISTANCE'}:
        return _ROMAN.get(token,token)
    return token.replace('B','В')


def extract_categorical_facts(
    page_corpus:Iterable[dict[str,Any]], registry:Iterable[dict[str,Any]],
)->list[dict[str,Any]]:
    entities=_registry_entities(registry); facts=[];seen=set()
    for page in page_corpus or []:
        if is_assignment_source(page):continue
        text=str(page.get('text') or '')
        if not text:continue
        section=canonical_section(page.get('document_type') or page.get('section') or page.get('document'))
        for rule in _RULES:
            for match in rule['regex'].finditer(text):
                start=max(0,match.start()-360);end=min(len(text),match.end()+360)
                window=re.sub(r'\s+',' ',text[start:end]).strip()
                owner,position,binding=_owner(window,entities,str(rule.get('project_owner') or ''))
                if not owner:continue
                raw_value=next((value for key,value in match.groupdict().items() if key.startswith('value') and value), '')
                value=_value(rule,raw_value)
                key=(rule['code'],owner,value,str(page.get('document') or ''),str(page.get('page') or ''))
                if key in seen:continue
                seen.add(key)
                facts.append({
                    'parameter_code':rule['code'],'parameter_name':rule['name'],'value':value,
                    'object':owner,'object_name':owner,'genplan_position':position,'binding_status':binding,
                    'document':page.get('document'),'page':page.get('page'),'section':section,
                    'context':window[:1200],'source_trace':window[:1200],
                    'physical_trace_level':'ROW_TRACE','evidence_quality_decision':'VERIFIED',
                    'fact_admission_decision':'ADMIT','source_kind':'PAGE_CLASSIFICATION',
                    'engine_version':ENGINE_VERSION,
                })
    return facts


def build_categorical_consistency_checks(
    page_corpus:Iterable[dict[str,Any]], registry:Iterable[dict[str,Any]],
)->list[dict[str,Any]]:
    facts=extract_categorical_facts(page_corpus,registry)
    groups=defaultdict(list)
    for fact in facts:
        groups[(fact['parameter_code'],normalize_text(fact['object']))].append(fact)
    rows=[]
    for (code,_owner_key),items in groups.items():
        values=sorted({str(item['value']) for item in items})
        documents={str(item.get('document') or '') for item in items if item.get('document')}
        sections={str(item.get('section') or '') for item in items if item.get('section')}
        if len(values)>1 and len(documents)>=2 and len(sections)>=2:
            status='ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ';finding_type='PROJECT_FINDING';user_status='Выявлено несоответствие'
        elif len(values)>1:
            status='ТРЕБУЕТ ПРОВЕРКИ';finding_type='REVIEW_QUESTION';user_status='Требует проверки'
        elif len(documents)>=2:
            status='СОВПАДАЕТ';finding_type='PROJECT_STATUS';user_status='Проверено'
        else:
            status='НЕДОСТАТОЧНО ДАННЫХ';finding_type='SYSTEM_LIMITATION';user_status='Ограничение автоматической проверки'
        first=items[0]
        sources=' | '.join(
            f"{item.get('section')} — {item.get('document')}, стр. {item.get('page')}: {item.get('parameter_name')} = {item.get('value')}"
            for item in items[:12]
        )
        values_by_doc=' | '.join(f"{item.get('section')}: {item.get('value')}" for item in items[:12])
        rows.append({
            'check_code':f"CORE-CAT-{code}-{len(rows)+1:03d}",'object':first['object'],
            'genplan_position':first.get('genplan_position') or '','parameter_code':code,
            'parameter_name':first['parameter_name'],'rule_name':'Согласованность классификационных признаков',
            'category':'Классификационная согласованность','check_type':'Адресная категориальная сверка',
            'status':status,'finding_type':finding_type,'user_status':user_status,
            'report_eligible':finding_type in {'PROJECT_FINDING','REVIEW_QUESTION'},
            'action_eligible':finding_type in {'PROJECT_FINDING','REVIEW_QUESTION'},
            'risk_eligible':finding_type=='PROJECT_FINDING','explicit_contradiction':len(values)>1,
            'independent_trusted_sources':len(documents),'independent_section_count':len(sections),
            'evidence_count':len(items),'document_values':values_by_doc,'sources':sources,
            'difference':{'values':values} if len(values)>1 else {},
            'explanation':(
                f"Найдены разные адресные значения классификационного признака: {', '.join(values)}."
                if len(values)>1 else
                f"Значение {values[0]} подтверждено в {len(documents)} документ(ах)."
            ),
            'recommendation':(
                'Проверить область действия каждого значения и синхронизировать классификацию в связанных разделах.'
                if len(values)>1 else 'Дополнительное действие не требуется.'
            ),
            'coverage_archetype':'IDENTITY_CLASSIFICATION',
            'coverage_state':'PROJECT_FINDING_CONFIRMED' if finding_type=='PROJECT_FINDING' else ('AUTOMATED_COMPLETE' if finding_type=='PROJECT_STATUS' else 'TARGETED_REVIEW' if finding_type=='REVIEW_QUESTION' else 'AUTOMATION_GAP'),
            'coverage_reason_code':'EXPLICIT_CLASSIFICATION_CONFLICT' if len(values)>1 else ('EVIDENCE_CONTRACT_SATISFIED' if len(documents)>=2 else 'SECOND_SOURCE_NOT_FOUND'),
            'engine_version':ENGINE_VERSION,
        })
    order={'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ':0,'ТРЕБУЕТ ПРОВЕРКИ':1,'НЕДОСТАТОЧНО ДАННЫХ':2,'СОВПАДАЕТ':3}
    return sorted(rows,key=lambda row:(order.get(row['status'],9),row['object'],row['parameter_name']))
