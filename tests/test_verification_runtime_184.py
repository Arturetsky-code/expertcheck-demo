from __future__ import annotations

import json
from types import SimpleNamespace

from core import semantic_evidence_engine as see
from core.verification_runtime_patch import (
    _confirm_cross_section_conflict,
    _downgrade_semantic_promotions,
    _hard_row_binding,
    _install_free_queue,
)


def test_cross_section_conflict_is_confirmable_without_owner_value_resolution():
    row = {
        "status": "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ",
        "object_id": "OBJ-COMPRESSOR",
        "parameter_code": "AREA_BUILD",
        "independent_trusted_sources": 2,
        "source_records": [
            {
                "document": "ПЗ.pdf",
                "page": 18,
                "section": "ПЗ",
                "object_id": "OBJ-COMPRESSOR",
                "parameter_code": "AREA_BUILD",
                "value": 54.3,
                "unit": "м2",
                "trusted_for_mismatch": True,
            },
            {
                "document": "ПЗУ.pdf",
                "page": 7,
                "section": "ПЗУ",
                "object_id": "OBJ-COMPRESSOR",
                "parameter_code": "AREA_BUILD",
                "value": 48.7,
                "unit": "м2",
                "trusted_for_mismatch": True,
            },
        ],
    }
    assert _confirm_cross_section_conflict(row) is True


def test_cross_section_equal_values_are_not_a_conflict():
    row = {
        "status": "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ",
        "object_id": "OBJ-1",
        "parameter_code": "AREA_BUILD",
        "independent_trusted_sources": 2,
        "source_records": [
            {"document": "ПЗ.pdf", "page": 1, "section": "ПЗ", "object_id": "OBJ-1", "parameter_code": "AREA_BUILD", "value": 89.9, "trusted_for_mismatch": True},
            {"document": "ПЗУ.pdf", "page": 2, "section": "ПЗУ", "object_id": "OBJ-1", "parameter_code": "AREA_BUILD", "value": 89.9, "trusted_for_mismatch": True},
        ],
    }
    assert _confirm_cross_section_conflict(row) is False


def test_advisory_dual_review_never_keeps_l5():
    rows = [{
        "specialized_checker_id": "SEMANTIC_EVIDENCE_CONSENSUS_V1",
        "evidence_level": "L5",
        "verification_kind": "VERIFIED_OK",
        "final_verification_kind": "VERIFIED_OK",
        "semantic_judge": {"verdict": "SUPPORTS", "valid": True},
        "semantic_critic": {"accept": True, "valid": True},
    }]
    verified, findings = _downgrade_semantic_promotions(rows)
    assert (verified, findings) == (1, 0)
    assert rows[0]["verification_kind"] == "REVIEW_QUESTION"
    assert rows[0]["evidence_level"] == "L4"
    assert rows[0]["semantic_consensus_state"] == "ADVISORY_DUAL_REVIEW"
    assert rows[0]["automatic_verdict_eligible"] is False


def test_physical_row_position_blocks_shift_to_neighbor_object():
    findings = [
        {
            "document": "ПЗ.pdf",
            "page": 10,
            "row_index": 12,
            "row_text": "4.12 Модуль обеспыливания 23,5 м2",
            "binding_status": "ROW_LOCKED",
            "genplan_position": "4.12",
            "object_hint": "Модуль обеспыливания",
            "core2_confidence": 0.95,
        },
        {
            "document": "ПЗ.pdf",
            "page": 10,
            "row_index": 12,
            "row_text": "4.12 Модуль обеспыливания 23,5 м2",
            "genplan_position": "4.13",
            "semantic_anchor_position": "4.13",
            "object_hint": "Здание проборазделки",
            "core2_confidence": 0.88,
        },
    ]
    stats = _hard_row_binding(findings)
    assert stats["physical_row_mismatches"] + stats["explicit_position_mismatches"] >= 1
    assert findings[1]["row_integrity_status"] == "BLOCKED_PHYSICAL_ROW_MISMATCH"
    assert findings[1]["comparison_excluded"] is True


class _FakeFreeGroq:
    name = "Groq"
    model = "openai/gpt-oss-120b"

    def __init__(self):
        self.calls: list[list[str]] = []

    def generate(self, prompt: str, system: str = ""):
        payload = json.loads(prompt)
        packets = payload["packets"]
        self.calls.append([packet["packet_id"] for packet in packets])
        decisions = []
        for packet in packets:
            evidence_id = packet["evidence"][0]["evidence_id"]
            decisions.append({
                "packet_id": packet["packet_id"],
                "verdict": "SUPPORTS",
                "evidence_ids": [evidence_id],
                "same_entity": True,
                "same_property": True,
                "qualifiers_satisfied": True,
                "modality_satisfied": True,
                "confidence": 0.95,
                "reason": "Тест",
            })
        return SimpleNamespace(
            ok=True,
            text=json.dumps({"decisions": decisions}, ensure_ascii=False),
            provider="Groq",
            model=self.model,
            status_code=200,
            error="",
        )


def test_free_queue_sends_single_packet_calls(monkeypatch):
    import core.verification_runtime_patch as runtime

    monkeypatch.setattr(runtime, "_pacing_seconds", lambda *args, **kwargs: 0.0)
    _install_free_queue()
    provider = _FakeFreeGroq()
    packets = [
        {
            "packet_id": f"P-{index}",
            "evidence": [{"evidence_id": f"E-{index}", "document": "ПЗ.pdf", "page": index, "section": "ПЗ", "text": "Факт"}],
        }
        for index in range(1, 4)
    ]
    collected, errors, calls = see._call_batches(provider, packets, checkpoint={})
    assert errors == []
    assert set(collected) == {"P-1", "P-2", "P-3"}
    assert provider.calls == [["P-1"], ["P-2"], ["P-3"]]
    assert all(call.get("requested") == 1 for call in calls if call.get("attempt"))



def test_runtime_does_not_reuse_other_entity_when_owner_binding_not_required():
    from core import semantic_evidence_engine as see
    from core.verification_runtime_patch import install

    install()

    class Provider:
        name = "Groq"
        model = "openai/gpt-oss-120b"
        def generate_validated(self, prompt, system, validator, json_schema=None):
            class Result:
                ok = True
                text = '{"decisions":[{"packet_id":"P-SITE","verdict":"SUPPORTS","evidence_ids":["E-1"],"same_entity":true,"same_property":true,"qualifiers_satisfied":true,"modality_satisfied":true,"confidence":0.95,"reason":"подтверждено"}]}'
                provider = "Groq"
                model = "openai/gpt-oss-120b"
                status_code = 200
                error = ""
            return Result()

    packet = {
        "packet_id": "P-SITE",
        "binding_contract": {
            "requires_same_owner": False,
            "requires_same_parameter": False,
        },
        "evidence": [{"evidence_id": "E-1"}],
    }
    checkpoint = {
        "P-SITE": {
            "packet_id": "P-SITE",
            "verdict": "OTHER_ENTITY",
            "evidence_ids": ["E-1"],
            "confidence": 0.95,
        }
    }
    collected, errors, calls = see._call_batches(
        Provider(),
        [packet],
        checkpoint=checkpoint,
        batch_size=1,
        max_calls=1,
    )
    assert not errors
    assert collected["P-SITE"]["verdict"] == "SUPPORTS"
    assert checkpoint["P-SITE"]["verdict"] == "SUPPORTS"
    assert any(call.get("attempt") == 1 for call in calls)
