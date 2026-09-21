from __future__ import annotations

from dataclasses import asdict
import json
from math import isfinite
from typing import Any, Mapping

from .contracts import (
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


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "value"):
        return _json_safe(value.value)
    return value


def _dump_payload(value: Any) -> str:
    return json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def dump_result(result: VerificationResult25) -> str:
    """Serialize one verification result.

    Kept for compatibility with the first core25 persistence surface.
    New callers that persist a run should use dump_results.
    """
    return _dump_payload(asdict(result))


def dump_results(results: tuple[VerificationResult25, ...]) -> str:
    """Serialize an ordered verification run without losing canonical trace data."""
    return _dump_payload([asdict(result) for result in results])


def _requirement(raw: Mapping[str, Any]) -> Requirement25:
    return Requirement25(
        requirement_id=str(raw.get("requirement_id") or ""),
        domain=Domain(str(raw.get("domain") or Domain.ASSIGNMENT.value)),
        text=str(raw.get("text") or ""),
        scope=Scope(str(raw.get("scope") or Scope.UNRESOLVED.value)),
        verification_kind=str(raw.get("verification_kind") or ""),
        target_object_id=raw.get("target_object_id"),
        parameter_code=str(raw.get("parameter_code") or ""),
        required_value=raw.get("required_value"),
        unit=str(raw.get("unit") or ""),
        expected_sections=tuple(raw.get("expected_sections") or ()),
        source_document=str(raw.get("source_document") or ""),
        source_page=raw.get("source_page"),
        source_fragment=str(raw.get("source_fragment") or ""),
        metadata=dict(raw.get("metadata") or {}),
    )


def _evidence(raw: Mapping[str, Any]) -> Evidence25:
    return Evidence25(
        evidence_id=str(raw.get("evidence_id") or ""),
        document=str(raw.get("document") or ""),
        document_name=str(raw.get("document_name") or ""),
        section=str(raw.get("section") or ""),
        page=raw.get("page"),
        table_id=str(raw.get("table_id") or ""),
        row_id=str(raw.get("row_id") or ""),
        cell_id=str(raw.get("cell_id") or ""),
        fragment=str(raw.get("fragment") or ""),
        source_kind=str(raw.get("source_kind") or ""),
        source_role=str(raw.get("source_role") or ""),
        addressable=bool(raw.get("addressable")),
        canonical=bool(raw.get("canonical", True)),
        trusted=bool(raw.get("trusted")),
        confidence=raw.get("confidence"),
        metadata=dict(raw.get("metadata") or {}),
    )


def _binding(raw: Mapping[str, Any]) -> Binding25:
    return Binding25(
        binding_id=str(raw.get("binding_id") or ""),
        evidence_id=str(raw.get("evidence_id") or ""),
        state=BindingState(str(raw.get("state") or BindingState.UNBOUND.value)),
        owner_id=str(raw.get("owner_id") or ""),
        parameter_code=str(raw.get("parameter_code") or ""),
        concept_code=str(raw.get("concept_code") or ""),
        method=str(raw.get("method") or ""),
        reason=str(raw.get("reason") or ""),
        reason_code=str(raw.get("reason_code") or ""),
        supporting_evidence_ids=tuple(raw.get("supporting_evidence_ids") or ()),
        metadata=dict(raw.get("metadata") or {}),
    )


def _proof(raw: Mapping[str, Any]) -> Proof25:
    return Proof25(
        proof_id=str(raw.get("proof_id") or ""),
        requirement_id=str(raw.get("requirement_id") or ""),
        state=ProofState(str(raw.get("state") or ProofState.INSUFFICIENT.value)),
        evidence_ids=tuple(raw.get("evidence_ids") or ()),
        binding_ids=tuple(raw.get("binding_ids") or ()),
        reason_code=str(raw.get("reason_code") or ""),
        metadata=dict(raw.get("metadata") or {}),
    )


def _result(raw: Mapping[str, Any]) -> VerificationResult25:
    requirement = _requirement(raw["requirement"])
    trace_raw = raw["trace"]
    proof = _proof(trace_raw["proof"])
    decision_raw = trace_raw["decision"]
    decision = Decision25(
        decision_id=str(decision_raw.get("decision_id") or ""),
        requirement_id=str(decision_raw.get("requirement_id") or ""),
        state=DecisionState(str(decision_raw.get("state") or DecisionState.REVIEW.value)),
        proof=proof,
        proof_id=str(decision_raw.get("proof_id") or ""),
        trace_id=str(decision_raw.get("trace_id") or ""),
        reason_code=str(decision_raw.get("reason_code") or ""),
        metadata=dict(decision_raw.get("metadata") or {}),
    )
    trace = Trace25(
        requirement_id=str(trace_raw.get("requirement_id") or requirement.requirement_id),
        evidence=tuple(_evidence(item) for item in trace_raw.get("evidence") or ()),
        bindings=tuple(_binding(item) for item in trace_raw.get("bindings") or ()),
        proof=proof,
        decision=decision,
        trace_id=str(trace_raw.get("trace_id") or ""),
    )
    result = VerificationResult25(
        requirement=requirement,
        trace=trace,
        metadata=dict(raw.get("metadata") or {}),
    )
    if result.decision.is_categorical and not result.is_categorical_result_valid():
        raise ValueError("categorical verification result has invalid canonical trace")
    return result


def load_result(payload: str) -> VerificationResult25:
    """Restore one result serialized by dump_result."""
    raw = json.loads(payload)
    if not isinstance(raw, Mapping):
        raise ValueError("Single verification result payload must be a JSON object")
    return _result(raw)


def load_results(payload: str) -> tuple[VerificationResult25, ...]:
    """Restore an ordered run serialized by dump_results."""
    raw = json.loads(payload)
    if not isinstance(raw, list):
        raise ValueError("Verification results payload must be a JSON array")
    if any(not isinstance(item, Mapping) for item in raw):
        raise ValueError("Every verification result payload item must be a JSON object")
    return tuple(_result(item) for item in raw)
