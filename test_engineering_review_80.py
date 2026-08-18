from pathlib import Path

from core.engineering_review_engine import CrossSectionDependencyEngine
from core.checklist_compiler import compile_item


def test_dependency_engine_enriches_capacity():
    eng=CrossSectionDependencyEngine(Path(__file__).parent/'knowledge')
    rows=[{'parameter_code':'CAPACITY','status':'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ','strong_evidence_count':2}]
    assert eng.enrich_comparisons(rows)==1
    row=rows[0]
    assert 'ТХ' in row['data_owner_sections']
    assert row['preliminary_compliance']=='Выявлен риск несоответствия'
    assert row['normative_requirements']


def test_checklist_compiler_has_execution_class():
    r=compile_item({'question':'Сверить мощность между ПЗ и разделом электроснабжения'}).to_dict()
    assert r['automation_class']=='CALC'
    assert 'POWER_INSTALLED' in r['parameter_codes']


def test_semantic_check_uses_ai_class():
    r=compile_item({'question':'Проверить обоснованность принятых решений по водоотведению'}).to_dict()
    assert r['automation_class']=='SEMANTIC'
    assert r['requires_semantic_review'] is True
