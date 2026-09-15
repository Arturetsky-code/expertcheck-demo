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

# Alpha 10 installs a narrow reliability overlay before downstream modules bind
# the normative semantic proof functions.  The Alpha 9 engine remains the
# underlying proof implementation; the overlay only adds cumulative checkpoint
# semantics and exposes the actually pending queue.
from .alpha10_reliability import install as _install_alpha10_reliability

_install_alpha10_reliability()

__all__ = [
    "CanonicalProject", "Comparison", "Evidence", "Finding", "ProjectObject",
    "PropertyValue", "Requirement", "ValidationIssue", "stable_id",
    "ENGINE_VERSION", "EvidenceAssessment", "VerificationDecision",
    "VerificationEngine20", "VerificationRequest",
]

__version__ = "20.0-alpha10-expert-workflow-reliability"
