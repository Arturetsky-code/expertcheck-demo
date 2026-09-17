from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DecisionState(str, Enum):
    COMPLIANT = "COMPLIANT"
    NONCOMPLIANT = "NONCOMPLIANT"
    REVIEW = "REVIEW"
    LIMITATION = "LIMITATION"


class BindingState(str, Enum):
    CANDIDATE = "CANDIDATE"
    PROVEN = "PROVEN"
    REJECTED = "REJECTED"


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
