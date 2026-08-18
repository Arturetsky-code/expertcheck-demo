
from pathlib import Path
from core.expert_practice_intelligence import ExpertPracticeIntelligence
ROOT=Path(__file__).parent/"knowledge"

def test_real_remarks_loaded():
    e=ExpertPracticeIntelligence(ROOT)
    s=e.summary()
    assert s["verified_remark_records"] >= 2200
    assert s["derived_recurrent_rules"] >= 250
    assert len(e.remarks) >= 2200

def test_object_registry_analogs_exist():
    e=ExpertPracticeIntelligence(ROOT)
    hits=e.analogs("В разных томах различается перечень проектируемых объектов. Необходимо представить достоверный состав объектов.",
                   target_code="OBJECT_REGISTRY",issue_families=["CROSS_SECTION_MISMATCH"],limit=5)
    assert hits
    assert any("перечень" in (h["remark"] or "").lower() and "объект" in (h["remark"] or "").lower() for h in hits)

def test_gpzu_source_document_practice_exists():
    e=ExpertPracticeIntelligence(ROOT)
    hits=e.analogs("В составе исходных данных отсутствует градостроительный план земельного участка",
                   target_code="LAND_DOCUMENTS",issue_families=["SOURCE_DATA"],limit=5)
    assert hits
    assert any("градостроитель" in (h["remark"] or "").lower() or "гпзу" in (h["remark"] or "").lower() for h in hits)

def test_historical_normative_refs_are_not_verified_law():
    import json
    rows=json.loads((ROOT/"historical_normative_citations.json").read_text(encoding="utf-8"))
    assert rows
    assert all(x["status"]=="HISTORICAL_EXPERT_CITATION_ONLY" for x in rows[:20])

def test_risk_uses_recurrence_and_analogs():
    e=ExpertPracticeIntelligence(ROOT)
    r=e.risk_from_evidence("Не представлены сведения и отсутствует обоснование в разделе",
                           issue_families=["MISSING_INFORMATION"])
    assert "remark_analogs" in r and "recurrent_rules" in r
    assert r["risk_score"] >= 0
