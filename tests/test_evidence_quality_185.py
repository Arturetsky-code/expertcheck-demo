from __future__ import annotations

from core.semantic_evidence_engine import (
    _entity_tokens,
    _focused_evidence_text,
    _public_packet,
    _validate_judge,
    build_evidence_packet,
)
from core.ai_continuation_ledger import queue_status_from_document
from core.requirement_contracts import SCOPE_SITE, build_contract
from core.semantic_continuation import _refresh_assignment_contracts


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



def test_entity_tokens_keep_short_project_code_and_drop_generic_noun():
    assert _entity_tokens("Площадка ДСК") == ["дск"]
    assert "пробораз" in _entity_tokens("Здание проборазделки")


def test_old_184_checkpoint_is_displayed_as_revalidation_queue_not_completed_work():
    row = {
        "semantic_evidence_packet": {
            "packet_id": "P-OLD",
            "engine_version": "17.0-verified-core-consensus",
            "evidence_level": "L4",
            "checker": {"consensus_eligible": True},
        }
    }
    doc = {
        "assignment_atomic_compliance": [row],
        "automatic_checklist_review": {"atomic_verification": {"atoms": []}},
        "semantic_evidence_engine": {
            "assignment": {
                "judge_candidates": 1,
                "judge_responses": 1,
                "critic_responses": 0,
            }
        },
        "analysis_snapshot": {"snapshot_id": "SNAP-1"},
    }
    checkpoint = {
        "_project_fingerprint": "SNAP-1",
        "_semantic_engine_version": "17.0-verified-core-consensus",
        "assignment": {
            "judge": {"P-OLD": {"verdict": "INSUFFICIENT"}},
            "critic": {},
        },
    }
    status = queue_status_from_document(doc, checkpoint)
    assert status["checkpoint_stale"] is True
    assert status["eligible"] == 1
    assert status["judge_done"] == 0
    assert status["judge_remaining"] == 1
    assert status["packages_complete"] == 0


def test_site_fence_requirement_does_not_require_standalone_fence_owner():
    row = {
        "atom_id": "REQ-FENCE-SITE",
        "domain": "assignment",
        "atom_text": "Предусмотреть ограждение части площадки с расположенным технологическим оборудованием.",
        "requirement_text": "Предусмотреть ограждение части площадки с расположенным технологическим оборудованием.",
        "object_name": "Ограждение",
        "scope_entity": "Ограждение",
        "atomic_kind": "PRESENCE_REQUIREMENT",
        "requirement_type": "PRESENCE_REQUIREMENT",
    }
    contract = build_contract(row)
    assert contract["scope"] == SCOPE_SITE
    assert contract["requires_same_owner"] is False
    assert contract["expected_sections"] == ["ПЗУ"]

    row["evidence_contract_v2"] = contract
    row["verification_recipe"] = {
        "expected_sections": ["ПЗУ"],
        "required_modality": "TEXT_OR_TABLE",
    }
    row["evidence_candidates"] = [{
        "document": "ПЗУ.pdf",
        "page": 27,
        "section": "ПЗУ",
        "text": "Территория площадки ДСК ограждается панелями FENSYS по металлическим столбам высотой 2,0 м.",
        "contract_state": "SATISFIED",
        "source_modality": "TEXT_OR_TABLE",
        "design_marker": True,
        "score": 94,
        "owner_match": False,
    }]
    packet = build_evidence_packet(row, {"facts": [], "passages": []})
    assert packet["evidence_level"] == "L4"
    assert packet["evidence"][0]["contract_ready_for_judgement"] is True
    assert packet["binding_contract"]["requires_same_owner"] is False


def test_required_owner_mismatch_still_blocks_l4():
    row = {
        "atom_id": "REQ-BUILDING",
        "domain": "assignment",
        "atom_text": "В здании проборазделки предусмотреть вентиляцию.",
        "requirement_text": "В здании проборазделки предусмотреть вентиляцию.",
        "object_name": "Здание проборазделки",
        "scope_entity": "Здание проборазделки",
        "atomic_kind": "PRESENCE_REQUIREMENT",
        "verification_recipe": {"expected_sections": ["ИОС4"], "required_modality": "TEXT_OR_TABLE"},
        "evidence_contract_v2": {
            "scope": "OBJECT_SPECIFIC",
            "expected_sections": ["ИОС4"],
            "required_modality": "TEXT_OR_TABLE",
            "critical_qualifiers": [],
            "requires_same_owner": True,
            "requires_same_parameter": False,
        },
        "evidence_candidates": [{
            "document": "ИОС4.pdf",
            "page": 4,
            "section": "ИОС4",
            "text": "В здании лаборатории предусмотрена общеобменная вентиляция.",
            "contract_state": "SATISFIED",
            "source_modality": "TEXT_OR_TABLE",
            "design_marker": True,
            "score": 95,
            "owner_match": False,
        }],
    }
    packet = build_evidence_packet(row, {"facts": [], "passages": []})
    assert packet["evidence_level"] != "L4"



def test_snapshot_continuation_refreshes_stale_site_feature_contract():
    row = {
        "atom_id": "REQ-FENCE-STORED",
        "requirement_id": "REQ-FENCE-STORED",
        "atom_text": "Предусмотреть ограждение части площадки с расположенным технологическим оборудованием.",
        "requirement_text": "Предусмотреть ограждение части площадки с расположенным технологическим оборудованием.",
        "object_name": "Ограждение",
        "scope_entity": "Ограждение",
        "requirement_type": "PRESENCE_REQUIREMENT",
        "atomic_kind": "PRESENCE_REQUIREMENT",
        "expected_sections": ["ПЗУ", "ТХ"],
        "evidence_contract_v2": {
            "scope": "OBJECT_SPECIFIC",
            "expected_sections": ["ПЗУ", "ТХ"],
            "required_modality": "TEXT_OR_TABLE",
            "critical_qualifiers": [],
            "requires_same_owner": True,
            "requires_same_parameter": False,
            "check_method": "AI_EVIDENCE_REVIEW",
        },
    }
    checkpoint = {
        "judge": {"REQ-FENCE-STORED": {"verdict": "OTHER_ENTITY"}},
        "critic": {"REQ-FENCE-STORED": {"accept": True}},
    }
    _refresh_assignment_contracts([row], checkpoint)
    assert row["evidence_contract_v2"]["scope"] == "SITE_SPECIFIC"
    assert row["evidence_contract_v2"]["requires_same_owner"] is False
    assert row["expected_sections"] == ["ПЗУ"]
    assert "REQ-FENCE-STORED" not in checkpoint["judge"]
    assert "REQ-FENCE-STORED" not in checkpoint["critic"]
