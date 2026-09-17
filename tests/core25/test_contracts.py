import pytest

from core25.contracts import (
    Binding25,
    BindingState,
    Decision25,
    DecisionState,
    Evidence25,
    Proof25,
    ProofState,
    Trace25,
)


def test_noncanonical_evidence_is_not_proof_eligible():
    evidence = Evidence25(
        evidence_id="E1",
        document_name="ПЗ.pdf",
        page=2,
        fragment="Оглавление",
        addressable=True,
        canonical=False,
        source_role="TOC",
    )

    assert evidence.proof_eligible is False


def test_categorical_states_are_explicit():
    proof = Proof25(
        proof_id="P1",
        requirement_id="R1",
        state=ProofState.PROVEN_MATCH,
    )
    decision = Decision25(
        decision_id="D1",
        requirement_id="R1",
        state=DecisionState.COMPLIANT,
        proof=proof,
        trace_id="T1",
    )

    assert proof.is_categorical is True
    assert decision.is_categorical is True


def test_compliant_requires_concrete_proof_not_only_proof_id():
    with pytest.raises(ValueError, match="Proof25"):
        Decision25(
            decision_id="D1",
            requirement_id="R1",
            state=DecisionState.COMPLIANT,
            proof_id="P1",
            trace_id="T1",
        )


def test_noncompliant_requires_concrete_proof_not_only_proof_id():
    with pytest.raises(ValueError, match="Proof25"):
        Decision25(
            decision_id="D2",
            requirement_id="R1",
            state=DecisionState.NONCOMPLIANT,
            proof_id="P2",
            trace_id="T2",
        )


def test_categorical_trace_rejects_binding_for_different_evidence():
    evidence_1 = Evidence25(
        evidence_id="E1",
        document="ПЗ.pdf",
        page=10,
        fragment="Площадь здания 89,9 м2",
        addressable=True,
        source_role="PAGE_TEXT",
    )
    evidence_2 = Evidence25(
        evidence_id="E2",
        document="АР.pdf",
        page=7,
        fragment="Площадь модуля обеспыливания 23,5 м2",
        addressable=True,
        source_role="PAGE_TEXT",
    )
    wrong_binding = Binding25(
        binding_id="B2",
        evidence_id="E2",
        state=BindingState.BOUND,
        owner_id="MODULE-DUST",
        parameter_code="AREA",
    )
    proof = Proof25(
        proof_id="P1",
        requirement_id="R1",
        state=ProofState.PROVEN_MATCH,
        evidence_ids=("E1",),
        binding_ids=("B2",),
    )
    decision = Decision25(
        decision_id="D1",
        requirement_id="R1",
        state=DecisionState.COMPLIANT,
        proof=proof,
        trace_id="T1",
    )
    trace = Trace25(
        requirement_id="R1",
        evidence=(evidence_1, evidence_2),
        bindings=(wrong_binding,),
        proof=proof,
        decision=decision,
        trace_id="T1",
    )

    assert trace.is_categorical_trace_valid() is False
