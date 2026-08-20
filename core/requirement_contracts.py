from __future__ import annotations
from typing import Any
from .normalization import normalize_text
from .object_semantics import canonical_parameter_code

SCOPE_PROJECT='PROJECT_GLOBAL'
SCOPE_SITE='SITE_SPECIFIC'
SCOPE_OBJECT='OBJECT_SPECIFIC'
SCOPE_SYSTEM='SYSTEM_SPECIFIC'
SCOPE_EQUIPMENT='EQUIPMENT_SPECIFIC'
SCOPE_DOCUMENT='DOCUMENT_SPECIFIC'
SCOPE_UNRESOLVED='UNRESOLVED'

PARAM_SECTION_HINTS={
 'SHIFT_DURATION':['ТХ','ПЗ'],
 'CAPACITY':['ТХ','ПЗ'],
 'AREA_BUILD':['ПЗУ','АР','ПЗ'],
 'AREA_TOTAL':['АР','ПЗ'],
 'POWER_INSTALLED':['ИОС1','ТХ','ПЗ'],
 'FLOW_RATE':['ИОС2','ТХ','ПЗ'],
 'VOLUME':['ИОС2','ТХ','ПЗ'],
 'BODY_VOLUME':['ТХ'],
 'BUCKET_VOLUME':['ТХ'],
 'LENGTH':['ПЗУ','ТХ','ИОС'],
 'HEIGHT_BUILD':['АР','ПЗ'],
 'QUANTITY':['ПЗ','ПЗУ','ТХ'],
}

def infer_scope(requirement:dict[str,Any])->str:
    text=normalize_text(requirement.get('requirement_text') or '')
    title=normalize_text(requirement.get('source_row_title') or '')
    obj=normalize_text(requirement.get('object_name') or '')
    code=canonical_parameter_code(requirement.get('parameter_code'))
    if obj:
        if any(x in text for x in ('автосамосвал','погрузчик','оборудован','агрегат','насос','трансформатор')):
            return SCOPE_EQUIPMENT
        return SCOPE_OBJECT
    if code in {'BODY_VOLUME','BUCKET_VOLUME'}:
        return SCOPE_EQUIPMENT
    if code=='SHIFT_DURATION' or any(x in title for x in ('режим работы','основным технико-экономическим показател')):
        return SCOPE_PROJECT
    if any(x in title for x in ('схеме планировочной','земельного участка','генеральн')):
        return SCOPE_SITE
    if any(x in title for x in ('водоснабжен','канализац','электроснабжен','отоплен','вентиляц','связ')):
        return SCOPE_SYSTEM
    if any(x in title for x in ('состав проектной документации','графическим материал')):
        return SCOPE_DOCUMENT
    return SCOPE_UNRESOLVED

def build_contract(requirement:dict[str,Any])->dict[str,Any]:
    rtype=str(requirement.get('requirement_type') or 'SEMANTIC_ENGINEERING')
    code=canonical_parameter_code(requirement.get('parameter_code'))
    scope=infer_scope(requirement)
    sections=list(PARAM_SECTION_HINTS.get(code,[]))
    if rtype=='SET_COMPARISON':
        method='SET_COMPARISON'; evidence=['Реестр объектов проекта','Приложение/перечень объектов Задания']
    elif rtype=='VALUE_COMPARISON':
        method='VALUE_COMPARISON'; evidence=['Структурированный инженерный факт с тем же показателем и областью действия']
    elif rtype=='CROSS_DOCUMENT_TRACE':
        method='TRACE_CHAIN'; evidence=['Исходный документ/изыскания','Проектное решение, использующее исходное значение']
    elif rtype=='CALCULATION_PRESENCE':
        method='CALCULATION_PRESENCE'; evidence=['Идентифицируемый расчёт','Исходные данные','Результат расчёта']
    elif rtype=='DRAWING_REQUIREMENT':
        method='DRAWING_EVIDENCE'; evidence=['Конкретный лист/графическая зона/обозначение']
    elif rtype=='NORMATIVE_COMPLIANCE':
        method='NORMATIVE_LINK'; evidence=['Верифицированный пункт НТД','Проектное доказательство выполнения']
    elif rtype=='PROHIBITION_OR_NOT_REQUIRED':
        method='APPLICABILITY_REVIEW'; evidence=['Подтверждение области применимости/неприменимости']
    else:
        method='AI_EVIDENCE_REVIEW'; evidence=['Конкретное проектное решение с документом и страницей/листом']
    return {
      'scope':scope,
      'check_method':method,
      'expected_sections':sections,
      'required_evidence':evidence,
      'minimum_evidence_count':1,
      'negative_from_not_found_allowed':False,
      'requires_same_owner':scope in {SCOPE_OBJECT,SCOPE_EQUIPMENT},
      'requires_same_parameter':rtype=='VALUE_COMPARISON',
      'ai_allowed':method in {'AI_EVIDENCE_REVIEW','TRACE_CHAIN','NORMATIVE_LINK','DRAWING_EVIDENCE'},
      'categorical_without_evidence':False,
    }

def evidence_packet(requirement:dict[str,Any], candidates:list[dict[str,Any]])->dict[str,Any]:
    contract=requirement.get('evidence_contract_v2') or build_contract(requirement)
    return {
      'requirement_id':requirement.get('requirement_id'),
      'requirement_text':requirement.get('requirement_text'),
      'scope':contract.get('scope'),
      'check_method':contract.get('check_method'),
      'expected_sections':contract.get('expected_sections') or [],
      'required_evidence':contract.get('required_evidence') or [],
      'candidates':candidates or [],
      'policy':'Отсутствие найденного доказательства не является доказательством невыполнения требования.',
    }
