from __future__ import annotations

from hashlib import sha1
from typing import Iterable, Mapping

from .adapters.core20 import compare_typed_values, normalize_unit, numeric_value
from .contracts import Binding25, BindingState, Evidence25, Proof25, ProofState, Requirement25
from .routing import VerificationRoute


def _proof_id(
    requirement: Requirement25,
    route: VerificationRoute,
    evidence_ids: tuple[str, ...],
    binding_ids: tuple[str, ...],
) -> str:
    payload = "|".join(
        (
            requirement.requirement_id,
            route.kind,
            ",".join(evidence_ids),
            ",".join(binding_ids),
        )
    ).encode("utf-8", "ignore")
    return "P25-" + sha1(payload).hexdigest()[:16].upper()


def _insufficient(
    requirement: Requirement25,
    route: VerificationRoute,
    *,
    reason_code: str,
    evidence_ids: tuple[str, ...] = (),
    binding_ids: tuple[str, ...] = (),
) -> Proof25:
    return Proof25(
        proof_id=_proof_id(requirement, route, evidence_ids, binding_ids),
        requirement_id=requirement.requirement_id,
        state=ProofState.INSUFFICIENT,
        evidence_ids=evidence_ids,
        binding_ids=binding_ids,
        reason_code=reason_code,
    )


def _system_limitation(
    requirement: Requirement25,
    route: VerificationRoute,
    *,
    reason_code: str,
    metadata: Mapping[str, object] | None = None,
) -> Proof25:
    return Proof25(
        proof_id=_proof_id(requirement, route, (), ()),
        requirement_id=requirement.requirement_id,
        state=ProofState.SYSTEM_LIMITATION,
        reason_code=reason_code,
        metadata=dict(metadata or {}),
    )


def _provider_failure(metadata: Mapping[str, object] | None) -> str:
    meta = dict(metadata or {})
    direct = str(meta.get("provider_error") or meta.get("ai_error") or "").strip()
    status = str(meta.get("provider_status") or meta.get("ai_status") or "").strip().casefold()
    http_status = str(meta.get("http_status") or meta.get("status_code") or "").strip()
    combined = " ".join((direct, status, http_status)).casefold()
    failure_markers = (
        "429",
        "rate limit",
        "rate_limit",
        "timeout",
        "timed out",
        "unavailable",
        "provider error",
        "provider_error",
        "service unavailable",
        "503",
    )
    if direct or status in {"error", "failed", "unavailable", "timeout"}:
        if not combined or any(marker in combined for marker in failure_markers) or status:
            return direct or status or http_status or "provider failure"
    if http_status in {"429", "503"}:
        return http_status
    return ""


def _eligible_pairs(
    requirement: Requirement25,
    route: VerificationRoute,
    evidence: Iterable[Evidence25],
    bindings: Iterable[Binding25],
) -> tuple[tuple[Evidence25, Binding25], ...]:
    binding_by_evidence = {
        item.evidence_id: item
        for item in bindings
        if item.state is BindingState.BOUND
    }
    pairs: list[tuple[Evidence25, Binding25]] = []
    for item in evidence:
        if _provider_failure(item.metadata):
            continue
        binding = binding_by_evidence.get(item.evidence_id)
        if binding is None:
            continue
        if route.requires_addressable_evidence and not item.proof_eligible:
            continue
        if route.parameter_code:
            bound_code = str(binding.parameter_code or "").strip().upper()
            if bound_code != route.parameter_code:
                continue
        if route.requires_owner:
            if not requirement.target_object_id or binding.owner_id != requirement.target_object_id:
                continue
        pairs.append((item, binding))
    return tuple(pairs)


