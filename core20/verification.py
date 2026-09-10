from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isclose
import re
from typing import Any, Iterable

from .model import CanonicalProject, Comparison, Requirement, stable_id
from .requirement_verification import reconstruct_requirement_proof


ENGINE_VERSION = "20.0-alpha8-normative-execution"

VERIFICATION_KINDS = {
    "VERIFIED_OK",
    "PROJECT_FINDING",
    "REVIEW_QUESTION",
    "SYSTEM_LIMITATION",
    "INFORMATIONAL",
}

KIND_STATES = {
    "VERIFIED_OK": "Соответствует",
    "PROJECT_FINDING": "Выявлено несоответствие",
    "REVIEW_QUESTION": "Требует проверки специалистом",
    "SYSTEM_LIMITATION": "Не проверено автоматически",
    "INFORMATIONAL": "Информация",
}


@dataclass(slots=True)
class VerificationRequest:
    verification_id: str
    domain: str
    claim: str
    object_id: str | None = None
    parameter_code: str = ""
    requirement_id: str | None = None
    comparison_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    required_evidence_level: str = "L0"
    expected_evidence_route: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvidenceAssessment:
    evidence_ids: list[str] = field(default_factory=list)
    addressable_ids: list[str] = field(default_factory=list)
    trusted_ids: list[str] = field(default_factory=list)
    independent_sections: list[str] = field(default_factory=list)
    missing_ids: list[str] = field(default_factory=list)
    evidence_level: str = "L0"

    @property
    def has_addressable_evidence(self) -> bool:
        return bool(self.addressable_ids)

    @property
    def independent_trusted_count(self) -> int:
        return len(self.trusted_ids)


@dataclass(slots=True)
class VerificationDecision:
    verification_id: str
    kind: str
    state: str
    reason: str
    evidence_level: str = "L0"
    evidence_ids: list[str] = field(default_factory=list)
    trace_ids: list[str] = field(default_factory=list)
    automatic_verdict_eligible: bool = False
    conflict_confirmed: bool = False
    correct_value_verified: bool = False
    contract_violations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _level_rank(level: str) -> int:
    try:
        return int(str(level or "L0").strip().upper().replace("L", ""))
    except ValueError:
        return 0


def _min_level(current: str, maximum: str) -> str:
    return current if _level_rank(current) <= _level_rank(maximum) else maximum


def _numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip().replace("\xa0", " ").replace(",", ".")
    if not text:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _unit(value: Any) -> str:
    text = str(value or "").strip().casefold()
    text = text.replace("²", "2").replace("^2", "2").replace(" ", "")
    aliases = {
        "м2": "m2", "m²": "m2", "м.кв.": "m2", "кв.м": "m2",
        "m2": "m2", "sqm": "m2",
        "м3": "m3", "м³": "m3", "m3": "m3",
        "мм": "mm", "mm": "mm",
        "см": "cm", "cm": "cm",
        "м": "m", "m": "m",
        "квт": "kw", "kw": "kw",
        "мпа": "mpa", "mpa": "mpa",
    }
    return aliases.get(text, text)


