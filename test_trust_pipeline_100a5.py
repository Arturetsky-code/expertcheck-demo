from core.global_finding_gate import classify_finding
from core.report_engine import build_structured_report
from core.project_understanding import build_project_object_model


def test_gp_field_not_confirmed_is_system_limitation():
    row={'parameter_code':'GP_EXPLICATION_FIELD','status':'ТРЕБУЕТ ПРОВЕРКИ','explanation':'Позиция есть в экспликации, но независимое подтверждение на поле чертежа не получено.'}
    q=classify_finding(row)
    assert q['finding_type']=='SYSTEM_LIMITATION'
    assert q['report_eligible'] is False


def test_system_limitation_not_in_gip_actions():
    row={'parameter_code':'GP_EXPLICATION_FIELD','status':'ТРЕБУЕТ ПРОВЕРКИ','object':'КТП','parameter_name':'Экспликация ↔ поле чертежа','explanation':'Позиция есть в экспликации, но независимое подтверждение на поле чертежа не получено.'}
    r=build_structured_report('P',[{}],[row])
    assert r['problems']==[]
    assert not r['recommendations']
    assert r['summary']['system_limitations']==1


def test_ownerless_fact_cannot_gain_semantic_owner_later():
    registry=[{'Наименование объекта':'Оборудование дробильного комплекса','Позиция по ГП':'4.2.1'}]
    findings=[{
        'parameter_code':'AREA_BUILD','parameter_name':'Площадь застройки','value':43414,'unit':'м²',
        'semantic_anchor_name':'Оборудование дробильного комплекса','semantic_anchor_position':'4.2.1',
        'document':'ПЗ.pdf','document_type':'ПЗ','page':27,'context':'Площадь застройки 43414 м2',
        'fact_admission_decision':'ADMIT','confidence':0.9,
    }]
    m=build_project_object_model(registry,findings)
    obj=m['objects'][0]
    assert 'AREA_BUILD' not in obj['properties']
    assert findings[0].get('fact_lineage_decision')=='HOLD'


def test_required_confirmation_stays_review_question():
    row={'status':'НЕДОСТАТОЧНО ДАННЫХ','cross_section_required':True,'object':'A','parameter_name':'B'}
    q=classify_finding(row)
    assert q['finding_type']=='REVIEW_QUESTION'
