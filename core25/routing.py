from __future__ import annotations

from dataclasses import dataclass

from .contracts import Requirement25, Scope


@dataclass(frozen=True, slots=True)
class VerificationRoute:
    kind: str
    scope: Scope
    expected_sections: tuple[str, ...]
    parameter_code: str
    requires_owner: bool
    requires_addressable_evidence: bool
    prefer_structured_source: bool = False


_SUPPORTED = {
    "TYPED_VALUE": "TYPED_VALUE",
    "PRESENCE": "PRESENCE",
    "RESERVE_TOPOLOGY": "RESERVE_TOPOLOGY",
    "TABLE_CELL_VALUE": "TYPED_VALUE",
    # 25.2 Coverage Breakthrough executors. These routes remain fail-closed:
    # only addressable candidates admitted by the matching proof routine can
    # become categorical.
    "NEGATIVE_ASSERTION": "NEGATIVE_ASSERTION",
    "NORMATIVE_ASSERTION": "NORMATIVE_ASSERTION",
}


def route_requirement(requirement: Requirement25) -> VerificationRoute:
    raw_kind = str(requirement.verification_kind or "").strip().upper()
    kind = _SUPPORTED.get(raw_kind, "REVIEW_ONLY")
    review_only = kind == "REVIEW_ONLY"
    requires_owner = bool(
        not review_only
        and requirement.scope is Scope.OBJECT_SPECIFIC
    )
    return VerificationRoute(
        kind=kind,
        scope=requirement.scope,
        expected_sections=tuple(requirement.expected_sections),
        parameter_code=str(requirement.parameter_code or "").strip().upper(),
        requires_owner=requires_owner,
        requires_addressable_evidence=not review_only,
        prefer_structured_source=raw_kind == "TABLE_CELL_VALUE",
    )
