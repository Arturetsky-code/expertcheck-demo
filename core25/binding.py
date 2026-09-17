from __future__ import annotations

from hashlib import sha1
import re
from typing import Mapping

from .contracts import Binding25, BindingState, Evidence25, Requirement25, Scope


def _norm(value: object) -> str:
    return " ".join(str(value or "").strip().replace("ё", "е").casefold().split())


def _binding_id(requirement: Requirement25, evidence: Evidence25) -> str:
    payload = f"{requirement.requirement_id}|{evidence.evidence_id}".encode("utf-8", "ignore")
    return "B25-" + sha1(payload).hexdigest()[:16].upper()


def _resolve_owner_name(
    owner_name: str,
    known_objects: Mapping[str, tuple[str, ...]],
) -> str:
    needle = _norm(owner_name)
    if not needle:
        return ""
    matches: list[str] = []
    for object_id, aliases in known_objects.items():
        for alias in aliases:
            normalized = _norm(alias)
            if normalized and (needle == normalized or normalized in needle or needle in normalized):
                matches.append(str(object_id))
                break
    return matches[0] if len(set(matches)) == 1 else ""


def _word_stem(word: str) -> str:
    """Return a conservative Russian noun stem for semantic owner hints only.

    This helper is deliberately not used for deterministic structured owner
    binding. It only lets obvious inflection variants such as
    ``проборазделка`` / ``проборазделки`` produce AMBIGUOUS instead of UNBOUND.
    """
    token = _norm(word)
    if len(token) < 8:
        return token
    for suffix in ("ами", "ями", "ого", "ему", "ому", "ах", "ях", "ов", "ев", "ей", "ам", "ям", "ом", "ем", "а", "я", "ы", "и", "у", "ю", "е", "о"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 7:
            return token[: -len(suffix)]
    return token


def _alias_semantically_present(alias: str, fragment: str) -> bool:
    alias_norm = _norm(alias)
    fragment_norm = _norm(fragment)
    if not alias_norm:
        return False
    if alias_norm in fragment_norm:
        return True

    alias_words = [word for word in re.findall(r"[a-zа-я0-9-]+", alias_norm) if len(word) >= 8]
    fragment_words = re.findall(r"[a-zа-я0-9-]+", fragment_norm)
    if not alias_words or not fragment_words:
        return False

    fragment_stems = {_word_stem(word) for word in fragment_words if len(word) >= 8}
    alias_stems = {_word_stem(word) for word in alias_words}
    return bool(alias_stems and alias_stems <= fragment_stems)


def _semantic_owner_candidates(
    fragment: str,
    known_objects: Mapping[str, tuple[str, ...]],
) -> list[str]:
    matches: list[str] = []
    for object_id, aliases in known_objects.items():
        if any(_alias_semantically_present(alias, fragment) for alias in aliases):
            matches.append(str(object_id))
    return sorted(set(matches))


def bind_evidence(
    requirement: Requirement25,
    evidence: Evidence25,
    known_objects: Mapping[str, tuple[str, ...]],
) -> Binding25:
    metadata = dict(evidence.metadata or {})
    binding_id = _binding_id(requirement, evidence)
    required_parameter = str(requirement.parameter_code or "").strip().upper()
    evidence_parameter = str(
        metadata.get("parameter_code")
        or metadata.get("typed_parameter_code")
        or metadata.get("project_parameter_code")
        or ""
    ).strip().upper()

    explicit_owner_id = str(metadata.get("owner_id") or metadata.get("object_id") or "").strip()
    explicit_owner_name = str(metadata.get("owner_name") or metadata.get("object_name") or "").strip()
    resolved_owner = explicit_owner_id or _resolve_owner_name(explicit_owner_name, known_objects)

    if required_parameter and evidence_parameter and evidence_parameter != required_parameter:
        return Binding25(
            binding_id=binding_id,
            evidence_id=evidence.evidence_id,
            state=BindingState.REJECTED,
            owner_id=resolved_owner,
            parameter_code=evidence_parameter,
            method="STRUCTURED_PARAMETER",
            reason="Evidence represents a different engineering parameter.",
            reason_code="PARAMETER_CONFLICT",
            metadata={"required_parameter": required_parameter, "evidence_parameter": evidence_parameter},
        )

    if requirement.scope is Scope.PROJECT_GLOBAL:
        return Binding25(
            binding_id=binding_id,
            evidence_id=evidence.evidence_id,
            state=BindingState.BOUND,
            owner_id="PROJECT",
            parameter_code=evidence_parameter or required_parameter,
            method="PROJECT_GLOBAL_CONTRACT",
            reason="Requirement contract explicitly declares project-global ownership.",
            reason_code="PROJECT_GLOBAL_BOUND",
        )

    target_owner = str(requirement.target_object_id or "").strip()
    if requirement.scope is not Scope.OBJECT_SPECIFIC or not target_owner:
        return Binding25(
            binding_id=binding_id,
            evidence_id=evidence.evidence_id,
            state=BindingState.UNBOUND,
            owner_id=resolved_owner,
            parameter_code=evidence_parameter or required_parameter,
            method="NO_OWNER_CONTRACT",
            reason="Requirement ownership is unresolved.",
            reason_code="OWNER_SCOPE_UNRESOLVED",
        )

    if explicit_owner_id or explicit_owner_name:
        if not resolved_owner:
            return Binding25(
                binding_id=binding_id,
                evidence_id=evidence.evidence_id,
                state=BindingState.UNBOUND,
                parameter_code=evidence_parameter or required_parameter,
                method="STRUCTURED_OWNER",
                reason="Structured owner metadata could not be resolved to a known project object.",
                reason_code="OWNER_NOT_RESOLVED",
            )
        if resolved_owner != target_owner:
            return Binding25(
                binding_id=binding_id,
                evidence_id=evidence.evidence_id,
                state=BindingState.REJECTED,
                owner_id=resolved_owner,
                parameter_code=evidence_parameter or required_parameter,
                method="STRUCTURED_OWNER_PARAMETER",
                reason="Evidence belongs to a different engineering object.",
                reason_code="OWNER_CONFLICT",
                metadata={"required_owner": target_owner, "evidence_owner": resolved_owner},
            )
        if required_parameter and not evidence_parameter:
            return Binding25(
                binding_id=binding_id,
                evidence_id=evidence.evidence_id,
                state=BindingState.UNBOUND,
                owner_id=resolved_owner,
                parameter_code="",
                method="STRUCTURED_OWNER",
                reason="Owner is proven but parameter identity is not proven.",
                reason_code="PARAMETER_NOT_PROVEN",
            )
        return Binding25(
            binding_id=binding_id,
            evidence_id=evidence.evidence_id,
            state=BindingState.BOUND,
            owner_id=resolved_owner,
            parameter_code=evidence_parameter or required_parameter,
            method="STRUCTURED_OWNER_PARAMETER",
            reason="Structured owner and engineering parameter match the requirement contract.",
            reason_code="OWNER_PARAMETER_BOUND",
        )

    semantic_owners = _semantic_owner_candidates(evidence.fragment, known_objects)
    if len(semantic_owners) == 1:
        semantic_owner = semantic_owners[0]
        if semantic_owner != target_owner:
            return Binding25(
                binding_id=binding_id,
                evidence_id=evidence.evidence_id,
                state=BindingState.REJECTED,
                owner_id=semantic_owner,
                parameter_code=evidence_parameter or required_parameter,
                method="SEMANTIC_OWNER_HINT",
                reason="Evidence text points to a different known object; semantic hints cannot override ownership.",
                reason_code="OWNER_CONFLICT",
            )
        return Binding25(
            binding_id=binding_id,
            evidence_id=evidence.evidence_id,
            state=BindingState.AMBIGUOUS,
            owner_id=semantic_owner,
            parameter_code=evidence_parameter or required_parameter,
            method="SEMANTIC_OWNER_HINT",
            reason="Semantic owner hint matches the target, but structured ownership evidence is absent.",
            reason_code="OWNER_SEMANTIC_ONLY",
        )

    if len(semantic_owners) > 1:
        return Binding25(
            binding_id=binding_id,
            evidence_id=evidence.evidence_id,
            state=BindingState.AMBIGUOUS,
            parameter_code=evidence_parameter or required_parameter,
            method="SEMANTIC_OWNER_HINT",
            reason="Evidence mentions multiple known objects.",
            reason_code="OWNER_AMBIGUOUS",
            metadata={"owner_candidates": semantic_owners},
        )

    return Binding25(
        binding_id=binding_id,
        evidence_id=evidence.evidence_id,
        state=BindingState.UNBOUND,
        parameter_code=evidence_parameter or required_parameter,
        method="NO_OWNER_EVIDENCE",
        reason="No deterministic owner evidence was found for an object-specific requirement.",
        reason_code="OWNER_NOT_PROVEN",
    )
