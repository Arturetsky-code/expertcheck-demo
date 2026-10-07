from __future__ import annotations

import json
from pathlib import Path

from core20.normative_execution import _set_completeness_evaluation
from core20.normative_proof import _apply_gate


ROOT = Path(__file__).resolve().parents[1]


def _contract(requirement_id: str) -> dict:
    rows = json.loads((ROOT / "knowledge" / "normative_requirements_v3.json").read_text(encoding="utf-8"))
    row = next(item for item in rows if item.get("id") == requirement_id)
    return {**row, "requirement_id": requirement_id}


def _page(text: str, *, document: str = "ПЗ.pdf", page: int = 10, section: str = "ПЗ") -> dict:
    return {
        "document": document,
        "page": page,
        "document_type": section,
        "section": section,
        "text": text,
    }


def _gate(contract: dict, set_eval: dict, page: dict) -> dict:
    return _apply_gate({
        "requirement_id": contract["requirement_id"],
        "source": contract.get("source"),
        "paragraph": contract.get("paragraph"),
        "topic": contract.get("topic"),
        "sections": contract.get("sections") or [],
        "check_kind": contract.get("check_kind"),
        "proof_type_hint": (contract.get("evidence_contract") or {}).get("proof_type"),
        "kind": "VERIFIED_OK",
        "state": "Подтверждено retrieval",
        "reason_code": "NORMATIVE_RETRIEVAL_CANDIDATE_CONFIRMED",
        "evidence_document": page["document"],
        "evidence_page": page["page"],
        "evidence_fragment": page["text"],
        "set_completeness": set_eval,
    })


def test_emergency_lighting_activation_promotes_without_ai_when_all_groups_are_local():
    contract = _contract("SP52-7.6.1-EMERGENCY-LIGHTING-POWER")
    page = _page(
        "Аварийное освещение включается автоматически при отключении рабочего освещения. "
        "При отказе автоматики предусмотрено ручное включение при отказе автоматики.",
        document="ИОС1.pdf",
        page=22,
        section="ИОС",
    )

    set_eval = _set_completeness_evaluation(contract, [page], [])
    result = _gate(contract, set_eval, page)

    assert set_eval["complete"] is True
    assert result["kind"] == "VERIFIED_OK"
    assert result["proof_state"] == "DETERMINISTIC_SET_COMPLETENESS_PROOF"


def test_emergency_lighting_presence_alone_is_not_deterministic_proof():
    contract = _contract("SP52-7.6.1-EMERGENCY-LIGHTING-POWER")
    page = _page(
        "В здании предусмотрено аварийное освещение.",
        document="ИОС1.pdf",
        page=22,
        section="ИОС",
    )

    set_eval = _set_completeness_evaluation(contract, [page], [])

    assert set_eval["complete"] is False
    assert "Питание и включение аварийного освещения" in set_eval["missing_labels"]



def test_spz_reliability_special_group_promotes_only_for_confirmed_owner():
    contract = _contract("SP6-2025-5.2-SPZ-RELIABILITY")
    page = _page(
        "Электроприёмники СПЗ относятся к особой группе I категории "
        "по надёжности электроснабжения.",
        document="ИОС1.pdf",
        page=28,
        section="ИОС1",
    )
    documents = [{
        "project_understanding": {
            "objects": [{
                "object_id": "OBJ-1",
                "properties": {
                    "spz_reliability": [{"document": "ИОС1.pdf", "page": 28}],
                },
            }]
        }
    }]

    set_eval = _set_completeness_evaluation(contract, [page], documents)
    result = _gate(contract, set_eval, page)

    assert set_eval["complete"] is True
    assert set_eval["owner_scope_state"] == "CONFIRMED"
    assert set_eval["owner_object_id"] == "OBJ-1"
    assert result["kind"] == "VERIFIED_OK"
    assert result["proof_state"] == "DETERMINISTIC_SET_COMPLETENESS_PROOF"


def test_spz_reliability_ordinary_first_category_stays_semantic():
    contract = _contract("SP6-2025-5.2-SPZ-RELIABILITY")
    page = _page(
        "Электроприёмники СПЗ относятся к I категории "
        "по надёжности электроснабжения.",
        document="ИОС1.pdf",
        page=28,
        section="ИОС1",
    )
    documents = [{
        "project_understanding": {
            "objects": [{
                "object_id": "OBJ-1",
                "properties": {
                    "spz_reliability": [{"document": "ИОС1.pdf", "page": 28}],
                },
            }]
        }
    }]

    set_eval = _set_completeness_evaluation(contract, [page], documents)
    result = _gate(contract, set_eval, page)

    assert set_eval["complete"] is False
    assert result["kind"] == "REVIEW_QUESTION"
    assert result["proof_state"] == "SEMANTIC_PROOF_REQUIRED"


