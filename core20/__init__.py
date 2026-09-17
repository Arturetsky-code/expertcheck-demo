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
# the normative semantic proof functions. The older semantic engine remains the
# underlying implementation; the overlay adds cumulative checkpoint semantics
# and exposes the actually pending queue.
from .alpha10_reliability import install as _install_alpha10_reliability

_install_alpha10_reliability()

# Alpha 10.1.1 tightens evidence quality and exported report integrity: table-of-
# contents pages are not admissible project proof, and exported AI-consensus is
# reconciled with the persisted normative Judge/Critic proof stream.
from .quality_integrity_1011 import install_quality_integrity_1011 as _install_quality_integrity_1011

_install_quality_integrity_1011()

# Alpha 10.1.2 closes the remaining evidence-quality gap: TOC continuation pages
# are rejected even without an explicit heading, and lexical matches confined to
# a repeated project/page header cannot prove a differently themed requirement.
from .evidence_quality_1012 import install_evidence_quality_1012 as _install_evidence_quality_1012

_install_evidence_quality_1012()

# Alpha 10.1.3 makes the evidence accepted by Judge/Critic the canonical visible
# proof while preserving the original retrieval winner as an auditable trace.
from .proof_trace_1013 import install_proof_trace_1013 as _install_proof_trace_1013

_install_proof_trace_1013()

__all__ = [
    "CanonicalProject", "Comparison", "Evidence", "Finding", "ProjectObject",
    "PropertyValue", "Requirement", "ValidationIssue", "stable_id",
    "ENGINE_VERSION", "EvidenceAssessment", "VerificationDecision",
    "VerificationEngine20", "VerificationRequest",
]

__version__ = "20.0-alpha10.1.3-proof-trace-consistency"
