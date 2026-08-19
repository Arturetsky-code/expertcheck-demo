from core.evidence_provenance import annotate_evidence_provenance, assess_evidence
from core.cross_section_consistency import build_cross_section_checks


def _row(document, section, value, *, method="строка таблицы ТЭП", binding="ROW_LOCKED", position="4.13", confidence=.97):
    return {
        "document": document, "document_type": section, "page": 18,
        "parameter_code": "AREA_BUILD", "parameter_name": "Площадь застройки",
        "value": value, "unit": "м2", "object_hint": "Здание проборазделки",
        "semantic_anchor_name": "Здание проборазделки", "genplan_position": position,
        "confidence": confidence, "core2_confidence": confidence,
        "match_method": method, "binding_status": binding,
        "entity_property_binding": {"valid": True},
    }


def test_structured_row_receives_high_trust_passport():
    item = _row("ПЗ.pdf", "ПЗ", 89.9)
    annotate_evidence_provenance([item])
    assert item["evidence_quality_decision"] in {"VERIFIED", "SUPPORTED"}
    assert item["evidence_comparison_eligible"] is True
    assert item["evidence_mismatch_eligible"] is True
    assert item["evidence_id"].startswith("EV-")


def test_high_ai_confidence_without_structural_binding_cannot_create_mismatch():
    item = _row("ПЗ.pdf", "ПЗ", 23.5, method="семантический поиск", binding="", position="", confidence=.99)
    annotate_evidence_provenance([item])
    assert item["evidence_mismatch_eligible"] is False
    assert item["evidence_quality_decision"] == "HOLD"


def test_integrity_block_is_rejected_even_with_high_confidence():
    item = _row("ПЗ.pdf", "ПЗ", 23.5)
    item["row_integrity_status"] = "BLOCKED_SHIFTED_VALUE"
    item["comparison_excluded"] = True
    result = assess_evidence(item)
    assert result["decision"] == "REJECT"
    assert result["score"] == 0


def test_weak_conflicting_value_is_not_allowed_to_form_false_cross_section_mismatch():
    pz = _row("ПЗ.pdf", "ПЗ", 89.9)
    pzu = _row("ПЗУ.pdf", "ПЗУ1", 89.9)
    weak = _row("ПЗ-generic.pdf", "ПЗ", 23.5, method="семантический поиск", binding="", position="", confidence=.99)
    items = [pz, pzu, weak]
    annotate_evidence_provenance(items)
    rows = build_cross_section_checks(items)
    assert len(rows) == 1
    assert rows[0]["status"] == "СОВПАДАЕТ"
    assert "23.5" not in rows[0]["document_values"]
