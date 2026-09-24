from __future__ import annotations

from hashlib import sha1
from typing import Iterable, Mapping

from .adapters.core20 import (
    compare_typed_values,
    normalize_unit,
    numeric_value,
    parse_reserve_topology,
)
from .contracts import Binding25, BindingState, Evidence25, Proof25, ProofState, Requirement25
from .routing import VerificationRoute


_DESIGN_MARKERS = (
    "предусмотр",
    "проектом",
    "принят",
    "выполнен",
    "выполнена",
    "оборудуется",
    "ограждается",
    "устанавливается",
    "размещается",
    "осуществляется",
    "обеспечивается",
)


def _norm_text(value: object) -> str:
    return " ".join(str(value or "").replace("ё", "е").casefold().split())


def _has_project_assertion(text: str) -> bool:
    normalized = _norm_text(text)
    return any(marker in normalized for marker in _DESIGN_MARKERS)


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


def _presence_proof(
    requirement: Requirement25,
    route: VerificationRoute,
    pairs: tuple[tuple[Evidence25, Binding25], ...],
) -> Proof25:
    selected_items = []
    for evidence_item, binding in pairs:
        metadata = dict(evidence_item.metadata or {})
        legacy_kind = str(metadata.get("legacy_evidence_kind") or "").upper()
        drawing_open_canopy = (
            legacy_kind == "QUALIFIED_DRAWING_PROJECT_FACT"
            and str(metadata.get("drawing_fact_code") or "").upper() == "OPEN_CANOPY"
            and metadata.get("structured_project_fact") is True
            and int(metadata.get("drawing_facade_view_count") or 0) >= 3
            and metadata.get("drawing_roof_proven") is True
            and metadata.get("drawing_structural_frame_corroborated") is True
            and metadata.get("drawing_enclosure_conflict") is not True
            and bool(str(metadata.get("drawing_owner_binding") or "").strip())
        )
        if _has_project_assertion(evidence_item.fragment) or drawing_open_canopy:
            selected_items.append((evidence_item, binding))
    selected = tuple(selected_items)
    if not selected:
        return _insufficient(
            requirement,
            route,
            reason_code="PRESENCE_EVIDENCE_NOT_STRONG_ENOUGH",
        )

    evidence_ids = tuple(item.evidence_id for item, _ in selected)
    binding_ids = tuple(binding.binding_id for _, binding in selected)
    return Proof25(
        proof_id=_proof_id(requirement, route, evidence_ids, binding_ids),
        requirement_id=requirement.requirement_id,
        state=ProofState.PROVEN_MATCH,
        evidence_ids=evidence_ids,
        binding_ids=binding_ids,
        reason_code="ASSIGNMENT_PRESENCE_CONFIRMED",
    )



def _design_determined_proof(
    requirement: Requirement25,
    route: VerificationRoute,
    pairs: tuple[tuple[Evidence25, Binding25], ...],
) -> Proof25:
    selected: list[tuple[Evidence25, Binding25]] = []
    for evidence_item, binding in pairs:
        metadata = dict(evidence_item.metadata or {})
        kind = str(metadata.get("legacy_evidence_kind") or "").upper()
        subject = str(metadata.get("design_determined_subject") or "").upper()
        if kind != "QUALIFIED_DESIGN_DETERMINED":
            continue
        if subject == "CONSTRUCTION_DURATION":
            value = numeric_value(metadata.get("observed_value"))
            unit = normalize_unit(metadata.get("observed_unit"))
            if value is None or not unit:
                continue
        if not (_has_project_assertion(evidence_item.fragment) or metadata.get("structured_project_fact") is True):
            continue
        selected.append((evidence_item, binding))

    if not selected:
        return _insufficient(
            requirement,
            route,
            reason_code="DESIGN_DETERMINED_VALUE_NOT_PROVEN",
        )

    evidence_ids = tuple(item.evidence_id for item, _ in selected)
    binding_ids = tuple(binding.binding_id for _, binding in selected)
    return Proof25(
        proof_id=_proof_id(requirement, route, evidence_ids, binding_ids),
        requirement_id=requirement.requirement_id,
        state=ProofState.PROVEN_MATCH,
        evidence_ids=evidence_ids,
        binding_ids=binding_ids,
        reason_code="ASSIGNMENT_DESIGN_VALUE_CONFIRMED",
    )


