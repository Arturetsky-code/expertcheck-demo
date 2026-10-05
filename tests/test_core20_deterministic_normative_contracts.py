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


def test_responsibility_level_promotes_only_as_confirmed_owner_design_decision():
    contract = _contract("FZ384-4-7-RESP-LEVEL")
    page = _page(
        "Для здания установлен уровень ответственности: нормальный. "
        "Уровень ответственности принят нормальный в соответствии с заданием на проектирование."
    )
    documents = [{
        "project_understanding": {
            "objects": [{
                "object_id": "OBJ-1",
                "properties": {
                    "responsibility_level": [{
                        "document": page["document"],
                        "page": page["page"],
                    }]
                },
            }]
        }
    }]

    set_eval = _set_completeness_evaluation(contract, [page], documents)
    result = _gate(contract, set_eval, page)

    assert set_eval["complete"] is True
    assert set_eval["owner_scope_state"] == "CONFIRMED"
    assert result["kind"] == "VERIFIED_OK"
    assert result["proof_state"] == "DETERMINISTIC_SET_COMPLETENESS_PROOF"
    assert result["reason_code"] == "NORMATIVE_SET_COMPLETENESS_PROOF_CONFIRMED"


def test_responsibility_level_does_not_promote_generic_normative_enumeration():
    contract = _contract("FZ384-4-7-RESP-LEVEL")
    page = _page(
        "Уровень ответственности может быть повышенный, нормальный или пониженный "
        "в зависимости от характеристик здания."
    )
    documents = [{
        "project_understanding": {
            "objects": [{
                "object_id": "OBJ-1",
                "properties": {
                    "responsibility_level": [{
                        "document": page["document"],
                        "page": page["page"],
                    }]
                },
            }]
        }
    }]

    set_eval = _set_completeness_evaluation(contract, [page], documents)

    assert set_eval["complete"] is False
    assert "Установленный уровень ответственности объекта" in set_eval["missing_labels"]


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
