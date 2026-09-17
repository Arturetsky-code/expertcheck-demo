from __future__ import annotations

from typing import Any, Callable


ENGINE_VERSION = "20.0-alpha10.1.3-proof-trace-consistency"
_INSTALLED = False
_ORIGINAL_BASE_APPLY: Callable[..., dict[str, Any]] | None = None


def _selected_primary(row: dict[str, Any]) -> dict[str, Any] | None:
    proof = dict(row.get("semantic_proof") or {})
    selected = list(proof.get("selected_evidence") or row.get("semantic_selected_evidence") or [])
    for item in selected:
        if not isinstance(item, dict):
            continue
        document = str(item.get("document") or item.get("evidence_document") or "").strip()
        page = item.get("page") if item.get("page") not in (None, "") else item.get("evidence_page")
        fragment = str(
            item.get("fragment")
            or item.get("text")
            or item.get("evidence_fragment")
            or ""
        ).strip()
        if document and page not in (None, "") and fragment:
            return {
                "evidence_id": str(item.get("evidence_id") or "").strip(),
                "document": document,
                "page": page,
                "fragment": fragment,
                "source_locator": str(item.get("source_locator") or "").strip()
                or f"{document}, стр. {page}",
            }
    return None


def _preserve_retrieval_trace(row: dict[str, Any]) -> None:
    """Keep the pre-semantic retrieval winner for audit without making it canonical."""
    mapping = {
        "retrieval_evidence_id": "evidence_id",
        "retrieval_evidence_document": "evidence_document",
        "retrieval_evidence_page": "evidence_page",
        "retrieval_evidence_fragment": "evidence_fragment",
    }
    for target, source in mapping.items():
        if target not in row:
            row[target] = row.get(source)
    row.setdefault("retrieval_evidence_source", "RETRIEVAL_PRIMARY")


def canonicalize_semantic_proof_trace(result: dict[str, Any] | None) -> dict[str, Any]:
    """Make the accepted Judge/Critic evidence the canonical engineer-facing proof.

    Retrieval is intentionally preserved as diagnostics. A semantic VERIFIED_OK
    without an addressable selected evidence trace is demoted fail-closed rather
    than exposing a categorical result whose visible evidence points elsewhere.
    """
    output = dict(result or {})
    rows = [dict(item) for item in (output.get("rows") or []) if isinstance(item, dict)]
    applied = 0

    for row in rows:
        if str(row.get("proof_state") or "").upper() != "SEMANTIC_CONSENSUS_PROOF":
            continue

        _preserve_retrieval_trace(row)
        primary = _selected_primary(row)
        if primary is None:
            row["kind"] = "REVIEW_QUESTION"
            row["state"] = "Вопрос специалисту"
            row["proof_state"] = "SEMANTIC_PROOF_REQUIRED"
            row["reason_code"] = "NORMATIVE_SEMANTIC_CANONICAL_EVIDENCE_MISSING"
            row["reason"] = (
                "Judge/Critic сформировали положительное решение, но в сохранённом proof trace отсутствует "
                "адресное выбранное доказательство. Категорическое подтверждение удержано."
            )
            row["proof_trace_consistent"] = False
            row["canonical_evidence_source"] = "NONE"
            continue

        row["evidence_id"] = primary["evidence_id"] or row.get("evidence_id") or ""
        row["evidence_document"] = primary["document"]
        row["evidence_page"] = primary["page"]
        row["evidence_fragment"] = primary["fragment"]
        row["canonical_evidence_source"] = "SEMANTIC_SELECTED_EVIDENCE"
        row["canonical_evidence_id"] = primary["evidence_id"]
        row["canonical_evidence_locator"] = primary["source_locator"]
        row["proof_trace_consistent"] = True
        applied += 1

    output["rows"] = rows
    output["verified_ok"] = sum(
        str(item.get("kind") or "").upper() == "VERIFIED_OK" for item in rows
    )
    output["review_questions"] = sum(
        str(item.get("kind") or "").upper() == "REVIEW_QUESTION" for item in rows
    )
    output["system_limitations"] = sum(
        str(item.get("kind") or "").upper() == "SYSTEM_LIMITATION" for item in rows
    )
    output["project_findings"] = sum(
        str(item.get("kind") or "").upper() == "PROJECT_FINDING" for item in rows
    )
    output["semantic_proof_applied"] = applied
    output["proof_trace_version"] = ENGINE_VERSION
    return output


def install_proof_trace_1013() -> None:
    """Patch the base apply gate used by the already-installed resumable overlay."""
    global _INSTALLED, _ORIGINAL_BASE_APPLY
    if _INSTALLED:
        return

    from . import alpha10_reliability as reliability

    _ORIGINAL_BASE_APPLY = reliability._ORIGINAL_APPLY

    def _apply_with_canonical_trace(
        proof_result: dict[str, Any],
        semantic_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base = _ORIGINAL_BASE_APPLY(proof_result, semantic_result)
        return canonicalize_semantic_proof_trace(base)

    reliability._ORIGINAL_APPLY = _apply_with_canonical_trace
    _INSTALLED = True


__all__ = [
    "ENGINE_VERSION",
    "canonicalize_semantic_proof_trace",
    "install_proof_trace_1013",
]
