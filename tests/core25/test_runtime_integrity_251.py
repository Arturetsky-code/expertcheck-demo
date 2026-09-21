from __future__ import annotations

import json

from core.ai_continuation_ledger import reconcile_domain_audit
from core.expert_review_engine import build_expert_risks
from core.report_engine import build_structured_report
from core.verified_verdict_gate import enforce_verified_verdicts, verdict_gate


def _packet(packet_id: str) -> dict:
    return {
        "semantic_evidence_packet": {
            "packet_id": packet_id,
            "evidence_level": "L4",
            "checker": {"consensus_eligible": True},
        }
    }


def test_core25_categorical_assignment_verdict_is_not_redowngraded_by_legacy_gate():
    row = {
        "final_verification_kind": "VERIFIED_OK",
        "verification_kind": "VERIFIED_OK",
        "evidence_level": "L5",
        "core25_decision": "COMPLIANT",
        "core25_integrity_gate_state": "PASSED",
        "proof_state": "PROVEN_MATCH",
        "proof_id": "P25-1",
        "trace_id": "T25-1",
        "verification_evidence": [
            {"document": "Раздел ПД №1_ПЗ.pdf", "page": 44, "fragment": "Мощность 1600 тыс. т/год"}
        ],
    }

    gate = verdict_gate(row, domain="assignment")
    assert gate["passed"] is True
    assert gate["core25_authoritative"] is True

    summary = enforce_verified_verdicts([row], domain="assignment")
    assert summary == {
        "version": "17.0-final-verdict-gate-v1",
        "domain": "assignment",
        "checked": 1,
        "passed": 1,
        "blocked": 0,
    }
    assert row["final_verification_kind"] == "VERIFIED_OK"
    assert row["status"] if "status" in row else True


def test_core25_categorical_assignment_verdict_still_fails_closed_without_trace():
    row = {
        "final_verification_kind": "VERIFIED_OK",
        "verification_kind": "VERIFIED_OK",
        "evidence_level": "L5",
        "core25_decision": "COMPLIANT",
        "core25_integrity_gate_state": "PASSED",
        "proof_state": "PROVEN_MATCH",
        "proof_id": "",
        "trace_id": "",
        "verification_evidence": [],
    }
    gate = verdict_gate(row, domain="assignment")
    assert gate["passed"] is False
    assert gate["required"] is True
    assert gate["reasons"]


def test_ai_ledger_prunes_phantom_checkpoint_responses_and_uses_current_rows():
    row_done = _packet("PKT-1")
    row_done["semantic_judge"] = {
        "response_received": True,
        "valid": True,
        "verdict": "INSUFFICIENT",
        "confidence": 0.9,
    }
    row_pending = _packet("PKT-2")
    checkpoint = {
        "judge": {
            "PKT-1": dict(row_done["semantic_judge"]),
            "STALE-PKT": {
                "response_received": True,
                "valid": True,
                "verdict": "SUPPORTS",
                "confidence": 0.99,
            },
        },
        "critic": {},
    }

    audit, ledger = reconcile_domain_audit(
        {"judge_candidates": 12, "judge_responses": 12},
        rows=[row_done, row_pending],
        checkpoint_domain=checkpoint,
        previous_audit={"cumulative_packet_total": 12, "judge_responses": 12},
        previous_ledger_domain={"packet_total": 12, "packet_ids": ["STALE-PKT"]},
    )

    assert audit["cumulative_packet_total"] == 2
    assert audit["judge_responses"] == 1
    assert audit["judge_pending"] == 1
    assert audit["unique_packages_complete"] == 1
    assert audit["telemetry_integrity_state"] == "REPAIRED"
    assert audit["telemetry_stale_judge_pruned"] == 1
    assert "STALE-PKT" not in checkpoint["judge"]
    assert ledger["packet_ids"] == ["PKT-1", "PKT-2"]


def test_ai_ledger_recovers_row_response_into_checkpoint():
    row = _packet("PKT-1")
    row["semantic_judge"] = {
        "response_received": True,
        "valid": True,
        "verdict": "INSUFFICIENT",
        "confidence": 0.9,
    }
    checkpoint = {"judge": {}, "critic": {}}

    audit, _ = reconcile_domain_audit(
        {},
        rows=[row],
        checkpoint_domain=checkpoint,
    )

    assert audit["judge_responses"] == 1
    assert audit["judge_pending"] == 0
    assert audit["telemetry_judge_recovered_from_rows"] == 1
    assert "PKT-1" in checkpoint["judge"]


def test_review_question_cannot_be_promoted_to_high_risk_by_knowledge_scenario(tmp_path):
    scenario_path = tmp_path / "risk_scenarios.json"
    scenario_path.write_text(json.dumps([
        {
            "scenario_id": "TEST-HIGH",
            "title": "Высокая историческая повторяемость",
            "category": "ТЭП и межраздельные сведения",
            "severity": 95,
            "recurrence": 10,
            "triggers": {"keywords": ["площадь застройки"], "statuses": ["расхождение"]},
            "possible_remark": "Тестовое замечание",
            "recommendation": "Тестовая рекомендация",
            "analogs": ["Test"],
        }
    ], ensure_ascii=False), encoding="utf-8")

    risks = build_expert_risks(
        [{
            "comparison_id": "TEST-REVIEW",
            "status": "Расхождение",
            "parameter_name": "Площадь застройки",
            "explanation": "Обнаружено расхождение площади застройки",
            "sources": "ПЗ, стр. 1",
            "independent_trusted_sources": 1,
            "independent_section_count": 1,
            "engineering_risk_score": 60,
            "priority": "Высокий",
        }],
        scenario_path=scenario_path,
    )

    assert len(risks) == 1
    assert risks[0]["finding_class"] == "REVIEW"
    assert risks[0]["level"] == "Средний"
    assert risks[0]["score"] <= 69


def test_report_summary_separates_incomplete_set_from_user_confirmation():
    report = build_structured_report(
        "Test",
        [{
            "document": "ПЗ.pdf",
            "completeness_user_confirmed": True,
            "completeness_summary": {
                "status": "Неполный комплект",
                "coverage": 43,
                "missing": 3,
                "user_confirmed": True,
            },
        }],
        [],
    )
    summary = report["summary"]
    assert summary["completeness"] == "Неполный комплект"
    assert summary["completeness_confirmed"] is True
    assert summary["completeness_coverage"] == 43
    assert summary["completeness_missing"] == 3
