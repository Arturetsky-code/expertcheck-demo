from __future__ import annotations

from typing import Any

from .legacy_adapter import Legacy18Adapter
from .parity import evaluate_golden_cases
from .verification import VerificationEngine20


DUAL_RUN_VERSION = "20.0-alpha4.1-audit"


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
    verification=VerificationEngine20(project).run()
    audit_rows=[]
    for decision in verification.get("decision_rows") or []:
        meta=dict(decision.get("metadata") or {})
        if not (
            decision.get("automatic_verdict_eligible")
            or decision.get("kind")=="PROJECT_FINDING"
            or meta.get("legacy_disagreement")
        ):
            continue
        trace_ids=list(decision.get("trace_ids") or [])
        requirement_id=next((item for item in trace_ids if item in project.requirements),None)
        comparison_id=next((item for item in trace_ids if item in project.comparisons),None)
        object_id=next((item for item in trace_ids if item in project.objects),None)
        requirement=project.requirements.get(requirement_id) if requirement_id else None
        comparison=project.comparisons.get(comparison_id) if comparison_id else None
        obj=project.objects.get(object_id) if object_id else None
        evidence_addresses=[]
        for evidence_id in decision.get("evidence_ids") or []:
            evidence=project.evidence.get(evidence_id)
            if evidence and evidence.address:
                evidence_addresses.append(evidence.address)
        audit_rows.append({
            "domain":meta.get("domain") or "",
            "kind":decision.get("kind") or "",
            "object":obj.name if obj else "",
            "check":(
                requirement.text if requirement
                else (comparison.parameter_name or comparison.parameter_code) if comparison
                else ""
            ),
            "parameter_code":meta.get("parameter_code") or "",
            "required_value":meta.get("required_value"),
            "project_value":meta.get("project_value"),
            "unit":meta.get("required_unit") or meta.get("canonical_unit") or "",
            "reason":decision.get("reason") or "",
            "proof_source":meta.get("proof_source") or "",
            "legacy_disagreement":bool(meta.get("legacy_disagreement")),
            "evidence":" | ".join(dict.fromkeys(evidence_addresses)),
            "trace_id":requirement_id or comparison_id or decision.get("verification_id") or "",
        })
    manifest={
        "version":DUAL_RUN_VERSION,
        "schema_version":project.schema_version,
        "fingerprint":project.fingerprint(),
        "stats":project.stats(),
        "validation_errors":len([item for item in issues if item.severity=="ERROR"]),
        "validation_warnings":len([item for item in issues if item.severity!="ERROR"]),
        "golden_passed":golden["passed"],
        "golden_failed":golden["failed"],
        "verification_engine":{
            "version":verification["version"],
            "mode":verification["mode"],
            "requests":verification["requests"],
            "decisions":verification["decisions"],
            "automatic_verdict_eligible":verification["automatic_verdict_eligible"],
            "automatic_coverage_pct":verification["automatic_coverage_pct"],
            "canonical_proofs_recomputed":verification.get("canonical_proofs_recomputed",0),
            "canonical_requirement_proofs_recomputed":verification.get("canonical_requirement_proofs_recomputed",0),
            "assignment_proofs_recomputed":verification.get("assignment_proofs_recomputed",0),
            "normative_checks_guarded":verification.get("normative_checks_guarded",0),
            "legacy_disagreements":verification.get("legacy_disagreements",0),
            "contract_errors":verification["contract_errors"],
            "counts":verification["counts"],
            "audit_rows":audit_rows[:40],
        },
        "legacy_results_unchanged":True,
    }
    if documents:
        documents[0]["canonical_core_20_manifest"]=manifest
    return manifest
