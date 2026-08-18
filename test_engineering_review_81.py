import json
from pathlib import Path
from core.engineering_review_engine import CrossSectionDependencyEngine
from core.checklist_compiler import compile_item

ROOT=Path(__file__).parent/'knowledge'
def test_dependency_catalog_expanded():
    e=CrossSectionDependencyEngine(ROOT)
    assert len(e.rules)>=35
    assert len(e.norms)>=19
    assert 'ILLUMINATION' in e.by_parameter
    assert 'RESPONSIBILITY_LEVEL' in e.by_parameter

def test_enrich_non_area_parameter():
    e=CrossSectionDependencyEngine(ROOT)
    rows=[{'parameter_code':'ILLUMINATION','status':'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ','evidence_count':2}]
    assert e.enrich_comparisons(rows)==1
    assert 'ИОС1' in rows[0]['data_owner_sections']
    assert rows[0]['normative_requirements']

def test_checklist_compiles_illumination():
    r=compile_item({'question':'Проверить соответствие освещённости рабочих зон требованиям'})
    assert 'ILLUMINATION' in r.parameter_codes
    assert r.automation_class in {'CALC','SEMANTIC'}
