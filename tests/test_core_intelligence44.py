from core.object_quality_rules import name_rejection_reasons, strong_object_name
from core.object_intelligence import build_object_decisions
from core.checklist_engine import ChecklistEngine


def test_document_title_is_rejected():
    reasons=name_rejection_reasons('Раздел ПД № 5_ТХ.pdf')
    assert reasons


def test_characteristic_is_not_object():
    ok,reasons=strong_object_name('Площадь застройки')
    assert not ok and reasons


def test_official_positioned_object_is_trusted():
    findings=[{
        'parameter_code':'OBJECT_ENTRY','value_text':'Насосная станция','genplan_position':'4.1',
        'trusted_zone':'OBJECT_REGISTER','document':'ПЗУ2.pdf','document_type':'ПЗУ2',
        'object_lifecycle_status':'Проектируемый','object_trust_score':0.98,
    }]
    d=next(iter(build_object_decisions(findings).values()))
    assert d['decision']=='trusted'


def test_narrative_object_is_not_auto_trusted():
    findings=[{
        'parameter_code':'OBJECT_CANDIDATE','value_text':'Насосная станция',
        'trusted_zone':'NARRATIVE','document':'ТХ.pdf','document_type':'ТХ',
        'object_lifecycle_status':'Проектируемый','object_trust_score':0.8,
    }]
    d=next(iter(build_object_decisions(findings).values()))
    assert d['decision']=='review'


def test_checklist_heading_detection(tmp_path):
    import json
    p=tmp_path/'catalog.json'
    p.write_text(json.dumps([
        {'source_file':'x.xlsx','sheet':'A','item_no':'1','question':'Раздел','document_types':['ПЗ']},
        {'source_file':'x.xlsx','sheet':'A','item_no':'1.1','question':'Наличие экспликации','document_types':['ПЗ']},
    ],ensure_ascii=False),encoding='utf-8')
    e=ChecklistEngine(p)
    assert e.items[0]['is_heading'] is True
    assert e.items[1]['is_heading'] is False
