from __future__ import annotations

import json
from types import SimpleNamespace

from core.ai_gateway import AIResult, FailoverProvider
from core.atomic_requirement_graph import atomize_requirement
from core.atomic_verification_engine import verify_atomic_requirements
from core.coverage_acceleration import coverage_budget, diversified_candidate_order
from core.engineering_plausibility import (
    apply_engineering_plausibility_guard,
    plausibility_review_questions,
)
from core.evidence_reconstruction import sanitize_high_value_facts
from core.project_review_planner import build_review_plan
from core.report_quality_gate import validate_review_plan
from core.semantic_evidence_engine import _call_batches
from core.verified_verdict_gate import enforce_verified_verdicts


class _Provider:
    def __init__(self, name: str, text: str):
        self.name = name
        self.api_key = "configured"
        self.text = text
        self.calls = 0

    def generate(self, prompt: str, system: str = "") -> AIResult:
        self.calls += 1
        return AIResult(True, self.name, text=self.text, status_code=200, model=f"{self.name}-test")


def test_failover_treats_invalid_json_as_provider_failure():
    bad = _Provider("OpenRouter", "Вот результат проверки без JSON")
    good = _Provider("Groq", json.dumps({"decisions": [{"packet_id": "P-1"}]}))
    provider = FailoverProvider([bad, good])
    result = provider.generate_validated(
        "{}", "Верните JSON",
        lambda text: isinstance(json.loads(text).get("decisions"), list),
    )
    assert result.ok and result.provider == "Groq"
    assert bad.calls == good.calls == 1


def test_semantic_batch_uses_validated_failover_response():
    bad = _Provider("OpenRouter", "not-json")
    good = _Provider("Groq", json.dumps({
        "decisions": [{
            "packet_id": "P-1", "verdict": "INSUFFICIENT", "evidence_ids": [],
            "same_entity": False, "same_property": False,
            "qualifiers_satisfied": False, "modality_satisfied": False,
            "confidence": 0.2, "reason": "Доказательств недостаточно.",
        }],
    }))
    responses, errors, calls = _call_batches(
        FailoverProvider([bad, good]), [{"packet_id": "P-1"}], batch_size=4,
    )
    assert set(responses) == {"P-1"}
    assert not errors and calls[0]["actual_provider"] == "Groq"


def _capacity_atom() -> dict:
    requirement = {
        "requirement_id": "CAP-1521",
        "requirement_text": "Установить ДСК суммарной производительностью 500 т/ч",
        "requirement_type": "VALUE_COMPARISON",
        "object_name": "ДСК",
        "parameter_code": "CAPACITY",
        "required_value": 500,
        "unit": "т/ч",
    }
    atom = next(row for row in atomize_requirement(requirement) if row.get("atomic_kind") == "VALUE_COMPARISON")
    atom["directed_evidence_candidates"] = [{
        "evidence_state": "verified_candidate",
        "parameter_code": "CAPACITY",
        "value": 334.86,
        "unit": "т/ч",
        "document": "ТХ.pdf",
        "page": 17,
        "source_trace": "Часовая производительность отделения 334,86 т/ч",
        "exact_clause": "Часовая производительность отделения 334,86 т/ч",
        "owner_match": True,
        "score": 98,
    }]
    return atom


def test_capacity_level_question_keeps_observed_value_and_source():
    result = verify_atomic_requirements(
        [_capacity_atom()], knowledge_root="knowledge",
        fact_graph={"facts": [], "passages": []}, page_corpus=[],
    )[0]
    assert result["verification_kind"] == "REVIEW_QUESTION"
    assert result["difference"]["required"] == 500
    assert result["difference"]["observed"] == 334.86
    assert result["difference"]["sources"][0]["document"] == "ТХ.pdf"
    assert "334.86 т/ч" in result["decision_basis"]
    assert "ТХ.pdf, стр. 17" in result["evidence"][0]