_NEGATIVE_ASSERTION_MARKERS = (
    "не требуется",
    "не предусматривается",
    "не предусмотрено",
    "разработка не требуется",
    "требования отсутствуют",
    "не применяется",
    "отсутствует необходимость",
)


def _negative_assertion_proof(
    requirement: Requirement25,
    route: VerificationRoute,
    pairs: tuple[tuple[Evidence25, Binding25], ...],
) -> Proof25:
    selected: list[tuple[Evidence25, Binding25]] = []
    for evidence_item, binding in pairs:
        metadata = dict(evidence_item.metadata or {})
        kind = str(metadata.get("legacy_evidence_kind") or "").upper()
        fragment = _norm_text(evidence_item.fragment)
        if (
            kind == "QUALIFIED_NEGATIVE_APPLICABILITY"
            and metadata.get("negative_assertion") is True
            and any(marker in fragment for marker in _NEGATIVE_ASSERTION_MARKERS)
        ):
            selected.append((evidence_item, binding))
    if not selected:
        return _insufficient(
            requirement,
            route,
            reason_code="NEGATIVE_APPLICABILITY_NOT_PROVEN",
        )

    evidence_ids = tuple(item.evidence_id for item, _ in selected)
    binding_ids = tuple(binding.binding_id for _, binding in selected)
    return Proof25(
        proof_id=_proof_id(requirement, route, evidence_ids, binding_ids),
        requirement_id=requirement.requirement_id,
        state=ProofState.PROVEN_MATCH,
        evidence_ids=evidence_ids,
        binding_ids=binding_ids,
        reason_code="NEGATIVE_APPLICABILITY_CONFIRMED",
    )


def _normative_assertion_proof(
    requirement: Requirement25,
    route: VerificationRoute,
    pairs: tuple[tuple[Evidence25, Binding25], ...],
) -> Proof25:
    selected: list[tuple[Evidence25, Binding25]] = []
    for evidence_item, binding in pairs:
        metadata = dict(evidence_item.metadata or {})
        kind = str(metadata.get("legacy_evidence_kind") or "").upper()
        refs = tuple(metadata.get("matched_normative_refs") or ())
        terms = tuple(metadata.get("matched_terms") or ())
        if kind == "QUALIFIED_NORMATIVE_ASSERTION" and refs and len(terms) >= 2:
            selected.append((evidence_item, binding))
    if not selected:
        return _insufficient(
            requirement,
            route,
            reason_code="FACTUAL_NORMATIVE_ASSERTION_NOT_PROVEN",
        )

    evidence_ids = tuple(item.evidence_id for item, _ in selected)
    binding_ids = tuple(binding.binding_id for _, binding in selected)
    return Proof25(
        proof_id=_proof_id(requirement, route, evidence_ids, binding_ids),
        requirement_id=requirement.requirement_id,
        state=ProofState.PROVEN_MATCH,
        evidence_ids=evidence_ids,
        binding_ids=binding_ids,
        reason_code="FACTUAL_NORMATIVE_ASSERTION_CONFIRMED",
    )


def _normative_design_adoption_proof(
    requirement: Requirement25,
    route: VerificationRoute,
    pairs: tuple[tuple[Evidence25, Binding25], ...],
) -> Proof25:
    accepted: list[tuple[Evidence25, Binding25]] = []
    has_solution = False
    matched_refs: set[str] = set()
    required_refs: set[str] = set()

    for evidence_item, binding in pairs:
        metadata=dict(evidence_item.metadata or {})
        kind=str(metadata.get("legacy_evidence_kind") or "").upper()
        if kind != "NORMATIVE_DESIGN_ADOPTION" or metadata.get("normative_design_adoption") is not True:
            continue
        slot=str(metadata.get("proof_slot") or "").upper()
        required_refs.update(str(x) for x in (metadata.get("required_normative_refs") or ()) if str(x))
        if slot == "DESIGN_SOLUTION" and tuple(metadata.get("matched_terms") or ()):
            has_solution=True
            accepted.append((evidence_item,binding))
        elif slot == "NORMATIVE_ADOPTION":
            refs={str(x) for x in (metadata.get("matched_normative_refs") or ()) if str(x)}
            terms=tuple(metadata.get("matched_terms") or ())
            if refs and len(terms)>=2:
                matched_refs.update(refs)
                accepted.append((evidence_item,binding))

    if not has_solution or not required_refs or not required_refs <= matched_refs:
        return _insufficient(
            requirement,
            route,
            reason_code="ASSIGNMENT_NORMATIVE_DESIGN_ADOPTION_NOT_PROVEN",
        )

    evidence_ids=tuple(dict.fromkeys(item.evidence_id for item,_ in accepted))
    binding_ids=tuple(dict.fromkeys(binding.binding_id for _,binding in accepted))
    return Proof25(
        proof_id=_proof_id(requirement,route,evidence_ids,binding_ids),
        requirement_id=requirement.requirement_id,
        state=ProofState.PROVEN_MATCH,
        evidence_ids=evidence_ids,
        binding_ids=binding_ids,
        reason_code="ASSIGNMENT_NORMATIVE_DESIGN_ADOPTION_CONFIRMED",
        metadata={"normative_compliance_not_assessed":True},
    )


