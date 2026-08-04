from pathlib import Path

from core.knowledge_base import KnowledgeBase
from core.risk_engine import calculate_engineering_risk


def test_evidence_summary():
    kb = KnowledgeBase(Path(__file__).resolve().parents[1] / "knowledge")
    summary = kb.summary()
    assert summary["projects_count"] == 10
    assert summary["remarks_count"] == 1254


def test_risk_is_explainable():
    item = {
        "result": "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ",
        "priority": "Высокий",
        "knowledge_project_count": 3,
        "knowledge_evidence_count": 9,
    }
    risk = calculate_engineering_risk(item)
    assert risk["level"] == "Высокий"
    assert risk["reasons"]
