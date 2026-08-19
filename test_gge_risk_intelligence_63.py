from core.expert_review_engine import build_expert_risks, summarize_risks

def test_area_mismatch_matches_knowledge():
    risks=build_expert_risks([{'status':'Расхождение','object':'Здание проборазделки','parameter_name':'Площадь застройки','sources':'ПЗ; ПЗУ'}])
    assert risks and risks[0]['scenario_id']=='GGE-TEP-001'
    assert risks[0]['level']=='Высокий'

def test_knowledge_summary_does_not_promote_unsupported_checklist_negative():
    risks=build_expert_risks([],checklist_results=[{'item_no':'1.1','question':'Проверить комплектность разделов по ПП 87','status':'Нет'}])
    assert summarize_risks(risks)['total'] == 0
