from core.ru_labels import ru_label
from core.report_engine import build_structured_report

def test_internal_codes_are_russian_for_user():
    assert ru_label('VERIFIED_EVIDENCE')=='Подтверждённое доказательство'
    assert ru_label('PROJECT_GLOBAL')=='Весь проект'
    assert ru_label('VALUE_COMPARISON')=='Сверка числового значения'
    assert ru_label('KB_GAP')=='Не покрыто нормативной базой ExpertCheck'

def test_insufficient_without_applicability_not_action():
    r=build_structured_report('P',[{}],[{'status':'НЕДОСТАТОЧНО ДАННЫХ','object':'Выгреб','parameter_name':'Объём'}])
    assert r['problems']==[]
    assert not any('Выгреб' in x for x in r['recommendations'])

def test_insufficient_with_required_confirmation_remains_question():
    r=build_structured_report('P',[{}],[{'status':'НЕДОСТАТОЧНО ДАННЫХ','object':'Объект','parameter_name':'Показатель','cross_section_required':True}])
    assert len(r['problems'])==1
