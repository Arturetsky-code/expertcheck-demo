from __future__ import annotations
from typing import Any, Iterable
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
 'POWER_CALCULATED':['ИОС1','ТХ','ПЗ'],
 'MOISTURE':['ТХ','ПЗ'],
 'BULK_DENSITY':['ТХ','ПЗ'],
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


def coverage_archetype(requirement:dict[str,Any], recipe:dict[str,Any]|None=None)->str:
    """Return a stable coverage family for benchmark and report aggregation."""
    recipe=recipe or {}
    contract=requirement.get('evidence_contract_v2') or requirement.get('evidence_contract') or build_contract(requirement)
    method=str(recipe.get('check_method') or contract.get('check_method') or '').upper()
    modality=str(contract.get('required_modality') or recipe.get('required_modality') or 'TEXT_OR_TABLE').upper()
    kind=str(requirement.get('atomic_kind') or requirement.get('requirement_type') or '').upper()
    if modality=='DRAWING' or 'DRAWING' in method:return 'DRAWING_EVIDENCE'
    if modality=='CALCULATION' or 'CALCULATION' in method:return 'CALCULATION_EVIDENCE'
    if modality=='DOCUMENT' or kind in {'DOCUMENT_DELIVERABLE','TRACEABILITY'}:return 'DOCUMENT_TRACEABILITY'
    if 'VALUE' in method or kind=='VALUE_COMPARISON':return 'NUMERIC_VALUE'
    if 'SET' in method or kind=='SET_COMPARISON':return 'SET_COMPLETENESS'
    if kind=='EQUIPMENT_IDENTITY' or 'IDENTITY' in method:return 'IDENTITY_CLASSIFICATION'
    if kind=='NORMATIVE_CLAUSE' or 'NORMATIVE' in method or 'CLAUSE' in method:return 'NORMATIVE_REQUIREMENT'
    if kind=='PROHIBITION' or 'PROHIBITION' in method:return 'PROHIBITION'
    return 'SEMANTIC_PROJECT_DECISION'


def coverage_diagnostics(
    requirement:dict[str,Any], recipe:dict[str,Any], *,
    evidence:Iterable[dict[str,Any]]=(), candidates:Iterable[dict[str,Any]]=(),
    gate_reasons:Iterable[str]=(), final_kind:str='',
)->dict[str,Any]:
    """Explain why one evidence contract completed, stopped or needs a specialist.

    The result is deliberately operational: report users see the exact missing
    slot instead of an undifferentiated ``not checked`` status.  Diagnostics do
    not promote a verdict and therefore cannot weaken the Finding Admission Gate.
    """
    contract=requirement.get('evidence_contract_v2') or requirement.get('evidence_contract') or build_contract(requirement)
    evidence_rows=list(evidence or []); candidate_rows=list(candidates or [])
    reasons=[str(x) for x in gate_reasons or [] if str(x).strip()]
    kind=str(final_kind or '').upper()
    missing=[]; code='NEEDS_SPECIALIST_JUDGEMENT'; explanation='Требуется предметная проверка специалистом.'

    if kind=='VERIFIED_OK':
        return {
          'coverage_archetype':coverage_archetype(requirement,recipe),'coverage_state':'AUTOMATED_COMPLETE',
          'coverage_reason_code':'EVIDENCE_CONTRACT_SATISFIED','coverage_reason':'Все обязательные слоты доказательства подтверждены.',
          'missing_evidence_slots':[],'expected_evidence_route':list(contract.get('expected_sections') or []),
        }
    if kind=='PROJECT_FINDING':
        return {
          'coverage_archetype':coverage_archetype(requirement,recipe),'coverage_state':'PROJECT_FINDING_CONFIRMED',
          'coverage_reason_code':'EXPLICIT_CONTRADICTION_CONFIRMED','coverage_reason':'Зафиксировано адресное сравнение или явное противоречие.',
          'missing_evidence_slots':[],'expected_evidence_route':list(contract.get('expected_sections') or []),
        }
    if not recipe.get('executable'):
        code='RECIPE_NOT_EXECUTABLE'; explanation='Проверочный рецепт не прошёл critic/regression gate.'; missing.append('EXECUTABLE_RECIPE')
    elif not evidence_rows and not candidate_rows:
        code='NO_ADDRESSABLE_EVIDENCE'; explanation='В ожидаемых разделах не найден адресный кандидат с документом и страницей.'; missing.extend(['SOURCE_DOCUMENT','PAGE'])
    else:
        all_rows=candidate_rows or evidence_rows
        if any(str(x.get('modality_gate_state') or '').upper()=='BLOCKED' for x in all_rows):
            code='WRONG_EVIDENCE_MODALITY'; explanation='Найден связанный текст, но его модальность не соответствует контракту.'; missing.append(str(contract.get('required_modality') or 'REQUIRED_MODALITY'))
        elif any(x.get('missing_critical_qualifiers') for x in all_rows):
            code='CRITICAL_QUALIFIER_MISSING'; explanation='В адресном фрагменте отсутствует обязательный инженерный квалификатор.'; missing.extend(str(v) for x in all_rows for v in (x.get('missing_critical_qualifiers') or []))
        elif any(str(x.get('same_clause_gate_state') or '').upper()=='BLOCKED' for x in all_rows):
            code='SAME_CLAUSE_NOT_PROVED'; explanation='Слоты доказательства найдены в разных фрагментах и не образуют одного проектного решения.'; missing.append('SAME_CLAUSE_EVIDENCE')
        elif any(x.get('owner_match') is False or str(x.get('binding_status') or '').upper() in {'HOLD','UNRESOLVED'} for x in all_rows):
            code='ENTITY_BINDING_UNRESOLVED'; explanation='Не подтверждено, к какому объекту относится найденное значение или решение.'; missing.append('ENTITY_BINDING')
        elif any(x.get('unit_compatible') is False for x in all_rows if x.get('unit_compatible') is not None):
            code='UNIT_INCOMPATIBLE'; explanation='Единицы найденного значения нельзя безопасно сопоставить с требованием.'; missing.append('COMPATIBLE_UNIT')
        elif any(str(x.get('contract_state') or '').upper()=='UNSATISFIED' for x in all_rows):
            code='EVIDENCE_CONTRACT_UNSATISFIED'; explanation='Кандидаты найдены, но не заполнены все обязательные слоты доказательства.'; missing.extend(str(x) for x in recipe.get('required_evidence_slots') or [])
        elif reasons:
            code='ADVERSARIAL_OR_SEMANTIC_GATE_BLOCKED'; explanation='Категоричный вывод удержан независимой проверкой достаточности.'; missing.append('INDEPENDENT_SEMANTIC_CONFIRMATION')
    state='TARGETED_REVIEW' if kind=='REVIEW_QUESTION' and bool(candidate_rows or evidence_rows) else 'AUTOMATION_GAP'
    return {
      'coverage_archetype':coverage_archetype(requirement,recipe),'coverage_state':state,
      'coverage_reason_code':code,'coverage_reason':explanation,
      'missing_evidence_slots':list(dict.fromkeys(x for x in missing if x)),
      'expected_evidence_route':list(contract.get('expected_sections') or recipe.get('expected_sections') or []),
    }
