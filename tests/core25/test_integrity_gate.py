from core25.contracts import (
    Binding,
    BindingState,
    DecisionRequest,
    DecisionState,
    EvidenceRef,
    Proof,
)
from core25.integrity import enforce_decision_integrity


def test_categorical_decision_requires_addressable_evidence():
    evidence = EvidenceRef(
        evidence_id="E1",
        document_id="PZ",
        page=12,
        fragment="Производительность ДСК 500 т/ч",
        addressable=False,
        source_kind="GENERIC_SEARCH_HIT",
    )
    binding = Binding(
        binding_id="B1",
        evidence_id="E1",
        object_id="DSK",
        parameter_code="CAPACITY",
        state=BindingState.PROVEN,
    )
    proof = Proof(proof_id="P1", evidence_ids=("E1",), binding_ids=("B1",), valid=True)

    result = enforce_decision_integrity(
        DecisionRequest(
            requested_state=DecisionState.COMPLIANT,
            evidence=(evidence,),
            bindings=(binding,),
            proof=proof,
            ownership_required=True,
        )
    )

    assert result.state is DecisionState.REVIEW
    assert result.reason_code == "ADDRESSABLE_EVIDENCE_REQUIRED"


def test_categorical_decision_requires_proven_binding_when_owner_required():
    evidence = EvidenceRef(
        evidence_id="E1",
        document_id="PZ",
        page=12,
        fragment="Производительность ДСК 500 т/ч",
        addressable=True,
        source_kind="PAGE_FRAGMENT",
    )
    binding = Binding(
        binding_id="B1",
        evidence_id="E1",
        object_id="DSK",
        parameter_code="CAPACITY",
        state=BindingState.CANDIDATE,
    )
    proof = Proof(proof_id="P1", evidence_ids=("E1",), binding_ids=("B1",), valid=True)

    result = enforce_decision_integrity(
        DecisionRequest(
            requested_state=DecisionState.NONCOMPLIANT,
            evidence=(evidence,),
            bindings=(binding,),
            proof=proof,
            ownership_required=True,
        )
    )

    assert result.state is DecisionState.REVIEW
    assert result.reason_code == "PROVEN_BINDING_REQUIRED"


def test_review_is_allowed_without_proof():
    result = enforce_decision_integrity(
        DecisionRequest(
            requested_state=DecisionState.REVIEW,
            evidence=(),
            bindings=(),
            proof=None,
            ownership_required=True,
        )
    )

    assert result.state is DecisionState.REVIEW
