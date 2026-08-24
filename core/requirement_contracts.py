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

TEXT_SECTION_HINTS=(
 (('генеральн план','планировочн','внутриплощадочн','проезд','подтоплен','благоустрой','огражден','земельн участ','рельеф','водоотводн канав'),['ПЗУ']),
 (('технологическ','оборудован','производительност','дроблен','конвейер','погрузчик','самосвал','бункер'),['ТХ']),
 (('архитектурн','помещен','фасад','ограждающ конструкц'),['АР']),
 (('конструктивн','фундамент','нагрузк','армирован','металлоконструкц'),['КР']),
 (('электроснабжен','освещен','заземлен','молниезащит','напряжен'),['ИОС1']),
 (('водоснабжен','канализац','водоотведен','расход вод','напор','сточн'),['ИОС2']),
 (('видеонаблюден','волс','связ','автоматизац'),['ИОС5']),
)

CRITICAL_QUALIFIER_STEMS = (
 'самотек','самотечн','заводск','привозн','бутилирован','светодиод',
 'воздушн','изолирован','металлическ','естественн','консольн','дистанцион',
 'онлайн','аварийн','перегруз','вахтов','заказчик','мачт','ливнев',
 'внеплощадочн','выгреб','накопительн','бессточн','герметичн',
 'существующ','предприят','склад','недроблен','персонал','калит',
 'безопасн','пуск','сблокирован','блокирован',
 'прожекторн','молниеприем',
)

DRAWING_TOKENS = (
 'чертеж','чертёж','лист','план ','плане','разрез','фасад','схем',
 'узел','экспликац','маркировк','условн обозначен','графическ',
)


def infer_required_modality(requirement:dict[str,Any], rtype:str)->str:
    text=normalize_text(requirement.get('requirement_text') or '').lower()
    compiled=requirement.get('compiled_rule') or {}
    typed=str(compiled.get('typed_check') or requirement.get('typed_check') or '').upper()
    if rtype=='DRAWING_REQUIREMENT' or typed.startswith('DRAWING_') or any(token in text for token in DRAWING_TOKENS):
        return 'DRAWING'
    if rtype=='CALCULATION_PRESENCE' or 'CALCULATION' in typed or any(token in text for token in ('расчет','расчёт','рассчитать','подтвердить расчетом','обоснован расчетом')):
        return 'CALCULATION'
    if rtype in {'CROSS_DOCUMENT_TRACE','DOCUMENT_DELIVERABLE'} or typed=='DOCUMENT_CONTENT_PRESENCE':
        return 'DOCUMENT'
    return 'TEXT_OR_TABLE'


def infer_critical_qualifiers(requirement:dict[str,Any])->list[str]:
    text=normalize_text(requirement.get('requirement_text') or '').lower()
    return [stem for stem in CRITICAL_QUALIFIER_STEMS if stem in text]


def infer_expected_sections(requirement:dict[str,Any], code:str='')->list[str]:
    direct=list(PARAM_SECTION_HINTS.get(code,[]))
    if direct:
        return direct
    text=normalize_text(requirement.get('requirement_text') or '')
    result=[]
    for hints,sections in TEXT_SECTION_HINTS:
        if any(hint in text for hint in hints):
            for section in sections:
                if section not in result:result.append(section)
    return result

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
    sections=infer_expected_sections(requirement,code)
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
    modality=infer_required_modality(requirement,rtype)
    qualifiers=infer_critical_qualifiers(requirement)
    return {
      'contract_version':'2.0-evidence-contract',
      'scope':scope,
      'check_method':method,
      'logical_operator':'AND',
      'expected_sections':sections,
      'required_evidence':evidence,
      'minimum_evidence_count':1,
      'required_modality':modality,
      'critical_qualifiers':qualifiers,
      'critical_qualifier_operator':'AND',
      'same_clause_required':True,
      'minimum_semantic_coverage':1.0,
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
