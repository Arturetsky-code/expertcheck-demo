from __future__ import annotations

from typing import Any

from .legacy_adapter import Legacy18Adapter
from .parity import evaluate_golden_cases
from .verification import VerificationEngine20
from .normative_foundation import default_foundation
from .normative_execution import NormativeExecutionEngine20
from core.visual_evidence_cache import build_visual_page_batches


DUAL_RUN_VERSION = "20.0-alpha8-normative-execution"


def compact_normative_diagnostic(manifest: dict[str, Any] | None) -> dict[str, Any]:
    """Persist only non-sensitive aggregate normative diagnostics.

    No project text, evidence fragments, page excerpts or visual payloads are
    copied here.  The structure is intentionally small so it can be stored in
    workspace history and queried without unpacking the full project snapshot.
    """
    source = dict(manifest or {})
    execution = dict(source.get("normative_execution") or {})
    frontier = dict(execution.get("proof_frontier") or {})
    semantic = dict(frontier.get("semantic_pending") or {})
    set_pending = dict(frontier.get("set_completeness") or {})
    visual = dict(frontier.get("visual_pending") or {})
    retained = dict(frontier.get("retained_fail_closed") or {})

    def _small_counts(value: Any) -> dict[str, int]:
        if not isinstance(value, dict):
            return {}
        result = {}
        for key, raw in value.items():
            try:
                count = int(raw or 0)
            except (TypeError, ValueError):
                continue
            if count:
                result[str(key)] = count
        return result

    return {
        "version": "1.0",
        "manifest_version": str(source.get("version") or ""),
        "registered_contracts": int(execution.get("registered_contracts") or execution.get("contracts") or 0),
        "active_contracts": int(execution.get("active_contracts") or execution.get("contracts") or 0),
        "inactive_triggered_contracts": int(execution.get("inactive_triggered_contracts") or 0),
        "verified_ok": int(execution.get("verified_ok") or 0),
        "project_findings": int(execution.get("project_findings") or 0),
        "review_questions": int(execution.get("review_questions") or 0),
        "system_limitations": int(execution.get("system_limitations") or 0),
        "held_by_proof_control": int(
            execution.get("demoted_keyword_only_remaining")
            if execution.get("demoted_keyword_only_remaining") is not None
            else execution.get("demoted_keyword_only") or 0
        ),
        "semantic_queue_total": int(execution.get("semantic_queue_total") or 0),
        "semantic_proof_applied": int(execution.get("semantic_proof_applied") or 0),
        "set_completeness_queue_total": int(execution.get("set_completeness_queue_total") or 0),
        "visual_queue_total": int(execution.get("visual_queue_total") or 0),
        "evidence_coverage_pct": float(execution.get("evidence_coverage_pct") or 0.0),
        "blocker_counts": _small_counts(frontier.get("blocker_counts")),
        "semantic_pending": {
            "total": int(semantic.get("total") or 0),
            "by_source": _small_counts(semantic.get("by_source")),
            "by_section": _small_counts(semantic.get("by_section")),
            "by_evidence_candidates": _small_counts(semantic.get("by_evidence_candidates")),
            "by_retrieval_admission": _small_counts(semantic.get("by_retrieval_admission")),
        },
        "set_completeness": {
            "total": int(set_pending.get("total") or 0),
            "by_source": _small_counts(set_pending.get("by_source")),
            "by_section": _small_counts(set_pending.get("by_section")),
        },
        "visual_pending": {
            "total": int(visual.get("total") or 0),
            "by_kind": _small_counts(visual.get("by_kind")),
            "by_section": _small_counts(visual.get("by_section")),
        },
        "retained_fail_closed": {
            "total": int(retained.get("total") or 0),
            "by_reason": _small_counts(retained.get("by_reason")),
            "by_source": _small_counts(retained.get("by_source")),
            "by_section": _small_counts(retained.get("by_section")),
        },
    }


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
    foundation=default_foundation()
    knowledge_summary=foundation.summary()
    knowledge_routes=foundation.project_routes(documents)
    page_corpus=list(((documents[0] if documents else {}).get("analysis_snapshot") or {}).get("page_corpus") or [])
    normative_execution=NormativeExecutionEngine20(foundation).run(documents,page_corpus)
    visual_cache=dict((documents[0] if documents else {}).get("visual_evidence_cache") or {})
    visual_batch_plan=build_visual_page_batches(
        normative_execution.get("visual_item_queue") or [],
        visual_cache,
    )
    normative_execution["visual_evidence_cache_summary"]={
        "version":visual_cache.get("version") or "",
        "planned_pages":int(visual_cache.get("planned_pages") or 0),
        "cached_pages":int(visual_cache.get("cached_pages") or 0),
        "omitted_pages":int(visual_cache.get("omitted_pages") or 0),
        "image_bytes":int(visual_cache.get("image_bytes") or 0),
        "persisted_for_resume":bool(visual_cache.get("persisted_for_resume")),
    }
    normative_execution["visual_page_batches"]=list(visual_batch_plan.get("page_batches") or [])
    normative_execution["visual_page_batch_total"]=int(visual_batch_plan.get("page_batch_total") or 0)
    normative_execution["visual_page_batch_items"]=int(visual_batch_plan.get("unique_items_with_cached_page") or 0)
    normative_execution["visual_page_batch_fallback_total"]=int(visual_batch_plan.get("fallback_page_total") or 0)
    normative_execution["visual_page_batch_candidate_total"]=int(visual_batch_plan.get("candidate_page_total") or 0)
    normative_execution["visual_page_batch_strategy"]=str(visual_batch_plan.get("strategy") or "")
    normative_execution["visual_page_fallbacks"]=list(visual_batch_plan.get("fallback_pages") or [])
    normative_execution["visual_page_batch_unresolved"]=int(visual_batch_plan.get("unresolved_item_total") or 0)
    audit_rows=[]
    for decision in verification.get("decision_rows") or []:
        meta=dict(decision.get("metadata") or {})
        if not (
            decision.get("automatic_verdict_eligible")
            or decision.get("kind")=="PROJECT_FINDING"
            or meta.get("legacy_disagreement")
            or meta.get("canonical_reason_code") in {
                "PARAMETER_BINDING_NOT_PROVEN",
                "RESERVE_TOPOLOGY_NOT_PROVEN",
                "RESERVE_TOPOLOGY_REQUIREMENT_UNSTRUCTURED",
                "PROJECT_EVIDENCE_VALUE_CONFLICT",
            }
            or (
                str(meta.get("domain") or "").casefold() == "normative"
                and bool(meta.get("canonical_reason_code"))
            )
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
        evidence_fragments=[]
        evidence_bindings=[]
        routed_evidence_count=0
        for evidence_id in decision.get("evidence_ids") or []:
            evidence=project.evidence.get(evidence_id)
            if evidence and evidence.address:
                evidence_addresses.append(evidence.address)
            if evidence and evidence.fragment:
                fragment=" ".join(str(evidence.fragment).split())
                if fragment and fragment not in evidence_fragments:
                    evidence_fragments.append(fragment[:360])
            if evidence:
                emeta=dict(evidence.metadata or {})
                if emeta.get("canonical_routed"):
                    routed_evidence_count+=1
                binding=" / ".join(
                    str(value) for value in (
                        emeta.get("typed_parameter_code") or emeta.get("project_parameter_code") or emeta.get("observed_parameter_code") or "",
                        emeta.get("project_value") if emeta.get("project_value") is not None else emeta.get("observed_value"),
                        emeta.get("project_unit") or emeta.get("observed_unit") or "",
                    ) if str(value or "").strip()
                )
                if binding and binding not in evidence_bindings:
                    evidence_bindings.append(binding)
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
            "reason_code":meta.get("canonical_reason_code") or meta.get("canonical_reason_code") or "",
            "typed_fact_count":meta.get("typed_fact_count") or 0,
            "routed_evidence_count":routed_evidence_count,
            "evidence_bindings":" | ".join(evidence_bindings[:4]),
            "required_topology":meta.get("required_topology"),
            "project_topology":meta.get("project_topology"),
            "verified_clause":bool(meta.get("verified_clause")),
            "normative_source":meta.get("source_reference") or "",
            "normative_paragraph":meta.get("paragraph") or "",
            "normative_check_kind":meta.get("check_kind") or "",
            "applicability_state":meta.get("applicability_state") or "",
            "normative_contract":meta.get("normative_contract") or "",
            "normative_registry_trust":meta.get("normative_registry_trust") or "",
            "normative_source_status":meta.get("normative_source_status") or "",
            "normative_history_occurrences":int(meta.get("normative_history_occurrences") or 0),
            "normative_history_projects":int(meta.get("normative_history_projects") or 0),
            "normative_history_policy":meta.get("normative_history_policy") or "",
            "required_document_roles":" + ".join(meta.get("required_document_roles") or []),
            "observed_document_roles":" + ".join(meta.get("observed_document_roles") or []),
            "missing_document_roles":" + ".join(meta.get("missing_document_roles") or []),
            "reason":decision.get("reason") or "",
            "proof_source":meta.get("proof_source") or "",
            "legacy_disagreement":bool(meta.get("legacy_disagreement")),
            "evidence":" | ".join(dict.fromkeys(evidence_addresses)),
            "evidence_fragment":" || ".join(evidence_fragments[:2]),
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
        "golden_skipped":bool(golden.get("skipped")),
        "golden_applicable":bool(golden.get("applicable",True)),
        "golden_profile_matches":golden.get("profile_matches",0),
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
            "normative_verified_clauses":verification.get("normative_verified_clauses",0),
            "normative_auto":verification.get("normative_auto",0),
            "normative_structure_auto":verification.get("normative_structure_auto",0),
            "normative_review":verification.get("normative_review",0),
            "normative_unverified":verification.get("normative_unverified",0),
            "normative_applicability_blocked":verification.get("normative_applicability_blocked",0),
            "typed_assignment_auto":verification.get("typed_assignment_auto",0),
            "reserve_topology_auto":verification.get("reserve_topology_auto",0),
            "parameter_binding_blocked":verification.get("parameter_binding_blocked",0),
            "canonical_routed_evidence":verification.get("canonical_routed_evidence",0),
            "legacy_disagreements":verification.get("legacy_disagreements",0),
            "contract_errors":verification["contract_errors"],
            "counts":verification["counts"],
            "audit_rows":audit_rows[:40],
        },
        "normative_execution":normative_execution,
        "knowledge_foundation":{
            **knowledge_summary,
            "project_sections":knowledge_routes.get("project_sections") or [],
            "project_relevant":knowledge_routes.get("project_relevant",0),
            "project_verified_clause_routes":knowledge_routes.get("verified_clause_routes",0),
            "project_automatic_contract_ready":knowledge_routes.get("automatic_contract_ready",0),
            "project_history_prioritized":knowledge_routes.get("history_prioritized",0),
            "priority_routes":list(knowledge_routes.get("rows") or [])[:40],
        },
        "legacy_results_unchanged":True,
    }
    if documents:
        documents[0]["canonical_core_20_manifest"]=manifest
    return manifest
