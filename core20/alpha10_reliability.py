from __future__ import annotations

"""Alpha 10.1 reliability overlay for the canonical normative proof workflow.

The overlay is deliberately small and reversible: it keeps the underlying proof
engine intact, but turns its semantic queue into a resumable queue. The full
proof queue remains the root contract; only packets without a persisted,
completed Judge/Critic decision are exposed for the next call.
"""

from typing import Any

from . import normative_semantic_proof as _semantic
from .normative_proof import proof_frontier_summary


ENGINE_VERSION = "20.0-alpha10.1-quality-integrity"
_INSTALLED = False
_ORIGINAL_RUN = _semantic.run_normative_semantic_proof
_ORIGINAL_APPLY = _semantic.apply_normative_semantic_proof


def _packet_requirement_id(packet: dict[str, Any]) -> str:
    rid = str(packet.get("requirement_id") or "").strip()
    if rid:
        return rid
    pid = str(packet.get("packet_id") or "").strip()
    return pid.removeprefix("NORM-")


def _positive_confidence(value: Any) -> bool:
    try:
        return float(value or 0) > 0
    except (TypeError, ValueError):
        return False


def _decision_complete(value: dict[str, Any] | None) -> bool:
    """Distinguish a real AI decision from a synthetic fail-closed placeholder.

    The base engine intentionally materialises REVIEW_QUESTION when a provider
    returns no answer. That is safe as a verdict, but it must not consume the
    resumable queue. A real non-SUPPORTS Judge answer is complete without Critic;
    SUPPORTS additionally requires an actual Critic answer (accept or reject).
    """
    if not isinstance(value, dict) or not _positive_confidence(value.get("judge_confidence")):
        return False
    verdict = str(value.get("judge_verdict") or "").upper()
    if verdict == "SUPPORTS":
        return _positive_confidence(value.get("critic_confidence"))
    return bool(verdict)


def _previous_checkpoint() -> dict[str, Any]:
    """Read the persisted checkpoint without making Streamlit a core dependency."""
    try:
        import streamlit as st  # imported only in the interactive runtime

        result = st.session_state.get("result")
        if isinstance(result, (list, tuple)) and result:
            documents = result[0]
            if isinstance(documents, list) and documents and isinstance(documents[0], dict):
                value = documents[0].get("normative_semantic_proof")
                if isinstance(value, dict):
                    return dict(value)
    except Exception:
        pass
    return {}


def _root_identity(previous: dict[str, Any], queue: list[dict[str, Any]]) -> tuple[str, int]:
    queue_fp = _semantic.queue_fingerprint(queue)
    previous_root = str(previous.get("root_fingerprint") or previous.get("fingerprint") or "")
    previous_total = int(previous.get("root_queue_total") or previous.get("queue_total") or 0)

    # If the current queue is already the pending subset produced by Alpha 10.1,
    # keep the persisted root identity. Otherwise a new queue becomes a new
    # root and old decisions must not leak into it.
    if previous_root and previous_total >= len(queue):
        previous_decisions = {
            key: value for key, value in dict(previous.get("decisions") or {}).items()
            if _decision_complete(value)
        }
        current_ids = {_packet_requirement_id(packet) for packet in queue}
        known_ids = set(previous_decisions)
        if not current_ids.intersection(known_ids):
            return previous_root, max(previous_total, len(queue) + len(known_ids))
        if previous_root == queue_fp:
            return previous_root, max(previous_total, len(queue))
    return queue_fp, len(queue)


