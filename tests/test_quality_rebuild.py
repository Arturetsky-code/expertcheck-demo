from pathlib import Path
from core.trusted_project_model import annotate_findings, filter_registry
from core.checklist_engine import ChecklistEngine


def test_file_never_enters_trusted_registry():
    findings=[{'parameter_code':'OBJECT_CANDIDATE','value_text':'Раздел ПД № 3_АР2.pdf','document':'ПЗ.pdf','document_type':'ПЗ','context':'состав проектной документации'}]
    audit=annotate_findings(findings)
    trusted,candidates=filter_registry([{'Наименование объекта':'Раздел ПД № 3_АР2.pdf','Количество источников':3}],findings)
    assert not trusted
    assert candidates
    assert audit[0]['score'] < 0


def test_existing_and_perspective_not_in_project_registry():
    findings=[
      {'parameter_code':'OBJECT_ENTRY','value_text':'Действующая подстанция','document_type':'ПЗУ2','general_plan_explication':True,'context':'Экспликация, Сущ.'},
      {'parameter_code':'OBJECT_ENTRY','value_text':'Площадка склада','document_type':'ПЗУ2','general_plan_explication':True,'context':'Экспликация, Перспект.'},
    ]
    annotate_findings(findings)
    rows=[{'Наименование объекта':'Действующая подстанция','Количество источников':2},{'Наименование объекта':'Площадка склада','Количество источников':2}]
    trusted,candidates=filter_registry(rows,findings)
    assert not trusted and len(candidates)==2


def test_project_object_with_explication_is_trusted():
    findings=[{'parameter_code':'OBJECT_ENTRY','value_text':'Насосная станция','document_type':'ПЗУ2','general_plan_explication':True,'context':'Экспликация, Проект.'}]
    annotate_findings(findings)
    trusted,candidates=filter_registry([{'Наименование объекта':'Насосная станция','Количество источников':1}],findings)
    assert len(trusted)==1 and not candidates


def test_checklist_catalog_loaded():
    path=Path(__file__).parents[1]/'knowledge'/'checklist_catalog.json'
    engine=ChecklistEngine(path)
    assert len(engine.items) >= 700
    results=engine.evaluate([{'Раздел':'ПЗУ'}],[],[])
    assert len(results)==len(engine.items)