def test_spz_reliability_copied_normative_special_group_wording_stays_semantic():
    contract = _contract("SP6-2025-5.2-SPZ-RELIABILITY")
    page = _page(
        "Электроприёмники СПЗ должны относиться к I категории по надёжности "
        "электроснабжения, а для специальных объектов категория должна приниматься "
        "по особой группе I категории электроприёмников.",
        document="ИОС1.pdf",
        page=28,
        section="ИОС1",
    )
    documents = [{
        "project_understanding": {
            "objects": [{
                "object_id": "OBJ-1",
                "properties": {
                    "spz_reliability": [{"document": "ИОС1.pdf", "page": 28}],
                },
            }]
        }
    }]

    set_eval = _set_completeness_evaluation(contract, [page], documents)
    result = _gate(contract, set_eval, page)

    assert set_eval["complete"] is False
    assert result["kind"] == "REVIEW_QUESTION"
    assert result["proof_state"] == "SEMANTIC_PROOF_REQUIRED"


def test_spz_reliability_special_group_without_confirmed_owner_stays_semantic():
    contract = _contract("SP6-2025-5.2-SPZ-RELIABILITY")
    page = _page(
        "Электроприёмники систем противопожарной защиты отнесены к особой группе "
        "I категории по надёжности электроснабжения.",
        document="ИОС1.pdf",
        page=28,
        section="ИОС1",
    )

    set_eval = _set_completeness_evaluation(contract, [page], [])
    result = _gate(contract, set_eval, page)

    assert set_eval["complete"] is False
    assert set_eval["owner_scope_state"] == "OWNER_NOT_PROVEN"
    assert result["kind"] == "REVIEW_QUESTION"
    assert result["proof_state"] == "SEMANTIC_PROOF_REQUIRED"


def test_spz_panel_promotes_without_ai_only_for_same_confirmed_object():
    contract = _contract("SP6-2025-5.3-SPZ-PANEL")
    category_page = _page(
        "Электроприёмники систем противопожарной защиты относятся к I категории "
        "по надёжности электроснабжения.",
        document="ИОС1.pdf",
        page=30,
        section="ИОС1",
    )
    panel_page = _page(
        "Питание электроприёмников СПЗ выполняется от панели питания электрооборудования СПЗ "
        "в составе НКУ.",
        document="ИОС1.pdf",
        page=31,
        section="ИОС1",
    )
    documents = [{
        "project_understanding": {
            "objects": [{
                "object_id": "OBJ-1",
                "properties": {
                    "spz_reliability": [{"document": "ИОС1.pdf", "page": 30}],
                    "spz_panel": [{"document": "ИОС1.pdf", "page": 31}],
                },
            }]
        }
    }]

    set_eval = _set_completeness_evaluation(contract, [category_page, panel_page], documents)
    result = _gate(contract, set_eval, category_page)

    assert set_eval["complete"] is True
    assert set_eval["owner_scope_state"] == "CONFIRMED"
    assert set_eval["owner_object_id"] == "OBJ-1"
    assert result["kind"] == "VERIFIED_OK"
    assert result["proof_state"] == "DETERMINISTIC_SET_COMPLETENESS_PROOF"


def test_spz_panel_does_not_merge_evidence_from_different_objects():
    contract = _contract("SP6-2025-5.3-SPZ-PANEL")
    category_page = _page(
        "Электроприёмники систем противопожарной защиты относятся к I категории "
        "по надёжности электроснабжения.",
        document="ИОС1.pdf",
        page=30,
        section="ИОС1",
    )
    panel_page = _page(
        "Питание электроприёмников СПЗ выполняется от панели питания электрооборудования СПЗ "
        "в составе НКУ.",
        document="ИОС1.pdf",
        page=31,
        section="ИОС1",
    )
    documents = [{
        "project_understanding": {
            "objects": [
                {
                    "object_id": "OBJ-1",
                    "properties": {
                        "spz_reliability": [{"document": "ИОС1.pdf", "page": 30}],
                    },
                },
                {
                    "object_id": "OBJ-2",
                    "properties": {
                        "spz_panel": [{"document": "ИОС1.pdf", "page": 31}],
                    },
                },
            ]
        }
    }]

    set_eval = _set_completeness_evaluation(contract, [category_page, panel_page], documents)

    assert set_eval["complete"] is False
    assert set_eval["owner_scope_state"] in {"OWNER_NOT_PROVEN", "AMBIGUOUS_OWNER"}
