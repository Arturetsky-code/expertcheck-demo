
from pathlib import Path
from core.engineering_review_engine import CrossSectionDependencyEngine
from core.checklist_compiler import compile_item
from core.remark_learning import RemarkLearningEngine

ROOT=Path(__file__).parent/"knowledge"

def test_dependency_catalog_82():
    e=CrossSectionDependencyEngine(ROOT)
    assert len(e.rules)>=50
    assert "PUMP_HEAD" in e.by_parameter
    assert "SEISMICITY" in e.by_parameter
    assert len(e.norms)>=28

def test_owner_diagnostics():
    e=CrossSectionDependencyEngine(ROOT)
    rows=[{"parameter_code":"POWER_INSTALLED","status":"совпадает","sources":"ПЗ; ПЗУ","evidence_count":2}]
    e.enrich_comparisons(rows)
    assert rows[0]["data_owner_evidence"]=="Не найден профильный источник"
    assert "ИОС1" in rows[0]["missing_expected_sections"]
    assert rows[0]["preliminary_compliance"].startswith("Недостаточно данных")

def test_checklist_semantic_has_evidence_contract():
    r=compile_item({"question":"Проверить обоснованность принятой схемы водоотведения"})
    assert r.automation_class=="SEMANTIC"
    assert "RELEVANT_FRAGMENT" in r.evidence_types
    assert r.negative_result_policy=="AI_WITH_EVIDENCE"

def test_checklist_calc_reservoir_count():
    r=compile_item({"question":"Сверить количество резервуаров между ПЗ и ВК"})
    assert "RESERVOIR_COUNT" in r.parameter_codes
    assert r.automation_class=="CALC"

def test_remark_issue_signature():
    e=RemarkLearningEngine(ROOT)
    sig=e.issue_signature("Значения мощности не совпадают между разделами", "POWER_INSTALLED", "ИОС1")
    assert "MISMATCH" in sig["families"]
    assert sig["parameter_code"]=="POWER_INSTALLED"
