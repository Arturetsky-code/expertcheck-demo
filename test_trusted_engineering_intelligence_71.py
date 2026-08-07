from core.object_gate import apply_hard_object_gate, hard_rejection_reason
from core.position_rules import normalize_genplan_position
from core.learning_engine import apply_learning_examples
from core.normative_knowledge import NormativeKnowledgeLayer
from core.remark_learning import RemarkLearningEngine
from pathlib import Path


def test_toc_entries_are_hard_blocked():
    rows=[
        {'parameter_code':'OBJECT_CANDIDATE','value_text':'1.1 Введение','object_hint':'1.1 Введение','context':'Содержание'},
        {'parameter_code':'OBJECT_ENTRY','value_text':'2.3 Основные проектные решения','object_hint':'2.3 Основные проектные решения'},
    ]
    audit=apply_hard_object_gate(rows)
    assert audit['blocked']==2
    assert all(r['object_intelligence_decision']=='blocked' for r in rows)


def test_dates_never_become_genplan_positions():
    assert normalize_genplan_position('21.05.26',allow_integer=True)==''
    row={'parameter_code':'OBJECT_CANDIDATE','value_text':'21.05.26 Введение','object_hint':'21.05.26 Введение','genplan_position':'21.05.26'}
    apply_hard_object_gate([row])
    assert row['genplan_position']==''
    assert row['object_intelligence_decision']=='blocked'


def test_real_position_and_object_survives_gate():
    row={'parameter_code':'OBJECT_ENTRY','value_text':'4.13 Здание проборазделки','object_hint':'Здание проборазделки','genplan_position':'4.13','context':'Экспликация зданий и сооружений'}
    audit=apply_hard_object_gate([row])
    assert audit['blocked']==0
    assert row['genplan_position']=='4.13'


def test_learning_requires_repeated_exclusion():
    finding={'parameter_code':'OBJECT_CANDIDATE','value_text':'Служебный блок','object_hint':'Служебный блок'}
    one=[{'kind':'object_decision','name':'Служебный блок','included':False,'reason':'Ошибочно распознанный текст'}]
    assert apply_learning_examples([dict(finding)],one)==0
    two=one+one
    row=dict(finding)
    assert apply_learning_examples([row],two)==1
    assert row['object_intelligence_decision']=='blocked'


def test_normative_layer_is_conservative():
    layer=NormativeKnowledgeLayer(Path(__file__).parent/'knowledge')
    result=layer.enrich([{'reference':'ПП РФ №87'}])[0]
    assert 'провер' in result['knowledge_status'].lower()


def test_remark_case_match_by_parameter():
    eng=RemarkLearningEngine(Path(__file__).parent/'knowledge')
    matches=eng.match(text='Расхождение количества резервуаров между разделами',parameter_code='QUANTITY')
    assert matches
    assert matches[0].get('scenario_id')
