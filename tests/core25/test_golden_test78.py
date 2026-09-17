import json
from pathlib import Path

import pytest

from core25 import verify_assignment
from core25.contracts import Domain, Evidence25, Requirement25, Scope


CASES_PATH = Path(__file__).resolve().parents[2] / "core25" / "golden" / "test78_cases.json"


def load_cases():
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def _scope(value: str) -> Scope:
    return Scope[str(value or "UNRESOLVED").upper()]


def _requirement(raw: dict) -> Requirement25:
    metadata = dict(raw.get("metadata") or {})
    return Requirement25(
        requirement_id=raw["requirement_id"],
        domain=Domain.ASSIGNMENT,
        text=raw["requirement_text"],
        scope=_scope(raw.get("scope", "UNRESOLVED")),
        verification_kind=raw.get("verification_kind", ""),
        target_object_id=raw.get("target_object_id"),
        parameter_code=raw.get("parameter_code", ""),
        required_value=raw.get("required_value"),
        unit=raw.get("unit", ""),
        expected_sections=tuple(raw.get("expected_sections") or ()),
        metadata=metadata,
    )


def _evidence(raw: dict) -> Evidence25:
    return Evidence25(
        evidence_id=raw["evidence_id"],
        document=raw.get("document", ""),
        section=raw.get("section", ""),
        page=raw.get("page"),
        fragment=raw.get("fragment", ""),
        source_kind=raw.get("source_kind", ""),
        addressable=bool(raw.get("addressable")),
        metadata=dict(raw.get("metadata") or {}),
    )


def run_case(case: dict):
    result = verify_assignment(
        (_requirement(case["requirement"]),),
        tuple(_evidence(item) for item in case.get("evidence", [])),
        {key: tuple(value) for key, value in case.get("objects", {}).items()},
    )[0]
    return result


@pytest.mark.parametrize("case", load_cases(), ids=lambda item: item["case_id"])
def test_test78_golden_case(case):
    result = run_case(case)

    assert result.decision.state.value == case["expected_decision"]
    assert result.trace.proof.state.value == case["expected_proof_state"]
    used = set(result.trace.proof.evidence_ids)
    assert used.isdisjoint(case.get("forbidden_evidence_ids", []))

    if result.decision.is_categorical:
        assert result.trace.is_categorical_trace_valid() is True
