from __future__ import annotations

from core.evidence_registry import evidence_record


def test_object_trust_score_is_not_presented_as_probability_confidence():
    rec=evidence_record({
        "object_trust_score": 310,
        "document_type": "ПЗУ",
        "document": "ПЗУ.pdf",
        "parameter_code": "OBJECT_ENTRY",
        "value_text": "Площадка ДСК",
    })
    assert rec["confidence"] == 310
    assert rec["confidence_kind"] == "OBJECT_TRUST_SCORE"


def test_core_confidence_keeps_probability_kind():
    rec=evidence_record({
        "core2_confidence": 0.91,
        "document_type": "ПЗУ",
        "document": "ПЗУ.pdf",
        "parameter_code": "OBJECT_ENTRY",
        "value_text": "Компрессорная",
    })
    assert rec["confidence"] == 0.91
    assert rec["confidence_kind"] == "CONFIDENCE"
