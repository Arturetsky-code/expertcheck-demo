from pathlib import Path
from core.project_object_recovery import recover_project_objects_from_pages
from core.object_gate import apply_hard_object_gate
from core.pp87_matrix import evaluate_pp87
from core.remark_learning import RemarkLearningEngine
from core.normative_knowledge import NormativeKnowledgeLayer


def test_recovery_from_project_scope_phrase_and_identification():
    pages=[{'document':'ПЗ.pdf','document_type':'ПЗ','page':12,'text':'Состав сложного объекта\nПроектом предусматривается строительство здания проборазделки; КТП; насосной станции.'}]
    findings,audit=recover_project_objects_from_pages(pages)
    names={x['value_text'].lower() for x in findings}
    assert any('проборазделки' in x for x in names)
    assert any('ктп' == x or 'ктп' in x for x in names)
    assert any('насос' in x for x in names)


def test_toc_and_date_do_not_survive_gate():
    rows=[
        {'parameter_code':'OBJECT_CANDIDATE','value_text':'1.1 Введение','object_hint':'1.1 Введение'},
        {'parameter_code':'OBJECT_CANDIDATE','value_text':'21.05.26 Проверка документации','object_hint':'21.05.26 Проверка документации','genplan_position':'21.05.26'},
    ]
    audit=apply_hard_object_gate(rows)
    assert audit['blocked']==2
    assert all(x.get('hard_object_gate_blocked') for x in rows)


def test_pp87_mining_appendix_detected():
    findings=[{'context':'Проект горнодобывающего предприятия. Карьер, отвалы и дробильно-сортировочный комплекс. Экспликация проектируемых сооружений.'}]
    rows=evaluate_pp87('ПЗУ',findings)
    assert any(x['item_no']=='PP87-APP-07' for x in rows)


def test_historical_remark_library_loaded_and_searchable():
    engine=RemarkLearningEngine(Path(__file__).parent/'knowledge')
    assert len(engine.raw_cases) > 1000
    matches=engine.match_raw(text='наименование и перечень проектируемых объектов не соответствуют заданию на проектирование',limit=3)
    assert matches


def test_normative_historical_index_loaded():
    layer=NormativeKnowledgeLayer(Path(__file__).parent/'knowledge')
    assert layer.summary()['historical_reference_index'] > 100
    rec=layer.lookup('Постановление Правительства РФ от 16.02.2008 № 87')
    assert rec and rec.get('status')=='Действует (проверено)'