def _reserve_topology_proof(
    requirement: Requirement25,
    route: VerificationRoute,
    pairs: tuple[tuple[Evidence25, Binding25], ...],
) -> Proof25:
    required = parse_reserve_topology(requirement.text)
    if required is None:
        return _insufficient(
            requirement,
            route,
            reason_code="RESERVE_TOPOLOGY_REQUIREMENT_UNSTRUCTURED",
        )

    accepted: list[tuple[Evidence25, Binding25, tuple[int, int]]] = []
    for evidence_item, binding in pairs:
        if not _has_project_assertion(evidence_item.fragment):
            continue
        topology = parse_reserve_topology(evidence_item.fragment)
        if topology is None:
            continue
        accepted.append((evidence_item, binding, topology))

    if not accepted:
        return _insufficient(
            requirement,
            route,
            reason_code="RESERVE_TOPOLOGY_NOT_PROVEN",
        )

    evidence_ids = tuple(item.evidence_id for item, _, _ in accepted)
    binding_ids = tuple(binding.binding_id for _, binding, _ in accepted)
    topologies = tuple(topology for _, _, topology in accepted)
    unique_topologies = set(topologies)
    proof_id = _proof_id(requirement, route, evidence_ids, binding_ids)
    required_metadata = {"working": required[0], "reserve": required[1]}

    if len(unique_topologies) > 1:
        return Proof25(
            proof_id=proof_id,
            requirement_id=requirement.requirement_id,
            state=ProofState.CONFLICT,
            evidence_ids=evidence_ids,
            binding_ids=binding_ids,
            reason_code="RESERVE_TOPOLOGY_PROJECT_CONFLICT",
            metadata={
                "required_topology": required_metadata,
                "project_topologies": tuple(
                    {"working": topology[0], "reserve": topology[1]}
                    for topology in sorted(unique_topologies)
                ),
            },
        )

    actual = next(iter(unique_topologies))
    state = ProofState.PROVEN_MATCH if actual == required else ProofState.PROVEN_MISMATCH
    reason_code = "RESERVE_TOPOLOGY_MATCH" if actual == required else "RESERVE_TOPOLOGY_MISMATCH"
    return Proof25(
        proof_id=proof_id,
        requirement_id=requirement.requirement_id,
        state=state,
        evidence_ids=evidence_ids,
        binding_ids=binding_ids,
        reason_code=reason_code,
        metadata={
            "required_topology": required_metadata,
            "project_topology": {"working": actual[0], "reserve": actual[1]},
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
    if route.kind == "PRESENCE":
        return _presence_proof(requirement, route, pairs)
    if route.kind == "RESERVE_TOPOLOGY":
        return _reserve_topology_proof(requirement, route, pairs)
    if route.kind == "NEGATIVE_ASSERTION":
        return _negative_assertion_proof(requirement, route, pairs)
    if route.kind == "NORMATIVE_ASSERTION":
        return _normative_assertion_proof(requirement, route, pairs)
    if route.kind == "NORMATIVE_DESIGN_ADOPTION":
        return _normative_design_adoption_proof(requirement, route, pairs)
    if route.kind == "DESIGN_DETERMINED":
        return _design_determined_proof(requirement, route, pairs)

    return _insufficient(
        requirement,
        route,
        reason_code="PROOF_KIND_NOT_IMPLEMENTED",
        evidence_ids=tuple(item.evidence_id for item, _ in pairs),
        binding_ids=tuple(binding.binding_id for _, binding in pairs),
    )
