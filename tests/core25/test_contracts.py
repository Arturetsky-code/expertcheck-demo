import pytest

from core25.contracts import Decision25, DecisionState, Evidence25, Proof25, ProofState


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