def _merge_result(
    current: dict[str, Any],
    previous: dict[str, Any],
    *,
    root_fingerprint: str,
    root_total: int,
    previous_decisions_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged = dict(current or {})
    previous_root = str(previous.get("root_fingerprint") or previous.get("fingerprint") or "")
    if previous_decisions_override is None:
        previous_decisions = {
            key: value for key, value in dict(previous.get("decisions") or {}).items()
            if previous_root == root_fingerprint and _decision_complete(value)
        }
    else:
        previous_decisions = {
            key: value for key, value in dict(previous_decisions_override or {}).items()
            if _decision_complete(value)
        }
    current_decisions = {
        key: value for key, value in dict(merged.get("decisions") or {}).items()
        if _decision_complete(value)
    }
    decisions = {**previous_decisions, **current_decisions}

    merged["version"] = ENGINE_VERSION
    merged["root_fingerprint"] = root_fingerprint
    # Keep fingerprint compatible with the base apply gate. The fingerprint
    # identifies the complete root queue rather than one pending slice.
    merged["fingerprint"] = root_fingerprint
    merged["root_queue_total"] = int(root_total)
    merged["queue_total"] = int(root_total)
    merged["decisions"] = decisions
    merged["processed_total"] = len(decisions)
    merged["completed_before"] = len(previous_decisions)
    merged["new_decisions"] = len(current_decisions)
    merged["verified_ok"] = sum(
        str(value.get("state") or "").upper() == "VERIFIED_OK"
        for value in decisions.values() if isinstance(value, dict)
    )
    merged["newly_verified_ok"] = sum(
        str(value.get("state") or "").upper() == "VERIFIED_OK"
        for value in current_decisions.values() if isinstance(value, dict)
    )
    merged["reviewed_total"] = sum(
        str(value.get("state") or "").upper() == "REVIEW_QUESTION"
        for value in decisions.values() if isinstance(value, dict)
    )
    merged["pending_total"] = max(0, int(root_total) - len(decisions))
    merged["pending_unprocessed"] = merged["pending_total"]

    previous_errors = [str(x) for x in previous.get("provider_errors") or [] if str(x)]
    current_errors = [str(x) for x in merged.get("provider_errors") or [] if str(x)]
    merged["provider_errors"] = list(dict.fromkeys([*previous_errors, *current_errors]))
    merged["principle"] = (
        "Alpha 10.1 resumable proof: each addressable normative packet is consumed only after a real Judge decision "
        "and, for SUPPORTS, a real Critic decision; only independent Judge/Critic SUPPORTS may create VERIFIED_OK. "
        "Provider failures leave unanswered packets pending."
    )
    return merged


def run_normative_semantic_proof(
    queue: list[dict[str, Any]] | None,
    *,
    judge_provider: Any = None,
    critic_provider: Any = None,
    limit: int = 24,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run only unprocessed packets and accumulate completed decisions.

    ``checkpoint`` is optional for deterministic non-Streamlit callers. The
    interactive app still falls back to the persisted project checkpoint.
    """
    source = [dict(x) for x in (queue or []) if isinstance(x, dict)]
    previous = dict(checkpoint) if isinstance(checkpoint, dict) else _previous_checkpoint()
    queue_fp = _semantic.queue_fingerprint(source)
    previous_root = str(previous.get("root_fingerprint") or previous.get("fingerprint") or "")
    previous_total = int(previous.get("root_queue_total") or previous.get("queue_total") or 0)
    complete_previous = {
        key: value for key, value in dict(previous.get("decisions") or {}).items()
        if _decision_complete(value)
    }

    if previous_root and previous_root == queue_fp:
        # The caller supplied the complete unchanged root queue.
        carried = complete_previous
        pending = [
            packet for packet in source
            if _packet_requirement_id(packet) not in carried
        ]
        root_fingerprint = previous_root
        root_total = max(previous_total, len(source))
    else:
        # In the Streamlit runtime the button receives the already-resolved
        # pending slice produced by apply_normative_semantic_proof().  Knowledge
        # expansion can make that slice larger than the old root.  Decisions
        # absent from this current pending slice have already been safely reused
        # by the apply gate and must survive the next partial AI run.  A previous
        # decision whose requirement is present in pending is deliberately NOT
        # carried: it must be re-evaluated fail-closed.
        current_ids = {_packet_requirement_id(packet) for packet in source}
        carried = {
            rid: decision for rid, decision in complete_previous.items()
            if rid not in current_ids
        }
        pending = list(source)
        root_fingerprint = queue_fp
        root_total = len(source) + len(carried)

    current = _ORIGINAL_RUN(
        pending,
        judge_provider=judge_provider,
        critic_provider=critic_provider,
        limit=limit,
    )
    current["selected_this_run"] = int(current.get("selected") or 0)
    current["pending_before_run"] = len(pending)
    return _merge_result(
        current,
        previous,
        root_fingerprint=root_fingerprint,
        root_total=root_total,
        previous_decisions_override=carried,
    )


def apply_normative_semantic_proof(
    proof_result: dict[str, Any],
    semantic_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """Apply cumulative decisions and expose only genuinely pending packets."""
    proof = dict(proof_result or {})
    full_queue = [dict(x) for x in (proof.get("semantic_queue") or []) if isinstance(x, dict)]
    expected = _semantic.queue_fingerprint(full_queue)
    semantic = dict(semantic_result or {})
    fingerprint = str(semantic.get("fingerprint") or "")
    root = str(semantic.get("root_fingerprint") or fingerprint or "")

    # Delegate compatibility to the base semantic-proof layer. It can reuse an
    # individual decision when the requirement and Judge-selected evidence are
    # unchanged even if the complete retrieval candidate pool/root fingerprint
    # has changed. Alpha 10 must not reintroduce a coarser whole-queue gate.
    compatible = dict(semantic)
    compatible["decisions"] = {
        key: value for key, value in dict(semantic.get("decisions") or {}).items()
        if _decision_complete(value)
    }
    exact_root = bool(semantic and root == expected and (not fingerprint or fingerprint == expected))
    if exact_root:
        compatible["fingerprint"] = expected
        compatible["root_fingerprint"] = expected

    result = _ORIGINAL_APPLY(proof, compatible)

    processed_decisions = {}
    for row in result.get("rows") or []:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("requirement_id") or "")
        decision = row.get("semantic_proof")
        if rid and _decision_complete(decision):
            processed_decisions[rid] = dict(decision)

    processed_ids = set(processed_decisions)
    pending = [packet for packet in full_queue if _packet_requirement_id(packet) not in processed_ids]
    confirmed = sum(
        str(value.get("state") or "").upper() == "VERIFIED_OK"
        for value in processed_decisions.values()
    )
    reviewed = sum(
        str(value.get("state") or "").upper() == "REVIEW_QUESTION"
        for value in processed_decisions.values()
    )

    result["semantic_queue_full_total"] = len(full_queue)
    result["semantic_queue_processed"] = len(processed_ids)
    result["semantic_completed_total"] = len(processed_ids)
    result["semantic_queue_confirmed"] = confirmed
    result["semantic_queue_reviewed"] = reviewed
    result["semantic_reviewed_no_promotion"] = reviewed
    result["semantic_queue"] = pending
    result["semantic_queue_total"] = len(pending)
    result["semantic_queue_evidence"] = sum(len(packet.get("evidence") or []) for packet in pending)

    initial_demoted = int(
        result.get("demoted_keyword_only_initial")
        or result.get("demoted_keyword_only")
        or 0
    )
    frontier = proof_frontier_summary(
        list(result.get("rows") or []),
        pending_requirement_ids={
            _packet_requirement_id(packet)
            for packet in pending
            if _packet_requirement_id(packet)
        },
    )
    result["demoted_keyword_only_initial"] = initial_demoted
    result["demoted_keyword_only_remaining"] = int(frontier.get("held_total") or 0)
    # The primary UI metric is the live remainder. Keep the initial gate count
    # separately for audit and before/after comparison.
    result["demoted_keyword_only"] = result["demoted_keyword_only_remaining"]
    result["proof_frontier"] = frontier

    summary = dict(result.get("semantic_proof_summary") or {})
    if semantic:
        summary.update({
            "version": ENGINE_VERSION,
            "root_fingerprint": root or expected,
            "current_queue_fingerprint": expected,
            "queue_fingerprint_match": exact_root,
            "root_queue_total": max(
                len(full_queue),
                int(semantic.get("root_queue_total") or semantic.get("queue_total") or 0),
            ),
            "processed_total": len(processed_ids),
            "verified_ok": confirmed,
            "reviewed_total": reviewed,
            "pending_total": len(pending),
        })
        result["semantic_proof_summary"] = summary
    return result


def install() -> None:
    """Install the overlay before UI and execution modules bind the functions."""
    global _INSTALLED
    if _INSTALLED:
        return
    _semantic.run_normative_semantic_proof = run_normative_semantic_proof
    _semantic.apply_normative_semantic_proof = apply_normative_semantic_proof
    _INSTALLED = True


__all__ = [
    "ENGINE_VERSION",
    "install",
    "run_normative_semantic_proof",
    "apply_normative_semantic_proof",
]
