from __future__ import annotations

from core.semantic_evidence_engine import (
    _focused_evidence_text,
    _public_packet,
    _validate_judge,
    build_evidence_packet,
)


def _support(packet_id: str, evidence_id: str) -> dict:
    return {
        "packet_id": packet_id,
        "verdict": "SUPPORTS",
        "evidence_ids": [evidence_id],
        "same_entity": True,
        "same_property": True,
        "qualifiers_satisfied": True,
        "modality_satisfied": True,
        "confidence": 0.95,
        "reason": "Фрагмент подтверждает требование.",
    }


def test_evidence_window_keeps_late_project_decision_instead_of_prefix():
    prefix = ("Служебное описание исходных условий и общих положений. " * 24)
    target = (
        " Проектом предусмотрено металлическое ограждение части площадки ДСК; "
        "территория площадки ДСК ограждается по периметру."
    )
    full = prefix + target
    window = _focused_evidence_text(
        full,
        ["металличе", "огражден", "площадк"],
        max_chars=960,
    )
    assert "ограждение части площадки ДСК" in window
    assert len(window) <= 965
    assert not window.startswith(prefix[:300])


def test_public_payload_uses_anchor_focused_window_not_first_720_chars():
    prefix = ("Общие положения без сведений о требуемом решении. " * 24)
    target = (
        " Проектом предусмотрено металлическое ограждение части площадки ДСК. "
        "Территория площадки ДСК ограждается."
    )
    row = {
        "atom_id": "REQ-FENCE-A001",
        "domain": "assignment",
        "atom_text": "Предусмотреть металлическое ограждение части площадки ДСК.",
        "requirement_text": "Предусмотреть металлическое ограждение части площадки ДСК.",
        "atomic_kind": "PRESENCE_REQUIREMENT",
        "verification_recipe": {
            "expected_sections": ["ПЗУ"],
            "required_modality": "TEXT_OR_TABLE",
        },
        "evidence_contract_v2": {
            "scope": "SITE_SPECIFIC",
            "expected_sections": ["ПЗУ"],
            "required_modality": "TEXT_OR_TABLE",
            "critical_qualifiers": ["металлическ"],
            "requires_same_owner": False,
            "requires_same_parameter": False,
        },
        "evidence_candidates": [{
            "document": "ПЗУ.pdf",
            "page": 7,
            "section": "ПЗУ",
            "text": prefix + target,
            "contract_state": "SATISFIED",
            "source_modality": "TEXT_OR_TABLE",
            "design_marker": True,
            "score": 94,
        }],
    }
    packet = build_evidence_packet(row, {"facts": [], "passages": []})
    public = _public_packet(packet)
    assert public["evidence"]
    outbound = public["evidence"][0]["text"]
    assert "металлическое ограждение части площадки ДСК" in outbound
    assert len(outbound) <= 1000


def test_object_specific_contract_cannot_reach_l4_without_owner_binding():
    row = {
        "atom_id": "REQ-COMP-A001",
        "domain": "assignment",
        "atom_text": "Площадь застройки компрессорной должна составлять 54,3 м2.",
        "requirement_text": "Площадь застройки компрессорной должна составлять 54,3 м2.",
        "object_name": "Компрессорная",
        "scope_entity": "Компрессорная",
        "parameter_code": "AREA_BUILD",
        "atomic_kind": "VALUE_COMPARISON",
        "verification_recipe": {
            "expected_sections": ["АР"],
            "required_modality": "TEXT_OR_TABLE",
        },
        "evidence_contract_v2": {
            "scope": "OBJECT_SPECIFIC",
            "expected_sections": ["АР"],
            "required_modality": "TEXT_OR_TABLE",
            "critical_qualifiers": [],
            "requires_same_owner": True,
            "requires_same_parameter": True,
        },
        "evidence_candidates": [{
            "document": "АР.pdf",
            "page": 3,
            "section": "АР",
            "text": "Площадь застройки 54,3 м2.",
            "property_code": "AREA_BUILD",
            "contract_state": "SATISFIED",
            "source_modality": "TEXT_OR_TABLE",
            "score": 95,
        }],
    }
    packet = build_evidence_packet(row, {"facts": [], "passages": []})
    assert packet["evidence_level"] != "L4"
    assert packet["evidence"][0]["entity_binding_state"] == "MISMATCH"
    assert packet["evidence"][0]["property_binding_state"] == "MATCHED"


def test_categorical_judge_is_blocked_when_required_property_is_unproven():
    packet = {
        "packet_id": "P-METRIC",
        "binding_contract": {
            "requires_same_owner": False,
            "requires_same_parameter": True,
        },
        "critical_qualifiers": [],
        "evidence": [{
            "evidence_id": "E-1",
            "owner_match": None,
            "property_match": None,
        }],
    }
    result = _validate_judge(packet, _support("P-METRIC", "E-1"))
    assert result["valid"] is False
    assert any("не подтвердил тот же инженерный показатель" in reason for reason in result["validation_reasons"])


def test_categorical_judge_is_blocked_when_required_entity_is_unproven():
    packet = {
        "packet_id": "P-ENTITY",
        "binding_contract": {
            "requires_same_owner": True,
            "requires_same_parameter": False,
        },
        "critical_qualifiers": [],
        "evidence": [{
            "evidence_id": "E-1",
            "owner_match": None,
            "property_match": None,
        }],
    }
    result = _validate_judge(packet, _support("P-ENTITY", "E-1"))
    assert result["valid"] is False
    assert any("не подтвердил тождество объекта" in reason for reason in result["validation_reasons"])
