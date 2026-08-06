from core.report_engine import build_structured_report


def test_compact_report_excludes_ok_rows_from_problems():
    report = build_structured_report('Test', [{'consolidated_registry': [{'name':'A'}]}], [
        {'object':'A','parameter_name':'Площадь','status':'Совпадает'},
        {'object':'A','parameter_name':'Высота','status':'Потенциальное расхождение'},
    ])
    assert len(report['problems']) == 1
    assert report['problems'][0]['parameter'] == 'Высота'


def test_checklist_summary_and_risks_are_included():
    report = build_structured_report('Test', [], [], risks=[{'level':'Высокий'}], checklist_results=[
        {'status':'Да'}, {'status':'Нет'}, {'status':'Требует проверки'},
    ])
    assert report['summary']['risks_high'] == 1
    assert report['summary']['checklist_total'] == 3
    assert report['summary']['checklist_no'] == 1
