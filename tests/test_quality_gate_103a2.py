from legacy_analyzer import _extract_pzu_building_areas

from core.assignment_compliance import compare_requirements
from core.cross_section_consistency import build_cross_section_checks
from core.deep_evidence_intelligence import run_deep_evidence_review
from core.directed_evidence import directed_evidence_facts
from core.evidence_provenance import annotate_evidence_provenance
from core.fact_admission import assess_fact_admission
from core.general_plan_engine import _is_plausible_name, is_service_role_label
from core.project_review_planner import build_review_plan
from core.report_quality_gate import validate_review_plan
from core.table_row_integrity import apply_table_row_integrity_guard
from studio.data import _evidence_sources


def _trusted_area(document, document_type, value):
    return {
        'document':document,'document_type':document_type,'page':18,
        'parameter_code':'AREA_BUILD','parameter_name':'Площадь застройки',
        'value':value,'value_text':f'{value} м²','unit':'м²',
        'context':f'Компрессорная станция — {value} м²','confidence':.97,
        'core2_confidence':.97,'object_hint':'Компрессорная станция',
        'match_method':'строка таблицы ТЭП','binding_status':'ROW_LOCKED',
        'table_index':'ТЭП','row_index':7,'row_text':f'Компрессорная станция {value} м²',
    }


def test_title_block_roles_are_not_general_plan_objects():
    for value in ('Нач. отд. Суходольский','Пров. Бурда','Разраб. Иванов','ГИП Петров'):
        assert is_service_role_label(value)
        assert not _is_plausible_name(value)
    assert _is_plausible_name('Пункт обогрева')
    assert _is_plausible_name('Компрессорная')


def test_pzu_tep_row_has_physical_trace_and_is_admitted():
    text='''Технико-экономические показатели земельного участка
Площадь застройки, всего « 100,0
Компрессорная станция « 48,7
'''
    rows=_extract_pzu_building_areas(
        18,text,'ПЗУ1.pdf',
        [{'code':'AREA_BUILD','name':'Площадь застройки'}],
        [{'canonical':'Компрессорная станция','aliases':['Компрессорная станция']}],
    )
    assert len(rows)==1
    finding=rows[0].to_dict(); finding['core2_confidence']=.97
    assert finding['binding_status']=='ROW_LOCKED'
    assert finding['table_index'] and finding['row_index'] and finding['row_text']
    apply_table_row_integrity_guard([finding])
    annotate_evidence_provenance([finding])
    finding.update(assess_fact_admission(finding))
    assert finding['physical_trace_level'] in {'ROW_TRACE','CELL_TRACE'}
    assert finding['evidence_quality_decision']=='VERIFIED'
    assert finding['fact_admission_decision']=='ADMIT'


def test_two_trusted_tep_rows_reveal_area_discrepancy():
    findings=[_trusted_area('ПЗ.pdf','ПЗ',54.3),_trusted_area('ПЗУ1.pdf','ПЗУ1',48.7)]
    apply_table_row_integrity_guard(findings)
    annotate_evidence_provenance(findings)
    for finding in findings:
        finding.update(assess_fact_admission(finding))
    rows=build_cross_section_checks(findings)
    assert len(rows)==1
    assert rows[0]['status']=='ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ'
    assert rows[0]['difference']>5


def test_directed_exact_value_survives_deep_evidence_gate():
    row={
        'requirement_id':'REQ-SHIFT','requirement_text':'Продолжительность смены 12 ч',
        'requirement_type':'VALUE','requirement_scope':'PROJECT_GLOBAL',
        'evidence_contract_v2':{'scope':'PROJECT_GLOBAL','expected_sections':['ТХ']},
        'parameter_code':'SHIFT_DURATION','required_value':12,'unit':'ч',
        'status':'Соответствует заданию','evidence':['ТХ1.pdf, стр. 33: продолжительность смены 12 ч'],
        'evidence_quality_state':'VERIFIED_EVIDENCE',
        'directed_evidence_candidates':[{
            'evidence_state':'verified_candidate','parameter_code':'SHIFT_DURATION',
            'value':12,'unit':'ч','document':'ТХ1.pdf','page':33,
            'context':'Режим работы — две смены, продолжительность смены 12 часов.',
        }],
    }
    facts=directed_evidence_facts([row])
    assert len(facts)==1 and facts[0]['directed_evidence'] is True
    plan=build_review_plan(assignment_rows=[row],normative_rows=[],checklist_review={'results':[]})
    review=run_deep_evidence_review(plan['items'],facts=facts)
    assert review['results'][0]['adversarial_state']=='PASSED'


def test_semantic_review_gets_an_actionable_recommendation():
    rows=compare_requirements([{
        'requirement_id':'REQ-SEM','requirement_text':'Предусмотреть аварийное освещение здания',
        'requirement_type':'SEMANTIC','object_name':'Здание',
    }],[{
        'document':'ИОС1.pdf','page':4,'context':'Аварийное освещение здания предусматривается проектом.',
        'object_hint':'Здание','parameter_name':'Освещение','value_text':'аварийное освещение',
    }],[])
    assert rows[0]['status']=='Требуется смысловая проверка'
    assert 'Проверить требование' in rows[0]['recommendation']


def test_report_gate_rejects_semantic_no_action_and_service_object():
    plan=build_review_plan(
        assignment_rows=[{
            'requirement_id':'REQ-BAD','requirement_text':'Смысловая проверка',
            'status':'Требуется смысловая проверка','evidence':'кандидат',
            'evidence_quality_state':'CANDIDATE_EVIDENCE',
            'recommendation':'Дополнительное действие не требуется.',
        }],normative_rows=[],checklist_review={'results':[]},
    )
    result=validate_review_plan(plan,object_registry=[{'Наименование объекта':'Нач. отд. Суходольский'}])
    assert result['status']=='FAILED'
    assert any('не требующий действия' in issue for issue in result['issues'])
    assert any('служебная роль' in issue for issue in result['issues'])


def test_checklist_source_trace_is_visible_or_explicitly_missing():
    assert _evidence_sources({'evidence_candidates':[{'document':'АР.pdf','page':7}]})=='АР.pdf, стр. 7'
    assert _evidence_sources({}).startswith('Источник не сформирован')
