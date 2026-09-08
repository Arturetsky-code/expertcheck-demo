"""ExpertCheck 20.0 canonical engineering core.

This package is intentionally isolated from the legacy core during migration.
Legacy 18.x remains the executable baseline until parity gates are satisfied.
"""

from .model import (
    CanonicalProject, Comparison, Evidence, Finding, ProjectObject,
    PropertyValue, Requirement, ValidationIssue, stable_id,
)
from .verification import (
    ENGINE_VERSION, EvidenceAssessment, VerificationDecision,
    VerificationEngine20, VerificationRequest,
)

__all__ = [
    "CanonicalProject", "Comparison", "Evidence", "Finding", "ProjectObject",
    "PropertyValue", "Requirement", "ValidationIssue", "stable_id",
    "ENGINE_VERSION", "EvidenceAssessment", "VerificationDecision",
    "VerificationEngine20", "VerificationRequest",
]

__version__ = "20.0-alpha3-canonical-proof"
