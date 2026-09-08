from __future__ import annotations

from typing import Any

from .cross_section_verification import qualify_cross_section_verdicts
from .project_review_planner import build_review_plan


VERSION = "18.7-verification-coverage-v1"


def refresh_verification_coverage(
    documents: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    """Requalify deterministic coverage without rereading PDFs or calling AI."""
    first = documents[0] if documents and isinstance(documents[0], dict) else {}
    if not first:
        return {"version": VERSION, "changed": False, "reason": "NO_DOCUMENT"}

    gate = qualify_cross_section_verdicts(comparisons)
    plan = build_review_plan(
        assignment_rows=list(first.get("assignment_compliance") or []),
        normative_rows=list(first.get("normative_compliance_audit") or []),
        checklist_review=dict(first.get("automatic_checklist_review") or {}),
        comparisons=comparisons,
    )
    first["cross_section_verified_gate"] = gate
    first["project_review_plan"] = plan

    comparison_domain = dict((plan.get("domains") or {}).get("comparison") or {})
    summary = {
        "version": VERSION,
        "changed": True,
        "cross_section_checked": int(gate.get("checked") or 0),
        "cross_section_passed": int(gate.get("passed") or 0),
        "cross_section_blocked": int(gate.get("blocked") or 0),
        "comparison_total": int(comparison_domain.get("total") or 0),
        "comparison_completed": int(comparison_domain.get("completed") or 0),
        "comparison_verified_ok": int(comparison_domain.get("verified_ok") or 0),
        "comparison_findings": int(comparison_domain.get("project_findings") or 0),
        "comparison_review": int(comparison_domain.get("review_questions") or 0),
        "comparison_limitations": int(comparison_domain.get("system_limitations") or 0),
        "comparison_strict_coverage_pct": float(comparison_domain.get("automatic_coverage_pct") or 0),
        "source_pdf_required": False,
        "ai_required": False,
    }
    first["verification_coverage_187"] = summary
    return summary
