from __future__ import annotations

import json
from pathlib import Path

from core.ai_gateway import AIResult, FailoverProvider
from core.atomic_verification_engine import verify_checklist_rows
from core.review_queue import MAX_CLUSTER_SIZE, build_review_clusters
from core.semantic_evidence_engine import _extract_json, _validate_judge
from core.semantic_slot_gate import evaluate_semantic_slots


ROOT = Path(__file__).resolve().parents[1]


def test_gold_standard_contains_all_critical_regressions():
    payload = json.loads((ROOT / "knowledge" / "quality_gold_standard_v1.json").read_text(encoding="utf-8"))
    critical = {row["id"] for row in payload["cases"] if row.get("critical")}
    assert critical == {
        "GOLD-DECIMAL-SCALE-PLAUSIBILITY", "GOLD-ENTITY-METRIC-BINDING",
        "GOLD-CROSS-SECTION-FOOTPRINT", "GOLD-SAFETY-BARRIER-SEMANTICS",
        "GOLD-WORK-PERIOD-DURATION", "GOLD-ANNUAL-CAPACITY",
    }
    assert payload["release_gates"]["critical_regressions_allowed"] == 0


def test_semantic_slots_block_machine_guard_as_traffic_geometry_proof():
    gate = evaluate_semantic_slots(
        "Проверить наличие площадки разворота спецтехники у защитного ограждения проезда",
        "Технологическое оборудование ограждается сетчатым защитным кожухом",
    )
    assert gate["state"] == "BLOCKED"
    assert gate["coverage"] < 0.5


def test_semantic_slots_accept_exact_drawing_artifact_title():
    gate = evaluate_semantic_slots(
        "Проверить наличие плана организации рельефа",
        "План организации рельефа М 1:1000",
    )
    assert gate["state"] == "PASSED"


def test_unrelated_safety_barrier_confirmation_is_not_promoted_to_l5():
    checklist = [{
        "question": "Проверить наличие площадки разворота спецтехники у защитного ограждения проезда",
        "automatic_section": "ПЗУ",
        "compiled_rule": {
            "typed_check": "DOCUMENT_CONTENT_PRESENCE", "verification_level": "L1_PRESENCE",
            "evidence_terms": ["ограждения"],
        },
        "typed_check": "DOCUMENT_CONTENT_PRESENCE",
    }]
    pages = [{
        "document": "ПЗУ.pdf", "document_type": "ПЗУ", "section": "ПЗУ", "page": 4,
        "text": "Технологическое оборудование ограждается сетчатым защитным кожухом.",
    }]
    verify_checklist_rows(
        checklist, knowledge_root=str(ROOT / "knowledge"),
        fact_graph={"facts": [], "passages": pages}, page_corpus=pages,
    )
    assert checklist[0]["verification_kind"] != "VERIFIED_OK"
    assert checklist[0]["evidence_level"] != "L5"


def test_structured_response_recovery_accepts_wrappers_arrays_and_single_rows():
    wrapped = _extract_json('{"result":{"decisions":[{"packet_id":"P-1","verdict":"INSUFFICIENT"}]}}')
    array = _extract_json('[{"packet_id":"P-2","verdict":"INSUFFICIENT"}]')
    single = _extract_json('{"packet_id":"P-3","accept":false}')
    assert wrapped["decisions"][0]["packet_id"] == "P-1"
    assert array["decisions"][0]["packet_id"] == "P-2"
    assert single["reviews"][0]["packet_id"] == "P-3"


def test_failover_repairs_contract_only_after_independent_lanes_fail():
    class Provider:
        api_key = "configured"

        def __init__(self, name: str, repair_ok: bool):
            self.name = name
            self.repair_ok = repair_ok
            self.calls = 0

        def generate(self, prompt: str, system: str = "") -> AIResult:
            self.calls += 1
            if self.calls > 1 and self.repair_ok:
                return AIResult(True, self.name, text='{"decisions":[]}', status_code=200)
            return AIResult(True, self.name, text="не JSON", status_code=200)

    first = Provider("OpenRouter", True)
    second = Provider("Groq", False)
    result = FailoverProvider([first, second]).generate_validated(
        "{}", "Верните JSON",
        lambda text: isinstance((_extract_json(text) or {}).get("decisions"), list),
    )
    assert result.ok and result.provider == "OpenRouter"
    assert first.calls == 2 and second.calls == 1


def test_judge_must_affirm_entity_and_property_not_merely_omit_them():
    packet = {"evidence": [{"evidence_id": "E-1"}], "critical_qualifiers": []}
    raw = {
        "verdict": "SUPPORTS", "evidence_ids": ["E-1"], "confidence": 0.95,
        "qualifiers_satisfied": True, "modality_satisfied": True,
    }
    decision = _validate_judge(packet, raw)
    assert decision["valid"] is False
    assert any("сущности" in reason for reason in decision["validation_reasons"])
    assert any("свойства" in reason for reason in decision["validation_reasons"])


def test_specialist_queue_is_topical_and_bounded():
    rows = [{
        "ID": f"Q-{index:02d}", "Контур": "Чек-листы", "Объект": "—",
        "Проверка": f"Проверить расчёт баланса {index}", "Причина": "Нужна смысловая проверка",
        "Ожидаемые разделы": "ТХ", "Уровень доказательства": "L3",
    } for index in range(25)]
    clusters = build_review_clusters(rows)
    assert len(clusters) == 3
    assert sum(row["Количество вопросов"] for row in clusters) == 25
    assert max(row["Количество вопросов"] for row in clusters) <= MAX_CLUSTER_SIZE
    assert {row["Тема"] for row in clusters} == {"Расчёты и балансы"}
