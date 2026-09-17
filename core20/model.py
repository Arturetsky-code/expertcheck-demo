from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha1
import json
from typing import Any, Iterable


CANONICAL_SCHEMA_VERSION = "20.0.0-alpha1"


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().replace("ё", "е").casefold().split())


def stable_id(prefix: str, *parts: Any) -> str:
    payload = "|".join(_norm(part) for part in parts if str(part or "").strip())
    digest = sha1(payload.encode("utf-8", "ignore")).hexdigest()[:16].upper()
    return f"{prefix}-{digest}"


@dataclass(slots=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "ERROR"
    entity_id: str = ""


@dataclass(slots=True)
class Evidence:
    evidence_id: str
    document_id: str = ""
    document_name: str = ""
    section: str = ""
    page: int | None = None
    table_id: str = ""
    row_id: str = ""
    fragment: str = ""
    source_kind: str = ""
    addressable: bool = False
    trusted: bool = False
    confidence: float | None = None
    confidence_kind: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def address(self) -> str:
        parts = [self.document_name or self.document_id]
        if self.page is not None:
            parts.append(f"стр. {self.page}")
        if self.table_id:
            parts.append(f"табл. {self.table_id}")
        if self.row_id:
            parts.append(f"строка {self.row_id}")
        return " · ".join(part for part in parts if part)


@dataclass(slots=True)
class ProjectObject:
    object_id: str
    name: str
    genplan_position: str = ""
    object_kind: str = ""
    lifecycle: str = ""
    included: bool = True
    parent_object_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PropertyValue:
    property_id: str
    object_id: str
    parameter_code: str
    parameter_name: str
    value: float | str | None
    value_text: str = ""
    unit: str = ""
    semantic_level: str = ""
    binding_status: str = ""
    physical_row_key: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Requirement:
    requirement_id: str
    domain: str
    text: str
    applicable: bool | None = None
    target_object_id: str | None = None
    expected_parameter_code: str = ""
    expected_evidence_route: list[str] = field(default_factory=list)
    required_slots: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    verification_kind: str = ""
    evidence_level: str = "L0"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Comparison:
    comparison_id: str
    object_id: str
    parameter_code: str
    parameter_name: str = ""
    unit: str = ""
    property_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    status: str = ""
    proof_kind: str = ""
    conflict_confirmed: bool = False
    correct_value_verified: bool = False
    evidence_level: str = "L0"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Finding:
    finding_id: str
    kind: str
    title: str
    object_id: str | None = None
    parameter_code: str = ""
    severity: str = ""
    state: str = ""
    evidence_level: str = "L0"
    reason: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    requirement_id: str | None = None
    comparison_id: str | None = None
    trace_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalProject:
    project_id: str
    name: str
    schema_version: str = CANONICAL_SCHEMA_VERSION
    objects: dict[str, ProjectObject] = field(default_factory=dict)
    properties: dict[str, PropertyValue] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    requirements: dict[str, Requirement] = field(default_factory=dict)
    comparisons: dict[str, Comparison] = field(default_factory=dict)
    findings: dict[str, Finding] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def stats(self) -> dict[str, int]:
        return {
            "objects": sum(1 for item in self.objects.values() if item.included),
            "object_candidates": len(self.objects),
            "properties": len(self.properties),
            "evidence": len(self.evidence),
            "requirements": len(self.requirements),
            "comparisons": len(self.comparisons),
            "findings": sum(1 for item in self.findings.values() if item.kind == "PROJECT_FINDING"),
            "review_questions": sum(1 for item in self.findings.values() if item.kind == "REVIEW_QUESTION"),
            "verified_ok": sum(1 for item in self.findings.values() if item.kind == "VERIFIED_OK"),
            "system_limitations": sum(1 for item in self.findings.values() if item.kind == "SYSTEM_LIMITATION"),
        }

    def object_properties(self, object_id: str) -> list[PropertyValue]:
        return [item for item in self.properties.values() if item.object_id == object_id]

    def object_findings(self, object_id: str) -> list[Finding]:
        return [item for item in self.findings.values() if item.object_id == object_id]

    def validate(self) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for obj in self.objects.values():
            if not obj.name.strip():
                issues.append(ValidationIssue("OBJECT_NAME_EMPTY", "У объекта отсутствует наименование.", entity_id=obj.object_id))
            if obj.parent_object_id and obj.parent_object_id not in self.objects:
                issues.append(ValidationIssue("OBJECT_PARENT_MISSING", "Родительский объект отсутствует в canonical model.", entity_id=obj.object_id))
            for evidence_id in obj.evidence_ids:
                if evidence_id not in self.evidence:
                    issues.append(ValidationIssue("OBJECT_EVIDENCE_MISSING", f"Не найдено evidence {evidence_id}.", entity_id=obj.object_id))

        for prop in self.properties.values():
            if prop.object_id not in self.objects:
                issues.append(ValidationIssue("PROPERTY_OBJECT_MISSING", "Показатель ссылается на отсутствующий объект.", entity_id=prop.property_id))
            if not prop.parameter_code:
                issues.append(ValidationIssue("PROPERTY_CODE_EMPTY", "У показателя отсутствует parameter_code.", entity_id=prop.property_id))
            for evidence_id in prop.evidence_ids:
                if evidence_id not in self.evidence:
                    issues.append(ValidationIssue("PROPERTY_EVIDENCE_MISSING", f"Не найдено evidence {evidence_id}.", entity_id=prop.property_id))

        for req in self.requirements.values():
            if req.target_object_id and req.target_object_id not in self.objects:
                issues.append(ValidationIssue("REQUIREMENT_OBJECT_MISSING", "Требование ссылается на отсутствующий объект.", entity_id=req.requirement_id))

        for cmp in self.comparisons.values():
            if cmp.object_id not in self.objects:
                issues.append(ValidationIssue("COMPARISON_OBJECT_MISSING", "Сверка ссылается на отсутствующий объект.", entity_id=cmp.comparison_id))
            for property_id in cmp.property_ids:
                if property_id not in self.properties:
                    issues.append(ValidationIssue("COMPARISON_PROPERTY_MISSING", f"Не найден property {property_id}.", entity_id=cmp.comparison_id))

        for finding in self.findings.values():
            if finding.object_id and finding.object_id not in self.objects:
                issues.append(ValidationIssue("FINDING_OBJECT_MISSING", "Finding ссылается на отсутствующий объект.", entity_id=finding.finding_id))
            if finding.requirement_id and finding.requirement_id not in self.requirements:
                issues.append(ValidationIssue("FINDING_REQUIREMENT_MISSING", "Finding ссылается на отсутствующее требование.", entity_id=finding.finding_id))
            if finding.comparison_id and finding.comparison_id not in self.comparisons:
                issues.append(ValidationIssue("FINDING_COMPARISON_MISSING", "Finding ссылается на отсутствующую сверку.", entity_id=finding.finding_id))
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fingerprint(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, default=str, separators=(',', ':'))
        return sha1(payload.encode("utf-8", "ignore")).hexdigest()

    def add_evidence(self, item: Evidence) -> Evidence:
        self.evidence[item.evidence_id] = item
        return item

    def add_object(self, item: ProjectObject) -> ProjectObject:
        self.objects[item.object_id] = item
        return item

    def add_property(self, item: PropertyValue) -> PropertyValue:
        self.properties[item.property_id] = item
        return item

    def add_requirement(self, item: Requirement) -> Requirement:
        self.requirements[item.requirement_id] = item
        return item

    def add_comparison(self, item: Comparison) -> Comparison:
        self.comparisons[item.comparison_id] = item
        return item

    def add_finding(self, item: Finding) -> Finding:
        self.findings[item.finding_id] = item
        return item
