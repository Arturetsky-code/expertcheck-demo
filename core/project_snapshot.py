from __future__ import annotations

import gzip
import hashlib
import json
from typing import Any, Iterable

from .project_data_contract import enforce_project_data_contract


SNAPSHOT_VERSION = "18.4.1-portable-project-with-ai-checkpoint"


def _text(value: Any, limit: int = 12000) -> str:
    return str(value or "")[:limit]


def _compact_pages(page_corpus: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in page_corpus or []:
        document = str(row.get("document") or row.get("filename") or "")
        page = str(row.get("page") or "")
        key = (document, page)
        if not document or key in seen:
            continue
        seen.add(key)
        pages.append({
            "document": document,
            "document_type": row.get("document_type") or row.get("section"),
            "page": row.get("page"),
            "section_title": _text(row.get("section_title"), 500),
            "text": _text(row.get("text") or row.get("content")),
        })
    return pages


def corpus_fingerprint(page_corpus: Iterable[dict[str, Any]]) -> str:
    """Identify exact extracted content so AI checkpoints cannot cross projects."""
    digest = hashlib.sha256()
    for page in page_corpus or []:
        digest.update(str(page.get("document") or page.get("filename") or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(page.get("page") or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(page.get("text") or page.get("content") or "").encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:24]


def build_analysis_snapshot(
    documents: Iterable[dict[str, Any]], *, page_corpus: Iterable[dict[str, Any]],
    fact_graph: dict[str, Any], object_registry: Iterable[dict[str, Any]] = (),
    quality_gate_comparisons: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Persist the expensive extraction layer independently from final verdicts."""
    manifest = [{
        "document": row.get("Файл") or row.get("document") or row.get("filename"),
        "document_type": row.get("Тип документа") or row.get("document_type"),
        "pages": row.get("Страниц") or row.get("page_count"),
        "size_mb": row.get("Размер, МБ") or row.get("size_mb"),
    } for row in documents or []]
    pages = _compact_pages(page_corpus)
    snapshot_id = corpus_fingerprint(pages)
    return {
        "version": SNAPSHOT_VERSION,
        "snapshot_id": snapshot_id,
        "manifest": manifest,
        "page_corpus": pages,
        "quality_gate_inputs": {
            "object_registry": list(object_registry or []),
            "comparisons": list(quality_gate_comparisons or []),
        },
        "fact_graph_summary": dict((fact_graph or {}).get("summary") or {}),
        "summary": {
            "documents": len(manifest),
            "pages": len(pages),
            "facts": len((fact_graph or {}).get("facts") or []),
            "rerunnable_without_pdf": bool(pages),
        },
    }


def project_snapshot_bytes(
    documents: Iterable[dict[str, Any]], findings: Iterable[dict[str, Any]],
    comparisons: Iterable[dict[str, Any]], *,
    semantic_checkpoint: dict[str, Any] | None = None,
    workspace_state: dict[str, Any] | None = None,
) -> bytes:
    """Export a portable compressed snapshot for regression and AI continuation."""
    source_documents = list(documents or [])
    first = dict(source_documents[0] if source_documents else {})
    document_manifest = [{
        "Файл": row.get("Файл"), "Тип документа": row.get("Тип документа"),
        "Страниц": row.get("Страниц"), "core_version": row.get("core_version"),
    } for row in source_documents]
    document_rows, finding_rows, comparison_rows, export_contract = enforce_project_data_contract(
        document_manifest, findings, comparisons, source="snapshot_export_boundary",
    )
    payload = {
        "format": "ExpertCheck Project Verification Snapshot",
        "version": SNAPSHOT_VERSION,
        "analysis_snapshot": first.get("analysis_snapshot") or {},
        "core_version": first.get("core_version"),
        "documents": document_rows,
        "findings": finding_rows,
        "comparisons": comparison_rows,
        "project_data_contract": first.get("project_data_contract") or export_contract,
        "snapshot_export_contract": export_contract,
        "assignment_requirements": first.get("assignment_requirements") or [],
        "assignment_compliance": first.get("assignment_compliance") or [],
        "assignment_atomic_compliance": first.get("assignment_atomic_compliance") or [],
        "automatic_checklist_review": first.get("automatic_checklist_review") or {},
        "normative_compliance_audit": first.get("normative_compliance_audit") or [],
        "universal_project_fact_graph": first.get("universal_project_fact_graph") or {},
        "project_review_plan": first.get("project_review_plan") or {},
        "report_quality_gate": first.get("report_quality_gate") or {},
        "coverage_matrix": first.get("coverage_matrix") or {},
        "semantic_evidence_engine": first.get("semantic_evidence_engine") or {},
        "semantic_continuation": first.get("semantic_continuation") or {},
        "semantic_project_graph": first.get("semantic_project_graph") or {},
        "atomic_requirement_graph": first.get("atomic_requirement_graph") or {},
        "coverage_acceleration_budget": first.get("coverage_acceleration_budget") or {},
        "deep_evidence_review": first.get("deep_evidence_review") or {},
        "verified_core_gate": first.get("verified_core_gate") or {},
        "semantic_execution_checkpoint": dict(semantic_checkpoint or {}),
        "workspace_state": dict(workspace_state or {}),
    }
    raw = json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8")
    return gzip.compress(raw, compresslevel=6)


def load_project_snapshot(data: bytes) -> dict[str, Any]:
    payload = json.loads(gzip.decompress(data).decode("utf-8"))
    if payload.get("format") != "ExpertCheck Project Verification Snapshot":
        raise ValueError("Файл не является цифровым снимком ExpertCheck.")
    if not isinstance(payload.get("analysis_snapshot"), dict):
        raise ValueError("В цифровом снимке отсутствует корпус доказательств.")
    page_corpus = list((payload.get("analysis_snapshot") or {}).get("page_corpus") or [])
    if not page_corpus:
        raise ValueError("Цифровой снимок не содержит извлечённого корпуса страниц.")
    stored_snapshot_id = str((payload.get("analysis_snapshot") or {}).get("snapshot_id") or "")
    actual_snapshot_id = corpus_fingerprint(page_corpus)
    if stored_snapshot_id and stored_snapshot_id != actual_snapshot_id:
        raise ValueError(
            "Цифровой снимок повреждён: fingerprint корпуса страниц не совпадает."
        )
    payload["analysis_snapshot"]["snapshot_id"] = actual_snapshot_id
    documents, findings, comparisons, contract = enforce_project_data_contract(
        payload.get("documents"), payload.get("findings"), payload.get("comparisons"),
        source="snapshot_load_boundary",
    )
    if contract.get("fatal_issues"):
        raise ValueError(
            "Цифровой снимок не прошёл контракт данных: "
            + "; ".join(str(item) for item in contract["fatal_issues"][:5])
        )
    payload["documents"] = documents
    payload["findings"] = findings
    payload["comparisons"] = comparisons
    payload["snapshot_load_contract"] = contract
    return payload


def snapshot_to_workspace_payload(
    payload: dict[str, Any], *,
    project_name: str = "",
) -> dict[str, Any]:
    """Rebuild a resumable workspace project from a portable snapshot.

    Old snapshots that predate AI-checkpoint export remain supported.  Their
    deterministic extraction layer is restored and semantic continuation starts
    from an empty checkpoint against the preserved page corpus.
    """
    documents = [dict(row) for row in payload.get("documents") or []]
    findings = [dict(row) for row in payload.get("findings") or []]
    comparisons = [dict(row) for row in payload.get("comparisons") or []]
    if not documents:
        documents = [{
            "Файл": "Цифровой снимок ExpertCheck",
            "Тип документа": "Снимок проекта",
            "Страниц": len((payload.get("analysis_snapshot") or {}).get("page_corpus") or []),
        }]

    first = documents[0]
    project_fields = (
        "analysis_snapshot",
        "project_data_contract",
        "assignment_requirements",
        "assignment_compliance",
        "assignment_atomic_compliance",
        "automatic_checklist_review",
        "normative_compliance_audit",
        "universal_project_fact_graph",
        "project_review_plan",
        "report_quality_gate",
        "coverage_matrix",
        "semantic_evidence_engine",
        "semantic_continuation",
        "semantic_project_graph",
        "atomic_requirement_graph",
        "coverage_acceleration_budget",
        "deep_evidence_review",
        "verified_core_gate",
    )
    for key in project_fields:
        if key in payload:
            first[key] = payload.get(key)

    first["core_version"] = payload.get("core_version") or first.get("core_version")
    first["snapshot_restored"] = True
    first["snapshot_restore_version"] = SNAPSHOT_VERSION

    # Older snapshots did not export the top-level semantic audit. Recover it
    # from the nested atomic structures when possible.
    if not isinstance(first.get("semantic_evidence_engine"), dict) or not first.get("semantic_evidence_engine"):
        assignment_atoms = list(first.get("assignment_atomic_compliance") or [])
        assignment_audit = dict(
            (assignment_atoms[0] if assignment_atoms else {}).get("semantic_engine_audit") or {}
        )
        checklist = dict(first.get("automatic_checklist_review") or {})
        checklist_atomic = dict(checklist.get("atomic_verification") or {})
        checklist_audit = dict(checklist_atomic.get("semantic_engine_audit") or {})
        first["semantic_evidence_engine"] = {
            "version": "snapshot-migrated",
            "assignment": assignment_audit,
            "checklist": checklist_audit,
        }

    checkpoint = payload.get("semantic_execution_checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, dict) else {}
    snapshot_id = str((first.get("analysis_snapshot") or {}).get("snapshot_id") or "")
    if checkpoint and checkpoint.get("_project_fingerprint") != snapshot_id:
        # Never reuse AI decisions when their corpus identity is not provably
        # the same. The deterministic snapshot is still perfectly reusable.
        checkpoint = {}
    if not checkpoint:
        checkpoint = {"_project_fingerprint": snapshot_id} if snapshot_id else {}

    workspace = dict(payload.get("workspace_state") or {})
    restored_name = (
        str(project_name or "").strip()
        or str(workspace.get("project_name") or "").strip()
        or "Восстановленный проект"
    )
    return {
        "project_name": restored_name,
        "analysis_time": workspace.get("analysis_time"),
        "result": (documents, findings, comparisons),
        "object_registry_confirmed": bool(workspace.get("object_registry_confirmed", False)),
        "object_assembly_rows": list(workspace.get("object_assembly_rows") or []),
        "completeness_user_confirmed": bool(workspace.get("completeness_user_confirmed", False)),
        "completeness_decisions": dict(workspace.get("completeness_decisions") or {}),
        "checklist_run": workspace.get("checklist_run"),
        "checklist_user_results": dict(workspace.get("checklist_user_results") or {}),
        "risk_user_decisions": dict(workspace.get("risk_user_decisions") or {}),
        "object_learning_examples": list(workspace.get("object_learning_examples") or []),
        "semantic_execution_checkpoint": checkpoint,
        "snapshot_restore_info": {
            "version": payload.get("version"),
            "snapshot_id": snapshot_id,
            "source_pdf_required": False,
            "ai_checkpoint_restored": bool(
                payload.get("semantic_execution_checkpoint")
                and len(checkpoint) > int(bool(snapshot_id))
            ),
        },
    }


def recheck_project_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Repeat deterministic release gates without parsing the source PDFs again."""
    from .coverage_matrix import build_coverage_matrix
    from .report_quality_gate import validate_review_plan

    plan = dict(payload.get("project_review_plan") or {})
    gate_inputs = dict((payload.get("analysis_snapshot") or {}).get("quality_gate_inputs") or {})
    comparisons = list(
        gate_inputs.get("comparisons") if "comparisons" in gate_inputs
        else payload.get("comparisons") or []
    )
    object_registry = list(gate_inputs.get("object_registry") or [])
    checklist = dict(payload.get("automatic_checklist_review") or {})
    rows = list(plan.get("items") or [])
    gate = validate_review_plan(
        plan,
        object_registry=object_registry,
        checklist_rows=list(checklist.get("results") or []),
        comparisons=comparisons,
    )
    coverage = build_coverage_matrix(rows)
    page_corpus = list((payload.get("analysis_snapshot") or {}).get("page_corpus") or [])
    return {
        "snapshot_id": (payload.get("analysis_snapshot") or {}).get("snapshot_id"),
        "core_version": payload.get("core_version"),
        "pages_reused": len(page_corpus),
        "review_items_rechecked": len(rows),
        "quality_gate": gate,
        "coverage_matrix": coverage,
        "project_data_contract": payload.get("snapshot_load_contract") or payload.get("project_data_contract") or {},
        "source_pdf_required": False,
    }
