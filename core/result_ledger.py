from __future__ import annotations

from copy import deepcopy
from typing import Any

from .cross_section_verification import qualify_cross_section_verdicts
from .project_review_planner import build_review_plan
from .verified_verdict_gate import enforce_project_verdicts


def build_qualified_result_ledger(
    *,
    assignment_rows: list[dict[str,Any]] | None = None,
    normative_rows: list[dict[str,Any]] | None = None,
    checklist_rows: list[dict[str,Any]] | None = None,
    comparisons: list[dict[str,Any]] | None = None,
    clone_inputs: bool = True,
) -> dict[str,Any]:
    """Build the single final adjudicated ledger used by Results and reports.

    The user-facing Results page and exported reports must never classify the
    same raw project payload through different gate sequences.  This helper
    applies the report trust-boundary sequence once:
      cross-section qualification -> Verified Core gate -> review plan.
    """
    if clone_inputs:
        assignment=deepcopy(list(assignment_rows or []))
        normative=deepcopy(list(normative_rows or []))
        checklist=deepcopy(list(checklist_rows or []))
        cross=deepcopy(list(comparisons or []))
    else:
        assignment=list(assignment_rows or [])
        normative=list(normative_rows or [])
        checklist=list(checklist_rows or [])
        cross=list(comparisons or [])

    qualify_cross_section_verdicts(cross)
    verified_gate=enforce_project_verdicts(
        assignment_rows=assignment,
        normative_rows=normative,
        checklist_review={"results":checklist},
        comparisons=cross,
    )
    plan=build_review_plan(
        assignment_rows=assignment,
        normative_rows=normative,
        checklist_review={"results":checklist},
        comparisons=cross,
    )
    return {
        "assignment_rows":assignment,
        "normative_rows":normative,
        "checklist_rows":checklist,
        "comparisons":cross,
        "review_plan":plan,
        "verified_gate":verified_gate,
    }
