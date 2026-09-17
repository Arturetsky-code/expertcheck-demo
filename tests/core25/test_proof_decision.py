import pytest

from core25.contracts import (
    Binding25,
    BindingState,
    DecisionState,
    Domain,
    Evidence25,
    ProofState,
    Requirement25,
    Scope,
)
from core25.decision import decide
from core25.proof import build_proof
from core25.routing import VerificationRoute


@pytest.fixture
def requirement_factory():
    def factory(**overrides):
        metadata = dict(overrides.pop("metadata", {}))
        values = {
            "requirement_id": "R1",
            "domain": Domain.ASSIGNMENT,
            "text": "Продолжительность смены 12 часов",
            "scope": Scope.PROJECT_GLOBAL,
            "verification_kind": "TYPED_VALUE",
            "parameter_code": "SHIFT_DURATION",
            "required_value": 12.0,
            "unit": "час",
            "expected_sections": ("ТХ",),
            "metadata": metadata,
        }
        values.update(overrides)
        return Requirement25(**values)

    return factory


@pytest.fixture
def route_factory():
    def factory(**overrides):
        values = {
            "kind": "TYPED_VALUE",
            "scope": Scope.PROJECT_GLOBAL,
            "expected_sections": ("ТХ",),
            "parameter_code": "SHIFT_DURATION",
            "requires_owner": False,
            "requires_addressable_evidence": True,
        }
        values.update(overrides)
        return VerificationRoute(**values)

    return factory


def _bound_evidence(evidence_id: str, value: float, *, page: int = 7):
    evidence = Evidence25(
        evidence_id=evidence_id,
        document="ТХ.pdf",
        section="ТХ",
        page=page,
        fragment=f"Продолжительность смены составляет {value:g} часов",
        addressable=True,
        source_kind="PAGE_TEXT",
        metadata={
            "value": value,
            "unit": "час",
            "parameter_code": "SHIFT_DURATION",
        },
    )
    binding = Binding25(
        binding_id=f"B-{evidence_id}",
        evidence_id=evidence_id,
        state=BindingState.BOUND,
        owner_id="PROJECT",
        parameter_code="SHIFT_DURATION",
    )
    return evidence, binding


def test_positive_semantic_judgment_without_selected_evidence_stays_insufficient(
    requirement_factory,
    route_factory,
):
    req = requirement_factory(metadata={"judge_verdict": "SUPPORTS", "critic_accept": True})
    proof = build_proof(req, route_factory(), (), ())
    assert proof.state is ProofState.INSUFFICIENT
    assert decide(proof).state is DecisionState.REVIEW


def test_bound_typed_value_match_is_proven(requirement_factory, route_factory):
    req = requirement_factory()
    ev, binding = _bound_evidence("E1", 12.0)
    proof = build_proof(req, route_factory(), (ev,), (binding,))
    assert proof.state is ProofState.PROVEN_MATCH
    assert proof.evidence_ids == ("E1",)
    assert proof.binding_ids == ("B-E1",)
    assert decide(proof).state is DecisionState.COMPLIANT


def test_bound_typed_value_mismatch_is_proven(requirement_factory, route_factory):
    req = requirement_factory()
    ev, binding = _bound_evidence("E2", 10.0)
    proof = build_proof(req, route_factory(), (ev,), (binding,))
    assert proof.state is ProofState.PROVEN_MISMATCH
    assert decide(proof).state is DecisionState.NONCOMPLIANT


def test_conflicting_bound_values_require_review(requirement_factory, route_factory):
    req = requirement_factory()
    ev1, binding1 = _bound_evidence("E3", 12.0, page=7)
    ev2, binding2 = _bound_evidence("E4", 10.0, page=8)
    proof = build_proof(req, route_factory(), (ev1, ev2), (binding1, binding2))
    assert proof.state is ProofState.CONFLICT
    assert decide(proof).state is DecisionState.REVIEW


def test_unbound_value_cannot_create_categorical_proof(requirement_factory, route_factory):
    req = requirement_factory()
    ev, _ = _bound_evidence("E5", 12.0)
    binding = Binding25(
        binding_id="B-E5",
        evidence_id="E5",
        state=BindingState.AMBIGUOUS,
        owner_id="PROJECT",
        parameter_code="SHIFT_DURATION",
    )
    proof = build_proof(req, route_factory(), (ev,), (binding,))
    assert proof.state is ProofState.INSUFFICIENT
    assert decide(proof).state is DecisionState.REVIEW
