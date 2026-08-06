from core.cognitive_document_intelligence import _zone, _object_findings_from_table
from core.checklist_compiler import compile_item
from core.ai_gateway import _extract_json


def test_service_zone_is_blocked():
    zone, confidence, _ = _zone('Состав проектной документации. Наименование документа')
    assert zone == 'DOCUMENT_SERVICE'
    assert confidence >= 95


def test_table_row_binds_object_and_property():
    matrix=[['Позиция по генплану','Наименование объекта','Площадь застройки, м²'],['4.13','Здание проборазделки','89,9 м²']]
    findings,_=_object_findings_from_table(matrix,'ПЗ.pdf','ПЗ',45,'OFFICIAL_OBJECT_REGISTER')
    objects=[x for x in findings if x['parameter_code']=='OBJECT_ENTRY']
    props=[x for x in findings if x['parameter_code']=='AREA_BUILD']
    assert objects[0]['object_hint']=='Здание проборазделки'
    assert props[0]['value']==89.9
    assert props[0]['object_hint']=='Здание проборазделки'
    assert props[0]['binding_status']=='ROW_LOCKED'


def test_checklist_compiler_numeric_rule():
    rule=compile_item({'question':'Сверить площадь застройки между ПЗ и ПЗУ'})
    assert rule.rule_type=='numeric_crosscheck'
    assert 'AREA_BUILD' in rule.parameter_codes


def test_ai_json_extraction_from_fence():
    data=_extract_json('```json\n{"result":"yes","confidence":0.9}\n```')
    assert data['result']=='yes'
