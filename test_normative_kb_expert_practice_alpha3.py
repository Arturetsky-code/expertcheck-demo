
from pathlib import Path
from core.pp87_compliance import PP87Compliance
from core.expert_practice_intelligence import ExpertPracticeIntelligence
from core.review_context_builder import ReviewContextBuilder
ROOT=Path(__file__).parent/"knowledge"

def test_pp87_mining_profile():
    p=PP87Compliance(ROOT)
    x=p.infer_profiles({"name":"Предприятие по добыче и первичной переработке твердых полезных ископаемых"})
    assert any(i["project_type"]=="MINING_PRIMARY_PROCESSING" for i in x)

def test_expert_pattern_cross_section():
    e=ExpertPracticeIntelligence(ROOT)
    x=e.classify("Значение не соответствует смежному разделу, привести в соответствие")
    assert any(i["pattern_id"]=="EP-CROSS-MISMATCH" for i in x)

def test_empty_verified_remarks_never_fabricates_analogs():
    e=ExpertPracticeIntelligence(ROOT)
    assert e.analogs("любое замечание")==[]

def test_unified_context_has_four_evidence_layers():
    b=ReviewContextBuilder(ROOT)
    x=b.build("Проверить мощность КТП и соответствие смежным разделам",object_name="КТП-1250",
              parameter_codes=["POWER_INSTALLED"],section="ИОС1",project_context={"project_type":"производственный"})
    assert "normative_context" in x and "expert_practice" in x and "pp87_context" in x and "evidence_quality" in x
    assert "по-русски" in x["ai_instruction"]
