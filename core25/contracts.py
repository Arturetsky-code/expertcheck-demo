from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Domain(str, Enum):
    ASSIGNMENT = "ASSIGNMENT"
    NORMATIVE = "NORMATIVE"
    CHECKLIST = "CHECKLIST"
    CROSS_SECTION = "CROSS_SECTION"


class Scope(str, Enum):
    PROJECT_GLOBAL = "PROJECT_GLOBAL"
    OBJECT_SPECIFIC = "OBJECT_SPECIFIC"
    UNRESOLVED = "UNRESOLVED"


class DecisionState(str, Enum):
    COMPLIANT = "COMPLIANT"
    NONCOMPLIANT = "NONCOMPLIANT"
    REVIEW = "REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    LIMITATION = "LIMITATION"


class BindingState(str, Enum):
    # 25.0 canonical states
    BOUND = "BOUND"
    AMBIGUOUS = "AMBIGUOUS"
    UNBOUND = "UNBOUND"
    REJECTED = "REJECTED"
    # Compatibility states used by the initial integrity-gate scaffold.
    CANDIDATE = "CANDIDATE"
    PROVEN = "PROVEN"


class ProofState(str, Enum):
    PROVEN_MATCH = "PROVEN_MATCH"
    PROVEN_MISMATCH = "PROVEN_MISMATCH"
    CONFLICT = "CONFLICT"
    INSUFFICIENT = "INSUFFICIENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SYSTEM_LIMITATION = "SYSTEM_LIMITATION"


@dataclass(frozen=True, slots=True)
class Requirement25:
    requirement_id: str
    domain: Domain
    text: str
    scope: Scope = Scope.UNRESOLVED
    verification_kind: str = ""
    target_object_id: str | None = None
    parameter_code: str = ""
    required_value: float | str | None = None
    unit: str = ""
    expected_sections: tuple[str, ...] = ()
    source_document: str = ""
    source_page: int | None = None
    source_fragment: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Evidence25:
    evidence_id: str
    document: str = ""
    document_name: str = ""
    section: str = ""
    page: int | None = None
    table_id: str = ""
    row_id: str = ""
    cell_id: str = ""
    fragment: str = ""
    source_kind: str = ""
    source_role: str = ""
    addressable: bool = False
    canonical: bool = True
    trusted: bool = False
    confidence: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def resolved_document(self) -> str:
        return self.document or self.document_name

    @property
    def proof_eligible(self) -> bool:
        blocked_roles = {"TOC", "TABLE_OF_CONTENTS", "INDEX", "DOCUMENT_TITLE", "FILE_NAME_ONLY"}
        role = (self.source_role or self.source_kind or "").strip().upper()
        return bool(
            self.addressable
            and self.canonical
            and self.resolved_document.strip()
            and isinstance(self.page, int)
            and self.page > 0
            and self.fragment.strip()
            and role not in blocked_roles
        )


@dataclass(frozen=True, slots=True)
class Binding25:
    binding_id: str
    evidence_id: str
    state: BindingState
    owner_id: str = ""
    parameter_code: str = ""
    concept_code: str = ""
    method: str = ""
    reason: str = ""
    reason_code: str = ""
    supporting_evidence_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Proof25:
    proof_id: str
    requirement_id: str
    state: ProofState
    evidence_ids: tuple[str, ...] = ()
    binding_ids: tuple[str, ...] = ()
    reason_code: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def is_categorical(self) -> bool:
        return self.state in {ProofState.PROVEN_MATCH, ProofState.PROVEN_MISMATCH}


@dataclass(frozen=True, slots=True)
class Decision25:
    decision_id: str
    requirement_id: str
    state: DecisionState
    proof: Proof25 | None = None
    proof_id: str = ""
    trace_id: str = ""
    reason_code: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.proof is None:
            return
        if self.proof.requirement_id != self.requirement_id:
            raise ValueError("Decision and proof must reference the same requirement")
        if self.state is DecisionState.COMPLIANT and self.proof.state is not ProofState.PROVEN_MATCH:
            raise ValueError("COMPLIANT requires PROVEN_MATCH")
        if self.state is DecisionState.NONCOMPLIANT and self.proof.state is not ProofState.PROVEN_MISMATCH:
            raise ValueError("NONCOMPLIANT requires PROVEN_MISMATCH")

    @property
    def is_categorical(self) -> bool:
        return self.state in {DecisionState.COMPLIANT, DecisionState.NONCOMPLIANT}

    @property
    def resolved_proof_id(self) -> str:
        return self.proof.proof_id if self.proof is not None else self.proof_id


@dataclass(frozen=True, slots=True)
class Trace25:
    requirement_id: str
    evidence: tuple[Evidence25, ...]
    bindings: tuple[Binding25, ...]
    proof: Proof25
    decision: Decision25
    trace_id: str = ""

    def is_categorical_trace_valid(self) -> bool:
        if not self.decision.is_categorical:
            return True
        if not self.proof.is_categorical:
            return False
        if self.decision.resolved_proof_id and self.decision.resolved_proof_id != self.proof.proof_id:
            return False

        evidence_by_id = {item.evidence_id: item for item in self.evidence}
        if not self.proof.evidence_ids:
            return False
        for evidence_id in self.proof.evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if item is None or not item.proof_eligible:
                return False

        binding_by_id = {item.binding_id: item for item in self.bindings}
        if not self.proof.binding_ids:
            return False
        for binding_id in self.proof.binding_ids:
            item = binding_by_id.get(binding_id)
            if item is None or item.state is not BindingState.BOUND:
                return False
            if item.evidence_id not in evidence_by_id:
                return False
        return True


@dataclass(frozen=True, slots=True)
class VerificationResult25:
    requirement: Requirement25
    trace: Trace25
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def decision(self) -> Decision25:
        return self.trace.decision


# ---------------------------------------------------------------------------
# Compatibility contracts for the initial 25.0 integrity-gate scaffold.
# They remain intentionally small and are kept separate from the canonical
# Requirement25/Evidence25/Binding25/Proof25/Decision25 trace model.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    evidence_id: str
    document_id: str
    page: int | None
    fragment: str
    addressable: bool
    source_kind: str


@dataclass(frozen=True, slots=True)
class Binding:
    binding_id: str
    evidence_id: str
    object_id: str | None
    parameter_code: str | None
    state: BindingState
    reason_code: str = ""


@dataclass(frozen=True, slots=True)
class Proof:
    proof_id: str
    evidence_ids: tuple[str, ...]
    binding_ids: tuple[str, ...]
    valid: bool
    reason_code: str = ""


@dataclass(frozen=True, slots=True)
class Decision:
    state: DecisionState
    reason_code: str
    evidence_ids: tuple[str, ...] = ()
    binding_ids: tuple[str, ...] = ()
    proof_id: str | None = None


@dataclass(frozen=True, slots=True)
class DecisionRequest:
    requested_state: DecisionState
    evidence: tuple[EvidenceRef, ...]
    bindings: tuple[Binding, ...]
    proof: Proof | None
    ownership_required: bool