def _typed_value_proof(
    requirement: Requirement25,
    route: VerificationRoute,
    pairs: tuple[tuple[Evidence25, Binding25], ...],
) -> Proof25:
    evidence_ids = tuple(item.evidence_id for item, _ in pairs)
    binding_ids = tuple(binding.binding_id for _, binding in pairs)

    required = numeric_value(requirement.required_value)
    if required is None:
        return _insufficient(
            requirement,
            route,
            reason_code="REQUIRED_VALUE_NOT_STRUCTURED",
            evidence_ids=evidence_ids,
            binding_ids=binding_ids,
        )

    required_unit = normalize_unit(requirement.unit)
    values: list[float] = []
    accepted_evidence_ids: list[str] = []
    accepted_binding_ids: list[str] = []

    for evidence_item, binding in pairs:
        metadata = dict(evidence_item.metadata or {})
        value = None
        for key in ("project_value", "observed_value", "value"):
            value = numeric_value(metadata.get(key))
            if value is not None:
                break
        if value is None:
            continue

        evidence_unit = normalize_unit(
            metadata.get("project_unit")
            or metadata.get("observed_unit")
            or metadata.get("unit")
            or requirement.unit
        )
        if required_unit and evidence_unit != required_unit:
            continue

        values.append(value)
        accepted_evidence_ids.append(evidence_item.evidence_id)
        accepted_binding_ids.append(binding.binding_id)

    if not values:
        return _insufficient(
            requirement,
            route,
            reason_code="BOUND_TYPED_VALUE_NOT_FOUND",
            evidence_ids=tuple(accepted_evidence_ids),
            binding_ids=tuple(accepted_binding_ids),
        )

    comparison_state, anchor = compare_typed_values(values, required)
    proof_evidence = tuple(accepted_evidence_ids)
    proof_bindings = tuple(accepted_binding_ids)
    proof_id = _proof_id(requirement, route, proof_evidence, proof_bindings)

    if comparison_state == "CONFLICT":
        state = ProofState.CONFLICT
        reason_code = "PROJECT_EVIDENCE_VALUE_CONFLICT"
    elif comparison_state == "MATCH":
        state = ProofState.PROVEN_MATCH
        reason_code = "TYPED_VALUE_MATCH"
    else:
        state = ProofState.PROVEN_MISMATCH
        reason_code = "TYPED_VALUE_MISMATCH"

    return Proof25(
        proof_id=proof_id,
        requirement_id=requirement.requirement_id,
        state=state,
        evidence_ids=proof_evidence,
        binding_ids=proof_bindings,
        reason_code=reason_code,
        metadata={
            "required_value": required,
            "required_unit": required_unit,
            "project_value": anchor,
            "project_values": tuple(values),
        },
    )


def build_proof(
    requirement: Requirement25,
    route: VerificationRoute,
    evidence: Iterable[Evidence25],
    bindings: Iterable[Binding25],
) -> Proof25:
    evidence_tuple = tuple(evidence)
    bindings_tuple = tuple(bindings)

    requirement_provider_failure = _provider_failure(requirement.metadata)
    if requirement_provider_failure:
        return _system_limitation(
            requirement,
            route,
            reason_code="AI_PROVIDER_FAILURE",
            metadata={"provider_error": requirement_provider_failure},
        )

    if route.kind == "REVIEW_ONLY":
        return _insufficient(requirement, route, reason_code="REVIEW_ONLY_ROUTE")

    failed_provider_evidence = tuple(
        item for item in evidence_tuple if _provider_failure(item.metadata)
    )
    pairs = _eligible_pairs(requirement, route, evidence_tuple, bindings_tuple)
    if not pairs:
        if failed_provider_evidence:
            return _system_limitation(
                requirement,
                route,
                reason_code="AI_PROVIDER_FAILURE",
                metadata={
                    "provider_failed_evidence_ids": tuple(item.evidence_id for item in failed_provider_evidence),
                },
            )
        return _insufficient(requirement, route, reason_code="NO_BOUND_CANONICAL_EVIDENCE")

    if route.kind == "TYPED_VALUE":
        return _typed_value_proof(requirement, route, pairs)

    return _insufficient(
        requirement,
        route,
        reason_code="PROOF_KIND_NOT_IMPLEMENTED",
        evidence_ids=tuple(item.evidence_id for item, _ in pairs),
        binding_ids=tuple(binding.binding_id for _, binding in pairs),
    )
