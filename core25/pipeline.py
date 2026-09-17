from __future__ import annotations

from hashlib import sha1
from typing import Iterable, Mapping

from core20.model import Evidence as Evidence20
from core20.model import Requirement as Requirement20

from .adapters.core20 import adapt_evidence, adapt_requirement
from .binding import bind_evidence
from .contracts import (
    Evidence25,
    Requirement25,
    Trace25,
    VerificationResult25,
)
from .decision import decide
from .evidence import qualify_evidence
from .proof import build_proof
from .requirement_engine import normalize_assignment_requirement
from .routing import route_requirement


def _requirement25(item: Requirement25 | Requirement20 | dict) -> Requirement25:
    if isinstance(item, Requirement25):
        return item
    if isinstance(item, Requirement20):
        return adapt_requirement(item)
    if isinstance(item, dict):
        return normalize_assignment_requirement(item)
    raise TypeError(f"Unsupported requirement type: {type(item)!r}")


def _evidence25(item: Evidence25 | Evidence20) -> Evidence25:
    if isinstance(item, Evidence25):
        return item
    if isinstance(item, Evidence20):
        return adapt_evidence(item)
    raise TypeError(f"Unsupported evidence type: {type(item)!r}")


def _trace_id(requirement_id: str, proof_id: str, decision_id: str) -> str:
    payload = f"{requirement_id}|{proof_id}|{decision_id}".encode("utf-8", "ignore")
    return "T25-" + sha1(payload).hexdigest()[:16].upper()


def verify_assignment(
    requirements: Iterable[Requirement25 | Requirement20 | dict],
    evidence: Iterable[Evidence25 | Evidence20],
    known_objects: Mapping[str, tuple[str, ...]],
) -> tuple[VerificationResult25, ...]:
    """Run the 25.0 Assignment vertical slice through one auditable pipeline.

    This function only orchestrates existing stages. Domain-specific proof rules
    remain in routing/evidence/binding/proof modules.
    """
    evidence25 = tuple(_evidence25(item) for item in evidence)
    results: list[VerificationResult25] = []

    for raw_requirement in requirements:
        requirement = _requirement25(raw_requirement)
        route = route_requirement(requirement)
        qualified = qualify_evidence(evidence25, route)
        bindings = tuple(
            bind_evidence(requirement, item, known_objects)
            for item in qualified
        )
        proof = build_proof(requirement, route, qualified, bindings)
        decision = decide(proof)
        trace_id = _trace_id(requirement.requirement_id, proof.proof_id, decision.decision_id)
        trace = Trace25(
            requirement_id=requirement.requirement_id,
            evidence=qualified,
            bindings=bindings,
            proof=proof,
            decision=decision,
            trace_id=trace_id,
        )
        results.append(
            VerificationResult25(
                requirement=requirement,
                trace=trace,
                metadata={
                    "route_kind": route.kind,
                    "route_scope": route.scope.value,
                    "expected_sections": route.expected_sections,
                    "requires_owner": route.requires_owner,
                    "requires_addressable_evidence": route.requires_addressable_evidence,
                },
            )
        )

    return tuple(results)
