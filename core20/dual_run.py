from __future__ import annotations

from typing import Any

from .legacy_adapter import Legacy18Adapter
from .parity import evaluate_golden_cases


DUAL_RUN_VERSION = "20.0-alpha1-dual-run"


def build_dual_run_manifest(
    *,
    project_name: str,
    documents: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    assembly_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build 20.0 canonical state beside 18.x without changing legacy verdicts."""
    project=Legacy18Adapter().build(
        project_name=project_name,documents=documents,findings=findings,comparisons=comparisons,assembly_rows=assembly_rows,
    )
    issues=project.validate()
    golden=evaluate_golden_cases(project)
    manifest={
        "version":DUAL_RUN_VERSION,
        "schema_version":project.schema_version,
        "fingerprint":project.fingerprint(),
        "stats":project.stats(),
        "validation_errors":len([item for item in issues if item.severity=="ERROR"]),
        "validation_warnings":len([item for item in issues if item.severity!="ERROR"]),
        "golden_passed":golden["passed"],
        "golden_failed":golden["failed"],
        "legacy_results_unchanged":True,
    }
    if documents:
        documents[0]["canonical_core_20_manifest"]=manifest
    return manifest
