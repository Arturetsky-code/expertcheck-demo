from __future__ import annotations

from .contracts import BindingState, Decision, DecisionRequest, DecisionState


_CATEGORICAL = {DecisionState.COMPLIANT, DecisionState.NONCOMPLIANT}


def _decision(request: DecisionRequest, state: DecisionState, reason_code: str) -> Decision:
    proof = request.proof
    return Decision(
        state=state,
        reason_code=reason_code,
        evidence_ids=tuple(proof.evidence_ids) if proof else (),
        binding_ids=tuple(proof.binding_ids) if proof else (),
        proof_id=proof.proof_id if proof else None,
    )


def enforce_decision_integrity(request: DecisionRequest) -> Decision:
    if request.requested_state not in _CATEGORICAL:
        return _decision(request, request.requested_state, "NON_CATEGORICAL_STATE")

    proof = request.proof
    if proof is None:
        return _decision(request, DecisionState.REVIEW, "PROOF_REQUIRED")

    evidence_by_id = {item.evidence_id: item for item in request.evidence}
    referenced_evidence = [evidence_by_id.get(evidence_id) for evidence_id in proof.evidence_ids]
    if not any(item is not None and item.addressable for item in referenced_evidence):
        return _decision(request, DecisionState.REVIEW, "ADDRESSABLE_EVIDENCE_REQUIRED")

    if request.ownership_required:
        bindings_by_id = {item.binding_id: item for item in request.bindings}
        referenced_bindings = [bindings_by_id.get(binding_id) for binding_id in proof.binding_ids]
        if not referenced_bindings or any(
            item is None or item.state is not BindingState.PROVEN
            for item in referenced_bindings
        ):
            return _decision(request, DecisionState.REVIEW, "PROVEN_BINDING_REQUIRED")

    if not proof.valid:
        return _decision(request, DecisionState.REVIEW, "PROOF_INVALID")

    return _decision(request, request.requested_state, "INTEGRITY_GATE_PASSED")
