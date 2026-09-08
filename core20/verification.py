from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .model import CanonicalProject, Comparison, Requirement, stable_id


ENGINE_VERSION = "20.0-alpha2-verification-engine"

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


class VerificationEngine20:
    """Typed, fail-closed verification over CanonicalProject.

    Alpha 2 is intentionally observational. It reads canonical state and returns
    decisions without mutating the project or replacing legacy 18.x verdicts.
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
        return {
            "version": ENGINE_VERSION,
            "mode": "OBSERVATIONAL_DUAL_RUN",
            "requests": len(requests),
            "decisions": len(decisions),
            "automatic_verdict_eligible": automatic,
            "automatic_coverage_pct": round(100.0 * automatic / max(1, len(decisions)), 1),
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

    def _verify_comparison(
        self,
        request: VerificationRequest,
        assessment: EvidenceAssessment,
    ) -> VerificationDecision:
        comparison = self.project.comparisons[request.comparison_id or ""]
        proof = str(comparison.proof_kind or "").upper()

        if not assessment.has_addressable_evidence:
            return self._decision(
                request,
                "SYSTEM_LIMITATION",
                "Нет адресного доказательства с документом и страницей.",
                assessment,
            )

        # A conflict is a fact about disagreement between sources. It does not
        # imply that ExpertCheck knows which value is correct.
        if comparison.conflict_confirmed:
            if len(assessment.trusted_ids) >= 2 and len(assessment.independent_sections) >= 2:
                return self._decision(
                    request,
                    "PROJECT_FINDING",
                    "Конфликт подтверждён двумя независимыми доверенными адресными источниками.",
                    assessment,
                    automatic=True,
                    conflict_confirmed=True,
                    correct_value_verified=bool(comparison.correct_value_verified),
                )
            return self._decision(
                request,
                "REVIEW_QUESTION",
                "Конфликт отмечен, но канонической доказательной базы недостаточно для автоматического замечания.",
                assessment,
                conflict_confirmed=True,
                correct_value_verified=False,
            )

        agreement_proofs = {"STRUCTURED_AGREEMENT", "STRUCTURED_COMPARISON"}
        if proof in agreement_proofs:
            if len(assessment.trusted_ids) >= 2 and len(assessment.independent_sections) >= 2:
                return self._decision(
                    request,
                    "VERIFIED_OK",
                    "Значение подтверждено независимыми доверенными адресными источниками.",
                    assessment,
                    automatic=True,
                )
            return self._decision(
                request,
                "REVIEW_QUESTION",
                "Совпадение найдено, но не выполнен контракт независимости доверенных источников.",
                assessment,
            )

        return self._decision(
            request,
            "REVIEW_QUESTION",
            "Есть адресные доказательства, но тип доказательства не закрывает автоматический инженерный вердикт.",
            assessment,
        )

    def _verify_requirement(
        self,
        request: VerificationRequest,
        assessment: EvidenceAssessment,
    ) -> VerificationDecision:
        requirement = self.project.requirements[request.requirement_id or ""]
        linked = [
            finding
            for finding in self.project.findings.values()
            if finding.requirement_id == requirement.requirement_id
        ]
        linked_kinds = {finding.kind for finding in linked}
        effective_level = _min_level(
            assessment.evidence_level,
            requirement.evidence_level or assessment.evidence_level,
        )

        if not assessment.has_addressable_evidence:
            return self._decision(
                request,
                "SYSTEM_LIMITATION",
                "Требование не имеет адресного доказательства; вывод о проекте запрещён.",
                assessment,
                evidence_level=effective_level,
            )

        if "PROJECT_FINDING" in linked_kinds:
            return self._decision(
                request,
                "PROJECT_FINDING",
                "Несоответствие уже связано с каноническим требованием и адресным доказательством.",
                assessment,
                evidence_level=effective_level,
                automatic=True,
            )

        if "VERIFIED_OK" in linked_kinds:
            if _level_rank(effective_level) >= 3:
                return self._decision(
                    request,
                    "VERIFIED_OK",
                    "Соответствие связано с каноническим требованием и достаточным адресным доказательством.",
                    assessment,
                    evidence_level=effective_level,
                    automatic=True,
                )
            return self._decision(
                request,
                "REVIEW_QUESTION",
                "Соответствие заявлено, но доказательный уровень ниже минимального автоматического порога L3.",
                assessment,
                evidence_level=effective_level,
            )

        if "REVIEW_QUESTION" in linked_kinds:
            return self._decision(
                request,
                "REVIEW_QUESTION",
                "Каноническая проверка требует инженерного решения специалиста.",
                assessment,
                evidence_level=effective_level,
            )

        return self._decision(
            request,
            "REVIEW_QUESTION",
            "Есть адресные доказательства, но отсутствует закрывающий канонический вывод.",
            assessment,
            evidence_level=effective_level,
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
    ) -> VerificationDecision:
        if kind not in VERIFICATION_KINDS:
            kind = "SYSTEM_LIMITATION"
            automatic = False
            reason = "Движок получил неизвестный тип результата; автоматический вердикт заблокирован."
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
            metadata={
                "domain": request.domain,
                "parameter_code": request.parameter_code,
                "independent_trusted_sources": len(assessment.trusted_ids),
                "independent_sections": list(assessment.independent_sections),
            },
        )
