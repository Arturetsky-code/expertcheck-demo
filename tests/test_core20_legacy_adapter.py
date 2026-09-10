from __future__ import annotations

from core20.legacy_adapter import Legacy18Adapter
from core20.parity import evaluate_golden_cases


def _registry():
    return [
        {'Позиция по ГП':'4.5','Наименование объекта':'Компрессорная'},
        {'Позиция по ГП':'4.12','Наименование объекта':'Модуль обеспыливания'},
        {'Позиция по ГП':'4.13','Наименование объекта':'Здание проборазделки'},
        {'Позиция по ГП':'4.2','Наименование объекта':'Технологический комплекс'},
    ]


def _assembly():
    return [
        {'Позиция по ГП':'4.5','Наименование объекта':'Компрессорная','Включить':True},
        {'Позиция по ГП':'4.12','Наименование объекта':'Модуль обеспыливания','Включить':True},
        {'Позиция по ГП':'4.13','Наименование объекта':'Здание проборазделки','Включить':True},
        {'Позиция по ГП':'4.2','Наименование объекта':'Технологический комплекс','Включить':False},
    ]


def _finding(name,position,value,document,page):
    return {
        'object_name':name,'genplan_position':position,'parameter_code':'AREA_BUILD',
        'parameter_name':'Площадь застройки','value':value,'value_text':str(value),
        'unit':'м2','document':document,'page':page,'section':document.replace('.pdf',''),
        'binding_status':'ROW_LOCKED',
    }


def _comparison(name,position,kind,status,values):
    return {
        'object':name,'genplan_position':position,'parameter_code':'AREA_BUILD',
        'parameter_name':'Площадь застройки','unit':'м2',
        'final_verification_kind':kind,'final_verification_state':status,
        'proof_kind':'STRUCTURED_CONFLICT' if kind=='PROJECT_FINDING' else 'STRUCTURED_AGREEMENT',
        'conflict_confirmed':kind=='PROJECT_FINDING','correct_value_verified':kind!='PROJECT_FINDING',
        'evidence_level':'L5',
        'verification_evidence':[
            {'document':'ПЗ.pdf','page':10,'section':'ПЗ','value':values[0],'trusted_for_mismatch':True},
            {'document':'ПЗУ.pdf','page':5,'section':'ПЗУ','value':values[-1],'trusted_for_mismatch':True},
        ],
    }


def test_legacy_adapter_preserves_user_object_scope_and_golden_bindings():
    findings=[
        _finding('Компрессорная','4.5',54.3,'ПЗ.pdf',12),
        _finding('Компрессорная','4.5',48.7,'ПЗУ.pdf',5),
        _finding('Модуль обеспыливания','4.12',23.5,'ПЗ.pdf',20),
        _finding('Модуль обеспыливания','4.12',23.5,'ПЗУ.pdf',8),
        _finding('Здание проборазделки','4.13',89.9,'ПЗ.pdf',21),
        _finding('Здание проборазделки','4.13',89.9,'ПЗУ.pdf',9),
    ]
    comparisons=[
        _comparison('Компрессорная','4.5','PROJECT_FINDING','Выявлено несоответствие',(54.3,48.7)),
        _comparison('Модуль обеспыливания','4.12','VERIFIED_OK','Соответствует',(23.5,23.5)),
        _comparison('Здание проборазделки','4.13','VERIFIED_OK','Соответствует',(89.9,89.9)),
    ]
    docs=[{'consolidated_registry':_registry(),'project_review_plan':{'items':[]}}]
    project=Legacy18Adapter().build(
        project_name='Тест 77',documents=docs,findings=findings,comparisons=comparisons,assembly_rows=_assembly(),
    )
    assert project.stats()['objects']==3
    assert project.stats()['object_candidates']==4
    assert project.validate()==[]
    golden=evaluate_golden_cases(project)
    assert golden['passed'] is True


def test_legacy_adapter_keeps_23_5_and_89_9_on_different_objects():
    docs=[{'consolidated_registry':_registry(),'project_review_plan':{'items':[]}}]
    findings=[
        _finding('Модуль обеспыливания','4.12',23.5,'ПЗ.pdf',20),
        _finding('Здание проборазделки','4.13',89.9,'ПЗ.pdf',21),
    ]
    project=Legacy18Adapter().build(
        project_name='Тест 77',documents=docs,findings=findings,comparisons=[],assembly_rows=_assembly(),
    )
    by_name={obj.name:obj.object_id for obj in project.objects.values()}
    dedusting=[p.value for p in project.object_properties(by_name['Модуль обеспыливания'])]
    sample=[p.value for p in project.object_properties(by_name['Здание проборазделки'])]
    assert 23.5 in dedusting and 89.9 not in dedusting
    assert 89.9 in sample and 23.5 not in sample
