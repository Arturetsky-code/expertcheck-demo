import json
from types import SimpleNamespace

from core.atomic_requirement_graph import atomize_requirement
from core.constraint_engine import (
    canonicalize_constraint,
    canonicalize_observed,
    constraint_from_atom,
    evaluate_numeric_constraint,
)
from core.semantic_evidence_engine import _call_batches, build_evidence_packet, run_semantic_evidence_engine
from core.atomic_verification_engine import verify_atomic_requirements
from core.checklist_engine import ChecklistEngine
from tests.test_semantic_evidence_engine_140a1 import FakeProvider, _row


def _numeric_atom(text: str):
    atoms = atomize_requirement({"requirement_id": "NUM-1", "requirement_text": text})
    return next(atom for atom in atoms if atom.get("atomic_kind") == "VALUE_COMPARISON")


def test_comparison_operators_and_ranges_are_atomized():
    minimum = _numeric_atom("Продолжительность смены должна быть не менее 12 часов.")
    maximum = _numeric_atom("Рабочее давление должно быть не более 1,6 МПа.")
    interval = _numeric_atom("Высота сооружения должна быть от 2,5 до 3,0 м.")
    assert (minimum["comparison_operator"], minimum["required_value"], minimum["unit"]) == ("GE", 12.0, "ч")
    assert (maximum["comparison_operator"], maximum["required_value"], maximum["unit"]) == ("LE", 1.6, "МПа")
    assert interval["comparison_operator"] == "BETWEEN"
    assert (interval["required_min"], interval["required_max"], interval["unit"]) == (2.5, 3.0, "м")


def test_pressure_and_annual_capacity_are_compared_in_canonical_units():
    pressure_atom = _numeric_atom("Рабочее давление должно быть не более 1,6 МПа.")
    pressure = canonicalize_constraint(constraint_from_atom(pressure_atom), "PRESSURE")
    observed_pressure, pressure_unit = canonicalize_observed(1600, "кПа", "PRESSURE")
    assert pressure_unit == pressure.unit == "МПа"
    assert evaluate_numeric_constraint(pressure, observed_pressure)["satisfied"] is True

    capacity_atom = _numeric_atom("Производительность комплекса должна быть не менее 1,6 млн тонн в год.")
    capacity = canonicalize_constraint(constraint_from_atom(capacity_atom), "CAPACITY")
    observed_capacity, capacity_unit = canonicalize_observed(1600, "тыс. т/год", "CAPACITY")
    assert capacity_unit == capacity.unit == "т/год"
    assert observed_capacity == 1_600_000
    assert evaluate_numeric_constraint(capacity, observed_capacity)["satisfied"] is True


def test_executable_numeric_check_emits_a_real_project_finding():
    atom = _numeric_atom("Рабочее давление должно быть не более 1,6 МПа.")
    fact = {
        "fact_id": "F-PRESSURE-1", "property_code": "PRESSURE", "property_name": "Рабочее давление",
        "value": 1800, "unit": "кПа", "document": "ТХ.pdf", "page": 3, "section": "ТХ",
        "source_trace": "Рабочее давление 1800 кПа", "fact_admission_decision": "ADMIT",
        "evidence_quality_decision": "VERIFIED", "binding_status": "ROW_LOCKED",
        "physical_trace_level": "ROW_TRACE", "owner": "Проект",
    }
    result = verify_atomic_requirements(
        [atom], knowledge_root="knowledge", fact_graph={"facts": [fact], "passages": []}, page_corpus=[]
    )[0]
    assert result["verification_kind"] == "PROJECT_FINDING"
    assert result["difference"]["operator"] == "LE"
    assert result["difference"]["observed"] == 1.8
    assert result["difference"]["required"] == 1.6


def test_l4_is_blocked_when_addressed_entity_does_not_match():
    row = _row()
    row["object_name"] = "Насосная станция"
    row["evidence_candidates"][0]["owner"] = "Компрессорная станция"
    packet = build_evidence_packet(row, {"facts": [], "passages": []})
    assert packet["evidence_level"] != "L4"
    assert packet["evidence_contract_state"] == "UNSATISFIED"


class PartialProvider:
    name = "PartialProvider"

    def __init__(self):
        self.calls = 0

    def generate(self, prompt, system=""):
        self.calls += 1
        payload = json.loads(prompt)
        packets = payload["packets"]
        selected = packets[:1]
        decisions = [{
            "packet_id": packet["packet_id"], "verdict": "INSUFFICIENT",
            "evidence_ids": [], "same_entity": None, "same_property": None,
            "qualifiers_satisfied": False, "modality_satisfied": False,
            "confidence": 0.9, "reason": "Недостаточно доказательств.",
        } for packet in selected]
        return SimpleNamespace(ok=True, text=json.dumps({"decisions": decisions}), provider=self.name, model="partial-test")


def test_partial_batch_response_is_retried_per_missing_packet():
    packets = [{"packet_id": "P-1"}, {"packet_id": "P-2"}]
    provider = PartialProvider()
    responses, errors, calls = _call_batches(provider, packets, batch_size=4, retry_limit=12)
    assert set(responses) == {"P-1", "P-2"}
    assert provider.calls == 2
    assert [call["state"] for call in calls] == ["PARTIAL", "PASSED"]
    assert not errors


def test_ai_execution_audit_records_actual_provider_and_model():
    row = _row()
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=FakeProvider("OpenRouter", "judge"),
        critic_provider=FakeProvider("Groq", "critic"),
    )
    execution = audit["execution_log"][0]
    assert execution["judge_provider"] == "OpenRouter"
    assert execution["critic_provider"] == "Groq"
    assert execution["judge_model"] == "OpenRouter-test"
    assert execution["critic_model"] == "Groq-test"
    assert audit["judge_calls"][0]["state"] == "PASSED"


def test_technology_checklist_pack_is_active():
    engine = ChecklistEngine("knowledge/checklist_catalog.json")
    rows = [row for row in engine.items if row.get("source_file") == "Чек-лист №14 Технологические решения"]
    assert len(rows) == 97
    assert all("ТХ" in (row.get("document_types") or []) for row in rows)
