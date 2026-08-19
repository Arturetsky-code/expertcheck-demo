from core.finding_qualification import qualify_comparison, qualify_checklist
from core.object_scope_guard import assess_scope_binding, position_relation
from core.property_intelligence import infer_value_scope
from core.project_understanding import build_project_object_model
from core.expert_review_engine import build_expert_risks
from core.drawing_intelligence import classify_drawing_context


def test_parent_child_position_relationship():
    assert position_relation('4.16.1','4.16') == 'child'
    assert position_relation('4.16','4.16.1') == 'parent'
    assert position_relation('4.16.1','4.16.2') == 'siblings'


def test_position_cannot_override_contradictory_object_name():
    finding={'object_hint':'Электрощитовая','genplan_position':'4.16.1','context':'Электрощитовая площадь 71,2'}
    result=assess_scope_binding(finding,'Эстакада кабельная','4.16.1')
    assert result['scope_binding_decision'] == 'HOLD'


def test_project_understanding_blocks_parent_child_leakage():
    registry=[
        {'Наименование объекта':'Электрощитовая','Позиция по ГП':'4.16'},
        {'Наименование объекта':'Эстакада кабельная','Позиция по ГП':'4.16.1'},
    ]
    findings=[{
        'object_hint':'Электрощитовая','genplan_position':'4.16.1','parameter_code':'AREA_TOTAL',
        'parameter_name':'Общая площадь','value':71.2,'unit':'м2','document':'ПЗ','document_type':'ПЗ',
        'page':45,'confidence':.99,'binding_status':'POSITION_LOCKED','row_integrity_status':'CONFIRMED_ROW'
    }]
    model=build_project_object_model(registry,findings)
    child=next(x for x in model['objects'] if x['position']=='4.16.1')
    assert child['property_count'] == 0
    assert findings[0]['project_understanding_binding'] == 'Требует проверки границ объекта'


def test_room_explication_area_not_directly_comparable_to_total_area():
    room={'parameter_name':'Площадь помещений. Экспликация помещений. Итого помещений','context':'Экспликация помещений','value':87.1}
    total={'parameter_name':'Общая площадь здания','context':'Технико-экономические показатели. Общая площадь здания','value':71.2}
    assert infer_value_scope(room,'AREA_TOTAL') == 'room_area_sum'
    assert infer_value_scope(total,'AREA_TOTAL') == 'building_total_area'


def test_site_area_not_building_footprint():
    assert infer_value_scope({'parameter_name':'Площадь территории площадки'},'AREA_BUILD') == 'site_area'
    assert infer_value_scope({'parameter_name':'Площадь застройки'},'AREA_BUILD') == 'building_footprint'


def test_insufficient_data_is_not_risk():
    row={'status':'НЕДОСТАТОЧНО ДАННЫХ','object':'КПП','parameter_name':'Общая площадь','sources':'ПЗ, стр. 45'}
    q=qualify_comparison(row)
    assert q['risk_eligible'] is False
    assert q['user_status']=='Недостаточно данных'
    assert build_expert_risks([row]) == []


def test_checklist_not_verified_by_system_is_not_risk():
    row={'status':'Требует проверки','question':'Проверить решение','evidence':'Достаточные смысловые доказательства автоматически не выявлены'}
    q=qualify_checklist(row)
    assert q['risk_eligible'] is False
    assert q['user_status']=='Не проверено системой'
    assert build_expert_risks([],checklist_results=[row]) == []


def test_confirmed_cross_section_mismatch_can_be_risk():
    row={
        'status':'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ','object':'Компрессорная','parameter_name':'Площадь застройки',
        'independent_trusted_sources':2,'independent_section_count':2,
        'sources':'ПЗ стр.45 = 54,3 | ПЗУ стр.18 = 48,7','priority':'Высокий'
    }
    q=qualify_comparison(row)
    assert q['risk_eligible'] is True
    risks=build_expert_risks([row])
    assert len(risks)==1
    assert risks[0]['finding_class']=='CONFIRMED_ISSUE'


def test_drawing_context_marks_ar_explication():
    item={'document_type':'АР','parameter_code':'AREA_TOTAL','context':'Экспликация помещений. Итого 87,1 м2'}
    result=classify_drawing_context(item)
    assert result['drawing_evidence'] is True
    assert result['drawing_kind']=='room_explication'
