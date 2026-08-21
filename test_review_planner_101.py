from core.project_review_planner import build_review_plan
from core.verification_core import classify_verification, verification_label


def test_review_plan_three_domains_and_conservative_coverage():
    plan=build_review_plan(
        assignment_rows=[{'requirement_id':'A1','requirement_text':'Смена 12 часов','status':'Соответствует заданию','evidence':['ТХ, стр. 3']},
                         {'requirement_id':'A2','requirement_text':'Предусмотреть X','status':'Не проверено системой'}],
        normative_rows=[{'requirement_id':'N1','source':'СП X','paragraph':'5.1','requirement':'X','status':'Не покрыто нормативной базой','coverage_state':'KB_GAP'}],
        checklist_review={'results':[{'item_no':'1','question':'Проверить площадь','status':'Да','proof_kind':'STRUCTURED_VALUE'},
                                     {'item_no':'2','question':'Проверить решение','status':'Требует проверки','proof_kind':'CANDIDATE_EVIDENCE','evidence':'найден фрагмент'}]},
    )
    assert plan['domains']['assignment']['total']==2
    assert plan['domains']['assignment']['completed']==1
    assert plan['domains']['normative']['system_limitations']==1
    assert plan['domains']['checklist']['verified_ok']==1
    assert plan['domains']['checklist']['system_limitations']==1


def test_unverified_normative_is_not_project_finding():
    q=classify_verification({'status':'Не покрыто нормативной базой','coverage_state':'KB_GAP','decision_basis':'нет пункта'},'normative')
    assert q['verification_kind']=='SYSTEM_LIMITATION'
    assert verification_label('SYSTEM_LIMITATION')=='Не проверено автоматически'
