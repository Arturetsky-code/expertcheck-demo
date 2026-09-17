from __future__ import annotations

"""Runtime fix for stale AI continuation totals.

For a checkpoint produced by the current Evidence Quality engine, the rebuilt
L4/consensus-eligible packet set is the authoritative actionable queue. Older
ledger totals remain useful diagnostics, but must not create phantom pending
work after evidence-window or binding rules change the eligible universe.

Older/stale checkpoints keep the legacy migration behaviour unchanged.
"""

import sys
from typing import Any, Iterable

from . import ai_continuation_ledger as ledger

PATCH_VERSION = "18.5.2-current-l4-universe-v1"
_POLICY = "CURRENT_ELIGIBLE_L4_AUTHORITATIVE"
_ORIGINAL_QUEUE_STATUS = ledger.queue_status_from_document
_INSTALLED = False

_QUEUE_COUNTER_KEYS = {
    "cumulative_packet_total",
    "judge_candidates",
    "judge_responses",
    "judge_pending",
    "not_selected",
    "queue_remaining",
    "critic_required",
    "critic_responses",
    "critic_pending",
    "cumulative_responses",
    "unique_packages_complete",
    "unique_packages_pending",
    "package_completion_pct",
}


def _domain_rows(doc: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    assignment = list(doc.get("assignment_atomic_compliance") or [])
    checklist_review = dict(doc.get("automatic_checklist_review") or {})
    checklist_atomic = dict(checklist_review.get("atomic_verification") or {})
    checklist = list(checklist_atomic.get("atoms") or [])
    return {"assignment": assignment, "checklist": checklist}


def _filtered_lane(
    checkpoint_domain: dict[str, Any] | None,
    role: str,
    current_ids: set[str],
) -> dict[str, dict[str, Any]]:
    domain = checkpoint_domain if isinstance(checkpoint_domain, dict) else {}
    lane = domain.get(role)
    if not isinstance(lane, dict):
        return {}
    return {
        str(packet_id): dict(value)
        for packet_id, value in lane.items()
        if str(packet_id) in current_ids and isinstance(value, dict)
    }


def _historical_total(
    audit: dict[str, Any],
    previous_ledger: dict[str, Any],
    checkpoint_domain: dict[str, Any] | None,
) -> int:
    domain = checkpoint_domain if isinstance(checkpoint_domain, dict) else {}
    checkpoint_ids = set()
    for role in ("judge", "critic"):
        lane = domain.get(role)
        if isinstance(lane, dict):
            checkpoint_ids.update(str(value) for value in lane if str(value))
    return max(
        int(audit.get("cumulative_packet_total") or 0),
        int(audit.get("judge_candidates") or 0),
        int(previous_ledger.get("packet_total") or 0),
        len(checkpoint_ids),
    )


def _sanitized_audit(audit: dict[str, Any]) -> dict[str, Any]:
    # Preserve provider/runtime diagnostics, evidence levels and execution logs;
    # only remove counters that describe the old queue universe.
    result = dict(audit or {})
    for key in _QUEUE_COUNTER_KEYS:
        result.pop(key, None)
    return result


def queue_status_current_universe(
    doc: dict[str, Any],
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return current actionable queue status without historical phantom work."""
    checkpoint_obj = checkpoint if isinstance(checkpoint, dict) else {}
    checkpoint_engine = str(checkpoint_obj.get("_semantic_engine_version") or "")

    # Old snapshots intentionally retain the old migration path. The current
    # universe becomes authoritative only once 18.5 has rebuilt packet metadata.
    if checkpoint_engine != ledger.CURRENT_SEMANTIC_ENGINE_VERSION:
        return _ORIGINAL_QUEUE_STATUS(doc, checkpoint)

    rows_by_domain = _domain_rows(doc)
    semantic_original = dict(doc.get("semantic_evidence_engine") or {})
    root_ledger = (
        dict(checkpoint_obj.get("_ledger") or {})
        if isinstance(checkpoint_obj.get("_ledger"), dict)
        else {}
    )
    old_ledger_domains = dict(root_ledger.get("domains") or {})

    working_doc = dict(doc)
    working_semantic = dict(semantic_original)
    working_checkpoint = dict(checkpoint_obj)
    working_checkpoint["_ledger"] = {
        "version": ledger.LEDGER_VERSION,
        "snapshot_id": str(root_ledger.get("snapshot_id") or ""),
        "domains": {},
    }

    diagnostics: dict[str, dict[str, int]] = {}
    for domain, rows in rows_by_domain.items():
        current_ids = ledger.packet_ids_from_rows(rows)
        audit = dict(semantic_original.get(domain) or {})
        previous_ledger = dict(old_ledger_domains.get(domain) or {})
        checkpoint_domain = (
            checkpoint_obj.get(domain)
            if isinstance(checkpoint_obj.get(domain), dict)
            else {}
        )
        historical_total = _historical_total(audit, previous_ledger, checkpoint_domain)
        diagnostics[domain] = {
            "historical_total": historical_total,
            "current_total": len(current_ids),
            "retired": max(0, historical_total - len(current_ids)),
        }

        working_semantic[domain] = _sanitized_audit(audit)
        filtered_domain = dict(checkpoint_domain)
        filtered_domain["judge"] = _filtered_lane(checkpoint_domain, "judge", current_ids)
        filtered_domain["critic"] = _filtered_lane(checkpoint_domain, "critic", current_ids)
        working_checkpoint[domain] = filtered_domain

    working_doc["semantic_evidence_engine"] = working_semantic
    status = _ORIGINAL_QUEUE_STATUS(working_doc, working_checkpoint)

    # Persist the corrected current-universe counters into the live project so
    # reports and the next rerun see the same state as the Project page.
    corrected_semantic = dict(working_doc.get("semantic_evidence_engine") or {})
    for domain, values in diagnostics.items():
        audit = dict(corrected_semantic.get(domain) or {})
        audit.update({
            "queue_universe_policy": _POLICY,
            "queue_universe_patch_version": PATCH_VERSION,
            "historical_packet_total": values["historical_total"],
            "current_universe_packet_total": values["current_total"],
            "retired_packet_count": values["retired"],
        })
        corrected_semantic[domain] = audit
    doc["semantic_evidence_engine"] = corrected_semantic

    if isinstance(checkpoint, dict):
        checkpoint["_ledger"] = dict(working_checkpoint.get("_ledger") or {})
        checkpoint["_queue_universe_patch_version"] = PATCH_VERSION

    status["queue_universe_policy"] = _POLICY
    status["queue_universe_patch_version"] = PATCH_VERSION
    status["historical_packet_total"] = sum(
        value["historical_total"] for value in diagnostics.values()
    )
    status["retired_packet_count"] = sum(
        value["retired"] for value in diagnostics.values()
    )
    return status


def install_ai_queue_universe_patch() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    ledger.queue_status_from_document = queue_status_current_universe

    # If semantic_continuation was imported earlier by another core module,
    # replace its bound reference too. Future imports automatically receive the
    # patched function from ai_continuation_ledger.
    module = sys.modules.get("core.semantic_continuation")
    if module is not None:
        setattr(module, "queue_status_from_document", queue_status_current_universe)
    _INSTALLED = True


__all__ = [
    "PATCH_VERSION",
    "queue_status_current_universe",
    "install_ai_queue_universe_patch",
]
