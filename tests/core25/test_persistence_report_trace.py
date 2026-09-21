import pytest

from core25 import verify_assignment
from core25.contracts import (
    Binding25,
    BindingState,
    Decision25,
    DecisionState,
    Domain,
    Evidence25,
    Proof25,
    ProofState,
    Requirement25,
    Scope,
    Trace25,
    VerificationResult25,
)
from core25.persistence import dump_result, dump_results, load_result, load_results
from core25.report_trace import report_row, report_trace_row


def _categorical_result():
    requirement = Requirement25(
        requirement_id="SHIFT-PERSIST",
        domain=Domain.ASSIGNMENT,
        text="Продолжительность смены 12 часов",
        scope=Scope.PROJECT_GLOBAL,
        verification_kind="TYPED_VALUE",
        parameter_code="SHIFT_DURATION",
        required_value=12.0,
        unit="час",
        expected_sections=("ТХ",),
    )
    evidence = Evidence25(
        evidence_id="E-SHIFT-PERSIST",
        document="ТХ.pdf",
        section="ТХ",
        page=7,
        fragment="Продолжительность смены составляет 12 часов.",
        addressable=True,
        source_kind="PAGE_TEXT",
        metadata={"parameter_code": "SHIFT_DURATION", "value": 12.0, "unit": "час"},
    )
    return verify_assignment((requirement,), (evidence,), {})[0]


def test_persistence_roundtrip_preserves_canonical_trace():
    original = _categorical_result()
    restored = load_result(dump_result(original))

    assert restored.decision.state is DecisionState.COMPLIANT
    assert restored.trace.is_categorical_trace_valid() is True
    assert restored.trace.proof.proof_id == original.trace.proof.proof_id
    assert restored.trace.proof.evidence_ids == original.trace.proof.evidence_ids
    assert restored.trace.proof.binding_ids == original.trace.proof.binding_ids
    assert restored.trace.evidence[0].document == "ТХ.pdf"
    assert restored.trace.evidence[0].page == 7
    assert "12 часов" in restored.trace.evidence[0].fragment


def test_plural_persistence_roundtrip_preserves_order_and_trace():
    first = _categorical_result()
    second = _categorical_result()

    restored = load_results(dump_results((first, second)))

    assert isinstance(restored, tuple)
    assert len(restored) == 2
    assert [item.requirement.requirement_id for item in restored] == [
        "SHIFT-PERSIST",
        "SHIFT-PERSIST",
    ]
    assert all(item.trace.is_categorical_trace_valid() for item in restored)
    assert restored[0].trace.proof.evidence_ids == first.trace.proof.evidence_ids


def test_report_trace_row_is_auditable_and_sanitized():
    result = _categorical_result()
    row = report_trace_row(result)

    assert row["decision"] == "COMPLIANT"
    assert row["proof_id"] == result.trace.proof.proof_id
    assert row["evidence_id"] == "E-SHIFT-PERSIST"
    assert row["binding_id"]
    assert row["document"] == "ТХ.pdf"
    assert row["page"] == 7
    assert "12 часов" in row["fragment"]
    assert "nan" not in str(row).casefold()


def test_report_row_matches_public_task9_contract():
    result = _categorical_result()
    row = report_row(result)

    assert row["requirement_id"] == "SHIFT-PERSIST"
    assert row["decision"] == "COMPLIANT"
    assert row["reason"]
    assert row["document"] == "ТХ.pdf"
    assert isinstance(row["page"], int)
    assert "12 часов" in row["fragment"]
    assert row["evidence_id"] == "E-SHIFT-PERSIST"
    assert row["binding_id"]
    assert row["proof_id"] == result.trace.proof.proof_id
    assert "nan" not in str(row).casefold()
    assert "alpha 9" not in str(row).casefold()


def test_report_row_fails_closed_for_invalid_categorical_trace():
    requirement = Requirement25(
        requirement_id="BROKEN-TRACE",
        domain=Domain.ASSIGNMENT,
        text="Продолжительность смены 12 часов",
        scope=Scope.PROJECT_GLOBAL,
        verification_kind="TYPED_VALUE",
        parameter_code="SHIFT_DURATION",
        required_value=12.0,
        unit="час",
    )
    proof = Proof25(
        proof_id="P-BROKEN",
        requirement_id="BROKEN-TRACE",
        state=ProofState.PROVEN_MATCH,
        evidence_ids=("E-MISSING",),
        binding_ids=("B-MISSING",),
        reason_code="MATCH",
    )
    decision = Decision25(
        decision_id="D-BROKEN",
        requirement_id="BROKEN-TRACE",
        state=DecisionState.COMPLIANT,
        proof=proof,
        trace_id="T-BROKEN",
        reason_code="MATCH",
    )
    result = VerificationResult25(
        requirement=requirement,
        trace=Trace25(
            requirement_id="BROKEN-TRACE",
            evidence=(),
            bindings=(),
            proof=proof,
            decision=decision,
            trace_id="T-BROKEN",
        ),
    )

    assert result.trace.is_categorical_trace_valid() is False
    with pytest.raises(ValueError, match="categorical trace"):
        report_row(result)


def test_report_trace_row_pairs_binding_with_its_evidence():
    requirement = Requirement25(
        requirement_id="AREA-TRACE",
        domain=Domain.ASSIGNMENT,
        text="Площадь здания 89,9 м2",
        scope=Scope.OBJECT_SPECIFIC,
        target_object_id="BUILDING-LAB",
        verification_kind="TYPED_VALUE",
        parameter_code="AREA",
        required_value=89.9,
        unit="м2",
    )
    evidence_1 = Evidence25(
        evidence_id="E1",
        document="АР.pdf",
        page=10,
        fragment="Площадь здания проборазделки 89,9 м2",
        addressable=True,
        source_kind="PAGE_TEXT",
    )
    evidence_2 = Evidence25(
        evidence_id="E2",
        document="ТХ.pdf",
        page=22,
        fragment="Площадь модуля обеспыливания 23,5 м2",
        addressable=True,
        source_kind="PAGE_TEXT",
    )
    binding_1 = Binding25(
        binding_id="B1",
        evidence_id="E1",
        state=BindingState.BOUND,
        owner_id="BUILDING-LAB",
        parameter_code="AREA",
    )
    binding_2 = Binding25(
        binding_id="B2",
        evidence_id="E2",
        state=BindingState.BOUND,
        owner_id="MODULE-DUST",
        parameter_code="AREA",
    )
    proof = Proof25(
        proof_id="P1",
        requirement_id="AREA-TRACE",
        state=ProofState.PROVEN_MATCH,
        evidence_ids=("E1", "E2"),
        binding_ids=("B2", "B1"),
    )
    decision = Decision25(
        decision_id="D1",
        requirement_id="AREA-TRACE",
        state=DecisionState.COMPLIANT,
        proof=proof,
        trace_id="T1",
    )
    trace = Trace25(
        requirement_id="AREA-TRACE",
        evidence=(evidence_1, evidence_2),
        bindings=(binding_2, binding_1),
        proof=proof,
        decision=decision,
        trace_id="T1",
    )
    result = VerificationResult25(requirement=requirement, trace=trace)

    assert trace.is_categorical_trace_valid() is True
    row = report_trace_row(result)
    assert row["evidence_id"] == "E1"
    assert row["binding_id"] == "B1"
    assert row["owner_id"] == "BUILDING-LAB"