def test_categorical_numeric_result_has_satisfied_contract_and_report_gate_state():
    atom = next(row for row in atomize_requirement({
        "requirement_id": "SHIFT-1521",
        "requirement_text": "Продолжительность смены – 12 часов",
        "requirement_type": "VALUE_COMPARISON",
        "parameter_code": "SHIFT_DURATION",
        "required_value": 12,
        "unit": "ч",
    }) if row.get("atomic_kind") == "VALUE_COMPARISON")
    atom["directed_evidence_candidates"] = [{
        "evidence_state": "verified_candidate", "parameter_code": "SHIFT_DURATION",
        "value": 12, "unit": "ч", "document": "ТХ.pdf", "page": 33,
        "source_trace": "Продолжительность смены 12 часов", "owner_match": True,
    }]
    result = verify_atomic_requirements(
        [atom], knowledge_root="knowledge",
        fact_graph={"facts": [], "passages": []}, page_corpus=[],
    )[0]
    assert result["verification_kind"] == "VERIFIED_OK"
    assert result["adversarial_state"] == "PASSED"
    assert result["evidence_contract_state"] == "SATISFIED"
    gate_summary = enforce_verified_verdicts([result], domain="assignment")
    assert gate_summary["passed"] == 1
    plan = build_review_plan(
        assignment_rows=[result],
        normative_rows=[], checklist_review={"results": []},
    )
    item = next(row for row in plan["items"] if row["domain_code"] == "assignment")
    assert item["adversarial_state"] == "PASSED"
    assert item["evidence_candidate_count"] == 1
    gate = validate_review_plan(plan)
    assert gate["status"] == "PASSED"


def test_non_admitted_duplicates_are_explicitly_excluded_from_comparison():
    rows = [{
        "parameter_code": "AREA_BUILD", "value": 43414, "unit": "м²",
        "fact_admission_decision": "HOLD",
        "fact_admission_reasons": ["уровень EQUIPMENT несовместим с building_footprint"],
    }]
    summary = sanitize_high_value_facts(rows)
    assert rows[0]["comparison_excluded"] is True
    assert "EQUIPMENT" in rows[0]["comparison_exclusion_reason"]
    assert summary["non_admitted_facts_excluded"] == 1


def test_pump_height_25_is_preserved_and_routed_as_decimal_review_question():
    common = {
        "document": "ПЗ.pdf", "page": 46, "genplan_position": "4.18",
        "object_hint": "Насосная станция", "binding_status": "ROW_LOCKED",
    }
    rows = [
        {**common, "parameter_code": "AREA_BUILD", "value": 26.9, "unit": "м²"},
        {**common, "parameter_code": "VOLUME_BUILD", "value": 67.25, "unit": "м³"},
        {**common, "parameter_code": "HEIGHT_BUILD", "value": 25, "unit": "м"},
    ]
    audit = apply_engineering_plausibility_guard(rows)
    height = rows[-1]
    assert height["value"] == 25
    assert height["possible_decimal_separator_candidate"] == 2.5
    assert height["comparison_excluded"] is True
    questions = plausibility_review_questions(audit)
    assert len(questions) == 1
    assert questions[0]["finding_type"] == "REVIEW_QUESTION"
    assert "25 м" in questions[0]["document_values"]
    assert "2.5 м" in questions[0]["document_values"]
    assert "Автоматическая подмена" in questions[0]["recommendation"]


def test_extended_budget_covers_project_sized_l4_queue_and_order_is_diversified():
    extended = coverage_budget("extended", "extended")
    assert extended.assignment_semantic_limit == 100
    assert extended.checklist_semantic_limit == 50
    packets = [
        {"packet_id": "A1", "domain": "checklist", "checker": {"checker_family": "A"}, "expected_sections": ["КР"], "evidence": [{"score": 99}]},
        {"packet_id": "A2", "domain": "checklist", "checker": {"checker_family": "A"}, "expected_sections": ["КР"], "evidence": [{"score": 98}]},
        {"packet_id": "B1", "domain": "checklist", "checker": {"checker_family": "B"}, "expected_sections": ["ТХ"], "evidence": [{"score": 80}]},
    ]
    assert [row["packet_id"] for row in diversified_candidate_order(packets)] == ["A1", "B1", "A2"]
