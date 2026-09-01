from __future__ import annotations

import gzip
import hashlib
import json
from typing import Any, Iterable


SNAPSHOT_VERSION = "1.0-rerunnable-evidence-corpus"


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
    comparisons: Iterable[dict[str, Any]],
) -> bytes:
    """Export a portable compressed snapshot for regression and AI continuation."""
    document_rows = list(documents or [])
    first = dict(document_rows[0] if document_rows else {})
    payload = {
        "format": "ExpertCheck Project Verification Snapshot",
        "version": SNAPSHOT_VERSION,
        "analysis_snapshot": first.get("analysis_snapshot") or {},
        "core_version": first.get("core_version"),
        "documents": [{
            "Файл": row.get("Файл"), "Тип документа": row.get("Тип документа"),
            "Страниц": row.get("Страниц"), "core_version": row.get("core_version"),
        } for row in document_rows],
        "findings": list(findings or []),
        "comparisons": list(comparisons or []),
        "assignment_requirements": first.get("assignment_requirements") or [],
        "assignment_compliance": first.get("assignment_compliance") or [],
        "assignment_atomic_compliance": first.get("assignment_atomic_compliance") or [],
        "automatic_checklist_review": first.get("automatic_checklist_review") or {},
        "normative_compliance_audit": first.get("normative_compliance_audit") or [],
        "universal_project_fact_graph": first.get("universal_project_fact_graph") or {},
        "project_review_plan": first.get("project_review_plan") or {},
        "report_quality_gate": first.get("report_quality_gate") or {},
        "coverage_matrix": first.get("coverage_matrix") or {},
    }
    raw = json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8")
    return gzip.compress(raw, compresslevel=6)


def load_project_snapshot(data: bytes) -> dict[str, Any]:
    payload = json.loads(gzip.decompress(data).decode("utf-8"))
    if payload.get("format") != "ExpertCheck Project Verification Snapshot":
        raise ValueError("Файл не является цифровым снимком ExpertCheck.")
    if not isinstance(payload.get("analysis_snapshot"), dict):
        raise ValueError("В цифровом снимке отсутствует корпус доказательств.")
    return payload


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
        "source_pdf_required": False,
    }
