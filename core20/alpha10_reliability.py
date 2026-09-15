from __future__ import annotations

"""Alpha 10 reliability overlay for the canonical normative proof workflow.

The overlay is deliberately small and reversible: it keeps the Alpha 9 proof
engine intact, but turns its semantic queue into a resumable queue. The full
proof queue remains the root contract; only packets without a persisted,
completed Judge/Critic decision are exposed for the next call.
"""

from typing import Any

from . import normative_semantic_proof as _semantic


ENGINE_VERSION = "20.0-alpha10-expert-workflow-reliability"
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

    Alpha 9 intentionally materialises REVIEW_QUESTION when a provider returns
    no answer. That is safe as a verdict, but it must not consume the resumable
    queue. A real non-SUPPORTS Judge answer is complete without Critic; SUPPORTS
    additionally requires an actual Critic answer (accept or reject).
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

    # If the current queue is already the pending subset produced by Alpha 10,
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
) -> dict[str, Any]:
    merged = dict(current or {})
    previous_root = str(previous.get("root_fingerprint") or previous.get("fingerprint") or "")
    previous_decisions = {
        key: value for key, value in dict(previous.get("decisions") or {}).items()
        if previous_root == root_fingerprint and _decision_complete(value)
    }
    current_decisions = {
        key: value for key, value in dict(merged.get("decisions") or {}).items()
        if _decision_complete(value)
    }
    decisions = {**previous_decisions, **current_decisions}

    merged["version"] = ENGINE_VERSION
    merged["root_fingerprint"] = root_fingerprint
    # Keep fingerprint compatible with the Alpha 9 apply gate. The fingerprint
    # identifies the complete root queue rather than one pending slice.
    merged["fingerprint"] = root_fingerprint
    merged["root_queue_total"] = int(root_total)
    merged["queue_total"] = int(root_total)
    merged["decisions"] = decisions
    merged["processed_total"] = len(decisions)
    merged["verified_ok"] = sum(
        str(value.get("state") or "").upper() == "VERIFIED_OK"
        for value in decisions.values() if isinstance(value, dict)
    )
    merged["reviewed_total"] = sum(
        str(value.get("state") or "").upper() == "REVIEW_QUESTION"
        for value in decisions.values() if isinstance(value, dict)
    )
    merged["pending_total"] = max(0, int(root_total) - len(decisions))

    previous_errors = [str(x) for x in previous.get("provider_errors") or [] if str(x)]
    current_errors = [str(x) for x in merged.get("provider_errors") or [] if str(x)]
    merged["provider_errors"] = list(dict.fromkeys([*previous_errors, *current_errors]))
    merged["principle"] = (
        "Alpha 10 resumable proof: each addressable normative packet is consumed only after a real Judge decision "
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
) -> dict[str, Any]:
    """Run only unprocessed packets and accumulate completed decisions."""
    source = [dict(x) for x in (queue or []) if isinstance(x, dict)]
    previous = _previous_checkpoint()
    root_fingerprint, root_total = _root_identity(previous, source)

    previous_root = str(previous.get("root_fingerprint") or previous.get("fingerprint") or "")
    previous_decisions = {
        key: value for key, value in dict(previous.get("decisions") or {}).items()
        if previous_root == root_fingerprint and _decision_complete(value)
    }
    pending = [packet for packet in source if _packet_requirement_id(packet) not in previous_decisions]

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

    # Preserve the Alpha 9 stale-check contract: an explicitly mismatched
    # fingerprint is always stale, even if a separate root_fingerprint remains.
    compatible_root = bool(semantic and root == expected and (not fingerprint or fingerprint == expected))
    if compatible_root:
        compatible = dict(semantic)
        compatible["fingerprint"] = expected
        compatible["decisions"] = {
            key: value for key, value in dict(semantic.get("decisions") or {}).items()
            if _decision_complete(value)
        }
        result = _ORIGINAL_APPLY(proof, compatible)
    else:
        result = _ORIGINAL_APPLY(proof, semantic)

    decisions = {
        key: value for key, value in dict(semantic.get("decisions") or {}).items()
        if compatible_root and _decision_complete(value)
    }
    processed_ids = set(decisions)
    pending = [packet for packet in full_queue if _packet_requirement_id(packet) not in processed_ids]
    confirmed = sum(
        str(value.get("state") or "").upper() == "VERIFIED_OK"
        for value in decisions.values() if isinstance(value, dict)
    )
    reviewed = sum(
        str(value.get("state") or "").upper() == "REVIEW_QUESTION"
        for value in decisions.values() if isinstance(value, dict)
    )

    result["semantic_queue_full_total"] = len(full_queue)
    result["semantic_queue_processed"] = len(processed_ids)
    result["semantic_queue_confirmed"] = confirmed
    result["semantic_queue_reviewed"] = reviewed
    result["semantic_queue"] = pending
    result["semantic_queue_total"] = len(pending)
    result["semantic_queue_evidence"] = sum(len(packet.get("evidence") or []) for packet in pending)

    summary = dict(result.get("semantic_proof_summary") or {})
    if compatible_root:
        summary.update({
            "version": ENGINE_VERSION,
            "root_fingerprint": expected,
            "root_queue_total": len(full_queue),
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
