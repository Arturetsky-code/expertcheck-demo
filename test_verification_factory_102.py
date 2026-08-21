from pathlib import Path
from core.verification_recipe_factory import recipe_from_checklist, recipe_from_assignment
from core.verification_recipe_critic import critique_recipe
from core.verification_regression_gate import regression_gate, synthetic_cases
from core.verification_factory import build_factory_catalog
from core.verification_feedback import labeled_case, feedback_summary
from core.verification_recipe_ai import consensus_decision

ROOT=Path(__file__).parent/'knowledge'


def test_presence_recipe_can_be_trusted_after_gates():
    r=recipe_from_checklist({'id':'X1','question':'Проверить наличие принципиальной схемы водоснабжения','document_types':['ИОС2']})
    r.update(critique_recipe(r)); r.update(regression_gate(r))
    assert r['verification_level']=='L1_PRESENCE'
    assert r['recipe_status']=='TRUSTED'


def test_complex_engineering_recipe_is_not_auto_trusted_without_strong_checker():
    r=recipe_from_checklist({'id':'X2','question':'Проверить обеспеченность противопожарными проездами ко всем зданиям','document_types':['ПЗУ']})
    r.update(critique_recipe(r)); r.update(regression_gate(r))
    assert r['verification_level'] in {'L4_COMPLETENESS','L5_ENGINEERING_COMPLIANCE'}
    assert r['recipe_status']=='EXPERIMENTAL'


def test_assignment_value_recipe_has_abstention_cases():
    r=recipe_from_assignment({'requirement_id':'A1','requirement_text':'Продолжительность смены 12 часов','requirement_type':'VALUE_COMPARISON','parameter_code':'SHIFT_DURATION','source_row_title':'Режим работы'})
    cases=synthetic_cases(r)
    assert any(x['case']=='wrong_owner' and x['expected']=='ABSTAIN' for x in cases)
    assert any(x['case']=='same_number_incompatible_unit' and x['expected']=='ABSTAIN' for x in cases)


def test_factory_builds_many_candidates_without_specialist_labeling():
    f=build_factory_catalog(ROOT)
    assert f['total']>500
    assert f['trusted_count']>20
    assert f['experimental_count']>f['trusted_count']


def test_specialist_feedback_is_optional_labeled_case():
    a=labeled_case(domain='checklist',check_id='1',automated_result='Соответствует',specialist_result='Не соответствует')
    s=feedback_summary([a])
    assert s['labeled_cases']==1 and s['disagreement_count']==1


def test_ai_consensus_is_conservative_on_disagreement():
    c=consensus_decision([{'safe':True,'score':0.9},{'safe':False,'score':0.8}])
    assert c['consensus']=='DISAGREE' and c['safe'] is False
