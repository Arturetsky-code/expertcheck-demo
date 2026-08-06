from core.expert_review_engine import build_expert_risks, summarize_risks


def test_mismatch_creates_risk():
    risks = build_expert_risks([{
        'status': 'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ',
        'object': 'Здание проборазделки',
        'parameter_name': 'Площадь застройки',
        'priority': 'Высокий',
        'explanation': 'ПЗ 89,9; ПЗУ 88,0',
    }])
    assert len(risks) == 1
    assert risks[0]['level'] in {'Высокий', 'Средний'}
    assert 'Площадь застройки' in risks[0]['possible_remark']


def test_checklist_negative_creates_risk():
    risks = build_expert_risks([], checklist_results=[{
        'item_no': '3.12',
        'question': 'Проверить соответствие экспликации перечню объектов ПЗ',
        'status': 'Нет',
    }])
    assert risks[0]['category'] == 'Чек-лист раздела'
    assert summarize_risks(risks)['total'] == 1
