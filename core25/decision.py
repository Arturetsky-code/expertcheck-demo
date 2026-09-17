from __future__ import annotations

from hashlib import sha1

from .contracts import Decision25, DecisionState, Proof25, ProofState


_DECISION_BY_PROOF = {
    ProofState.PROVEN_MATCH: DecisionState.COMPLIANT,
    ProofState.PROVEN_MISMATCH: DecisionState.NONCOMPLIANT,
    ProofState.NOT_APPLICABLE: DecisionState.NOT_APPLICABLE,
    ProofState.SYSTEM_LIMITATION: DecisionState.LIMITATION,
    ProofState.CONFLICT: DecisionState.REVIEW,
    ProofState.INSUFFICIENT: DecisionState.REVIEW,
}


def _decision_id(proof: Proof25) -> str:
    payload = f"{proof.requirement_id}|{proof.proof_id}|{proof.state.value}".encode("utf-8", "ignore")
    return "D25-" + sha1(payload).hexdigest()[:16].upper()


def decide(proof: Proof25) -> Decision25:
    state = _DECISION_BY_PROOF[proof.state]
    return Decision25(
        decision_id=_decision_id(proof),
        requirement_id=proof.requirement_id,
        state=state,
        proof=proof,
        proof_id=proof.proof_id,
        reason_code=proof.reason_code,
    )