class VerificationEngine20:
    """Fail-closed verification over CanonicalProject.

    Alpha 6 keeps the accepted Assignment contracts and adds independent
    normative verification over verified clauses, applicability and canonical
    project evidence. Normative checks remain fail-closed whenever clause,
    applicability or evidence contracts are incomplete. Legacy proof flags are
    parity diagnostics only.
    """

    def __init__(self, project: CanonicalProject):
        self.project = project

    def build_requests(self) -> list[VerificationRequest]:
        requests: list[VerificationRequest] = []
        for comparison in self.project.comparisons.values():
            requests.append(self._comparison_request(comparison))
        for requirement in self.project.requirements.values():
            requests.append(self._requirement_request(requirement))
        return requests

    def run(self) -> dict[str, Any]:
        requests = self.build_requests()
        decisions = [self.verify(request) for request in requests]
        contract_errors = [
            violation
            for decision in decisions
            for violation in decision.contract_violations
        ]
        counts = {
            kind: sum(1 for decision in decisions if decision.kind == kind)
            for kind in sorted(VERIFICATION_KINDS)
        }
        automatic = sum(1 for decision in decisions if decision.automatic_verdict_eligible)
        canonical_recomputed = sum(
            1 for decision in decisions
            if decision.metadata.get("proof_source") == "CANONICAL_RECOMPUTED"
        )
        legacy_disagreements = sum(
            1 for decision in decisions
            if decision.metadata.get("legacy_disagreement")
        )
        requirement_recomputed = sum(
            1 for decision in decisions
            if decision.metadata.get("proof_source") in {
                "CANONICAL_REQUIREMENT_RECONSTRUCTION",
                "CANONICAL_NORMATIVE_RECONSTRUCTION",
            }
            and decision.metadata.get("canonical_requirement_state") in {"COMPLIANT","NONCOMPLIANT"}
        )
        assignment_recomputed = sum(
            1 for decision in decisions
            if decision.metadata.get("proof_source") == "CANONICAL_REQUIREMENT_RECONSTRUCTION"
            and str(decision.metadata.get("domain") or "").casefold() == "assignment"
            and decision.metadata.get("canonical_requirement_state") in {"COMPLIANT","NONCOMPLIANT"}
        )
        normative_guarded = sum(
            1 for decision in decisions
            if str(decision.metadata.get("domain") or "").casefold() == "normative"
        )
        normative_verified_clauses = sum(
            1 for decision in decisions
            if str(decision.metadata.get("domain") or "").casefold() == "normative"
            and bool(decision.metadata.get("verified_clause"))
        )
        normative_auto = sum(
            1 for decision in decisions
            if str(decision.metadata.get("domain") or "").casefold() == "normative"
            and decision.automatic_verdict_eligible
        )
        normative_structure_auto = sum(
            1 for decision in decisions
            if decision.automatic_verdict_eligible
            and decision.metadata.get("canonical_reason_code") == "NORMATIVE_STRUCTURE_VERIFIED"
        )
        normative_review = sum(
            1 for decision in decisions
            if str(decision.metadata.get("domain") or "").casefold() == "normative"
            and decision.kind == "REVIEW_QUESTION"
        )
        normative_unverified = sum(
            1 for decision in decisions
            if decision.metadata.get("canonical_reason_code") == "NORMATIVE_CLAUSE_NOT_VERIFIED"
        )
        normative_applicability_blocked = sum(
            1 for decision in decisions
            if decision.metadata.get("canonical_reason_code") == "NORMATIVE_APPLICABILITY_NOT_PROVEN"
        )
        typed_assignment_auto = sum(
            1 for decision in decisions
            if decision.automatic_verdict_eligible
            and decision.metadata.get("canonical_reason_code") in {
                "ASSIGNMENT_TYPED_VALUE_MATCH","ASSIGNMENT_TYPED_VALUE_MISMATCH"
            }
        )
        reserve_topology_auto = sum(
            1 for decision in decisions
            if decision.automatic_verdict_eligible
            and decision.metadata.get("canonical_reason_code") in {
                "RESERVE_TOPOLOGY_MATCH","RESERVE_TOPOLOGY_MISMATCH"
            }
        )
        parameter_binding_blocked = sum(
            1 for decision in decisions
            if decision.metadata.get("canonical_reason_code") == "PARAMETER_BINDING_NOT_PROVEN"
        )
        canonical_routed_evidence = sum(
            1 for evidence in self.project.evidence.values()
            if bool((evidence.metadata or {}).get("canonical_routed"))
        )
        return {
            "version": ENGINE_VERSION,
            "mode": "OBSERVATIONAL_DUAL_RUN",
            "requests": len(requests),
            "decisions": len(decisions),
            "automatic_verdict_eligible": automatic,
            "automatic_coverage_pct": round(100.0 * automatic / max(1, len(decisions)), 1),
            "canonical_proofs_recomputed": canonical_recomputed,
            "canonical_requirement_proofs_recomputed": requirement_recomputed,
            "assignment_proofs_recomputed": assignment_recomputed,
            "normative_checks_guarded": normative_guarded,
            "normative_verified_clauses": normative_verified_clauses,
            "normative_auto": normative_auto,
            "normative_structure_auto": normative_structure_auto,
            "normative_review": normative_review,
            "normative_unverified": normative_unverified,
            "normative_applicability_blocked": normative_applicability_blocked,
            "typed_assignment_auto": typed_assignment_auto,
            "reserve_topology_auto": reserve_topology_auto,
            "parameter_binding_blocked": parameter_binding_blocked,
            "canonical_routed_evidence": canonical_routed_evidence,
            "legacy_disagreements": legacy_disagreements,
            "contract_errors": len(contract_errors),
            "counts": counts,
            "decision_rows": [decision.to_dict() for decision in decisions],
        }

    def verify(self, request: VerificationRequest) -> VerificationDecision:
        contract_violations = self._validate_request(request)
        assessment = self._assess_evidence(request.evidence_ids)

        if assessment.missing_ids:
            contract_violations.extend(
                f"EVIDENCE_REF_MISSING:{evidence_id}" for evidence_id in assessment.missing_ids
            )

        if contract_violations:
            return self._decision(
                request,
                "SYSTEM_LIMITATION",
                "Нарушен канонический контракт проверки; автоматический вердикт заблокирован.",
                assessment,
                contract_violations=contract_violations,
            )

        if request.comparison_id:
            return self._verify_comparison(request, assessment)
        if request.requirement_id:
            return self._verify_requirement(request, assessment)

        return self._decision(
            request,
            "SYSTEM_LIMITATION",
            "Для типа проверки отсутствует исполняемый канонический маршрут.",
            assessment,
        )

    def _comparison_request(self, comparison: Comparison) -> VerificationRequest:
        object_name = self.project.objects.get(comparison.object_id)
        title = object_name.name if object_name else comparison.object_id
        return VerificationRequest(
            verification_id=stable_id("VER", "comparison", comparison.comparison_id),
            domain="comparison",
            claim=f"{title}: {comparison.parameter_name or comparison.parameter_code}",
            object_id=comparison.object_id,
            parameter_code=comparison.parameter_code,
            comparison_id=comparison.comparison_id,
            evidence_ids=list(comparison.evidence_ids),
            required_evidence_level=comparison.evidence_level or "L0",
            metadata={
                "proof_kind": comparison.proof_kind,
                "status": comparison.status,
                "conflict_confirmed": comparison.conflict_confirmed,
                "correct_value_verified": comparison.correct_value_verified,
                "legacy_verification_kind": comparison.metadata.get("verification_kind", ""),
            },
        )

    def _requirement_request(self, requirement: Requirement) -> VerificationRequest:
        linked = [
            finding
            for finding in self.project.findings.values()
            if finding.requirement_id == requirement.requirement_id
        ]
        evidence_ids = list(requirement.evidence_ids)
        for finding in linked:
            for evidence_id in finding.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)
        return VerificationRequest(
            verification_id=stable_id("VER", "requirement", requirement.requirement_id),
            domain=requirement.domain or "requirement",
            claim=requirement.text,
            object_id=requirement.target_object_id,
            parameter_code=requirement.expected_parameter_code,
            requirement_id=requirement.requirement_id,
            evidence_ids=evidence_ids,
            required_evidence_level=requirement.evidence_level or "L0",
            expected_evidence_route=list(requirement.expected_evidence_route),
            metadata={
                "verification_kind": requirement.verification_kind,
                "linked_finding_ids": [finding.finding_id for finding in linked],
                "linked_kinds": [finding.kind for finding in linked],
            },
        )

    def _assess_evidence(self, evidence_ids: Iterable[str]) -> EvidenceAssessment:
        ids = list(dict.fromkeys(str(item) for item in evidence_ids if str(item).strip()))
        existing = [self.project.evidence[item] for item in ids if item in self.project.evidence]
        missing = [item for item in ids if item not in self.project.evidence]
        addressable = [item.evidence_id for item in existing if item.addressable]
        trusted = [item.evidence_id for item in existing if item.addressable and item.trusted]
        sections = sorted({
            (item.section or item.document_name or item.document_id).strip()
            for item in existing
            if item.addressable and item.trusted and (item.section or item.document_name or item.document_id).strip()
        })

        if len(trusted) >= 2 and len(sections) >= 2:
            level = "L5"
        elif trusted:
            level = "L4"
        elif addressable:
            level = "L3"
        elif existing:
            level = "L1"
        else:
            level = "L0"

        return EvidenceAssessment(
            evidence_ids=[item.evidence_id for item in existing],
            addressable_ids=addressable,
            trusted_ids=trusted,
            independent_sections=sections,
            missing_ids=missing,
            evidence_level=level,
        )

    def _canonical_comparison_proof(
        self,
        comparison: Comparison,
        assessment: EvidenceAssessment,
    ) -> dict[str, Any]:
        facts: list[dict[str, Any]] = []
        target_unit = _unit(comparison.unit)

        for evidence_id in assessment.trusted_ids:
            evidence = self.project.evidence[evidence_id]
            meta = evidence.metadata or {}
            bound_object = str(
                meta.get("comparison_object_id")
                or meta.get("observed_object_id")
                or ""
            ).strip()
            bound_parameter = str(
                meta.get("comparison_parameter_code")
                or meta.get("observed_parameter_code")
                or ""
            ).strip()
            if bound_object and bound_object != comparison.object_id:
                continue
            if bound_parameter and bound_parameter != comparison.parameter_code:
                continue

            value = _numeric(meta.get("observed_value"))
            if value is None:
                value = _numeric(meta.get("observed_value_text"))
            if value is None:
                continue

            unit = _unit(
                meta.get("observed_unit")
                or meta.get("comparison_unit")
                or comparison.unit
            )
            facts.append({
                "evidence_id": evidence_id,
                "section": evidence.section or evidence.document_name or evidence.document_id,
                "value": value,
                "unit": unit or target_unit,
            })

        independent = {
            str(fact["section"]).strip().casefold()
            for fact in facts
            if str(fact["section"]).strip()
        }
        if len(facts) < 2 or len(independent) < 2:
            return {
                "state": "INSUFFICIENT",
                "reason_code": "CANONICAL_VALUES_INSUFFICIENT",
                "facts": facts,
            }

        units = {fact["unit"] for fact in facts if fact["unit"]}
        if len(units) > 1:
            return {
                "state": "INSUFFICIENT",
                "reason_code": "UNIT_CONTRACT_MISMATCH",
                "facts": facts,
            }

        values = [float(fact["value"]) for fact in facts]
        anchor = values[0]
        equal = all(isclose(value, anchor, rel_tol=1e-9, abs_tol=1e-6) for value in values[1:])
        return {
            "state": "AGREEMENT" if equal else "CONFLICT",
            "reason_code": "CANONICAL_AGREEMENT" if equal else "CANONICAL_CONFLICT",
            "facts": facts,
            "values": values,
            "unit": next(iter(units), target_unit),
        }

    def _legacy_disagrees(self, comparison: Comparison, canonical_state: str) -> bool:
        legacy_kind = str(comparison.metadata.get("verification_kind") or "").upper()
        legacy_conflict = bool(comparison.conflict_confirmed) or legacy_kind == "PROJECT_FINDING"
        legacy_ok = legacy_kind == "VERIFIED_OK" or str(comparison.proof_kind or "").upper() == "STRUCTURED_AGREEMENT"
        if canonical_state == "CONFLICT":
            return legacy_ok and not legacy_conflict
        if canonical_state == "AGREEMENT":
            return legacy_conflict
        return False

    def _verify_comparison(
        self,
        request: VerificationRequest,
        assessment: EvidenceAssessment,
    ) -> VerificationDecision:
        comparison = self.project.comparisons[request.comparison_id or ""]

        if not assessment.has_addressable_evidence:
            return self._decision(
                request,
                "SYSTEM_LIMITATION",
                "Нет адресного доказательства с документом и страницей.",
                assessment,
            )

        proof = self._canonical_comparison_proof(comparison, assessment)
        state = proof["state"]
        diagnostic = {
            "proof_source": "CANONICAL_RECOMPUTED" if state in {"AGREEMENT", "CONFLICT"} else "CANONICAL_INSUFFICIENT",
            "canonical_proof_state": state,
            "canonical_reason_code": proof.get("reason_code"),
            "canonical_values": proof.get("values") or [fact["value"] for fact in proof.get("facts", [])],
            "canonical_unit": proof.get("unit") or "",
            "canonical_fact_count": len(proof.get("facts") or []),
            "legacy_proof_kind": comparison.proof_kind,
            "legacy_conflict_confirmed": comparison.conflict_confirmed,
            "legacy_disagreement": self._legacy_disagrees(comparison, state),
        }

        if state == "CONFLICT":
            return self._decision(
                request,
                "PROJECT_FINDING",
                "20.0 независимо пересчитал конфликт по двум адресным доверенным источникам.",
                assessment,
                automatic=True,
                conflict_confirmed=True,
                correct_value_verified=False,
                decision_metadata=diagnostic,
            )

        if state == "AGREEMENT":
            return self._decision(
                request,
                "VERIFIED_OK",
                "20.0 независимо пересчитал совпадение по двум адресным доверенным источникам.",
                assessment,
                automatic=True,
                decision_metadata=diagnostic,
            )

        return self._decision(
            request,
            "REVIEW_QUESTION",
            "Адресные evidence есть, но 20.0 не смог независимо восстановить достаточный числовой proof; legacy-флаг не используется как автоматическое доказательство.",
            assessment,
            decision_metadata=diagnostic,
        )

    def _verify_requirement(
        self,
        request: VerificationRequest,
        assessment: EvidenceAssessment,
    ) -> VerificationDecision:
        requirement = self.project.requirements[request.requirement_id or ""]
        proof = reconstruct_requirement_proof(self.project, requirement)
        state = str(proof.get("state") or "LIMITATION").upper()
        effective_level = str(proof.get("evidence_level") or "") or _min_level(
            assessment.evidence_level,
            requirement.evidence_level or assessment.evidence_level,
        )
        legacy_kind = str(requirement.verification_kind or "").upper()
        legacy_disagreement = bool(
            (state == "COMPLIANT" and legacy_kind == "PROJECT_FINDING")
            or (state == "NONCOMPLIANT" and legacy_kind == "VERIFIED_OK")
        )
        diagnostic = {
            "proof_source": proof.get("proof_source") or "CANONICAL_REQUIREMENT_RECONSTRUCTION",
            "canonical_requirement_state": state,
            "canonical_reason_code": proof.get("reason_code") or "",
            "domain": requirement.domain,
            "trusted_requirement_evidence": int(proof.get("trusted_evidence_count") or 0),
            "addressable_requirement_evidence": int(proof.get("addressable_evidence_count") or 0),
            "typed_fact_count": int(proof.get("typed_fact_count") or 0),
            "required_value": proof.get("required_value"),
            "project_value": proof.get("project_value"),
            "required_unit": proof.get("required_unit") or "",
            "required_topology": proof.get("required_topology"),
            "project_topology": proof.get("project_topology"),
            "verified_clause": bool(proof.get("verified_clause")),
            "source_reference": proof.get("source_reference") or "",
            "paragraph": proof.get("paragraph") or "",
            "check_kind": proof.get("check_kind") or "",
            "applicability_state": proof.get("applicability_state") or "",
            "normative_contract": proof.get("normative_contract") or "",
            "normative_requirement_id": proof.get("normative_requirement_id") or "",
            "normative_registry_trust": proof.get("normative_registry_trust") or "",
            "normative_source_status": proof.get("normative_source_status") or "",
            "normative_history_occurrences": int(proof.get("normative_history_occurrences") or 0),
            "normative_history_projects": int(proof.get("normative_history_projects") or 0),
            "normative_history_policy": proof.get("normative_history_policy") or "",
            "required_document_roles": proof.get("required_document_roles") or [],
            "observed_document_roles": proof.get("observed_document_roles") or [],
            "missing_document_roles": proof.get("missing_document_roles") or [],
            "legacy_requirement_kind": requirement.verification_kind,
            "legacy_disagreement": legacy_disagreement,
        }

        if state == "COMPLIANT":
            return self._decision(
                request,
                "VERIFIED_OK",
                str(proof.get("reason") or "Требование канонически подтверждено."),
                assessment,
                automatic=True,
                evidence_level=effective_level,
                decision_metadata=diagnostic,
            )

        if state == "NONCOMPLIANT":
            return self._decision(
                request,
                "PROJECT_FINDING",
                str(proof.get("reason") or "Канонически подтверждено несоответствие требованию."),
                assessment,
                automatic=True,
                correct_value_verified=bool(proof.get("correct_value_verified")),
                evidence_level=effective_level,
                decision_metadata=diagnostic,
            )

        if state == "NOT_APPLICABLE":
            return self._decision(
                request,
                "INFORMATIONAL",
                str(proof.get("reason") or "Требование НТД неприменимо к данному проекту."),
                assessment,
                evidence_level=effective_level,
                decision_metadata=diagnostic,
            )

        if state == "REVIEW":
            return self._decision(
                request,
                "REVIEW_QUESTION",
                str(proof.get("reason") or "Требуется инженерная проверка."),
                assessment,
                evidence_level=effective_level,
                decision_metadata=diagnostic,
            )

        return self._decision(
            request,
            "SYSTEM_LIMITATION",
            str(proof.get("reason") or "Автоматическая проверка требования пока недоступна."),
            assessment,
            evidence_level=effective_level,
            decision_metadata=diagnostic,
        )

    def _validate_request(self, request: VerificationRequest) -> list[str]:
        issues: list[str] = []
        if not request.verification_id:
            issues.append("VERIFICATION_ID_EMPTY")
        if request.object_id and request.object_id not in self.project.objects:
            issues.append("OBJECT_REF_MISSING")
        if request.requirement_id and request.requirement_id not in self.project.requirements:
            issues.append("REQUIREMENT_REF_MISSING")
        if request.comparison_id and request.comparison_id not in self.project.comparisons:
            issues.append("COMPARISON_REF_MISSING")
        if request.requirement_id and request.comparison_id:
            issues.append("AMBIGUOUS_VERIFICATION_TARGET")
        return issues

    def _decision(
        self,
        request: VerificationRequest,
        kind: str,
        reason: str,
        assessment: EvidenceAssessment,
        *,
        automatic: bool = False,
        conflict_confirmed: bool = False,
        correct_value_verified: bool = False,
        contract_violations: list[str] | None = None,
        evidence_level: str | None = None,
        decision_metadata: dict[str, Any] | None = None,
    ) -> VerificationDecision:
        if kind not in VERIFICATION_KINDS:
            kind = "SYSTEM_LIMITATION"
            automatic = False
            reason = "Движок получил неизвестный тип результата; автоматический вердикт заблокирован."
        metadata = {
            "domain": request.domain,
            "parameter_code": request.parameter_code,
            "independent_trusted_sources": len(assessment.trusted_ids),
            "independent_sections": list(assessment.independent_sections),
        }
        metadata.update(decision_metadata or {})
        return VerificationDecision(
            verification_id=request.verification_id,
            kind=kind,
            state=KIND_STATES[kind],
            reason=reason,
            evidence_level=evidence_level or assessment.evidence_level,
            evidence_ids=list(assessment.evidence_ids),
            trace_ids=[
                item
                for item in (request.requirement_id, request.comparison_id, request.object_id)
                if item
            ],
            automatic_verdict_eligible=bool(automatic),
            conflict_confirmed=bool(conflict_confirmed),
            correct_value_verified=bool(correct_value_verified),
            contract_violations=list(contract_violations or []),
            metadata=metadata,
        )
