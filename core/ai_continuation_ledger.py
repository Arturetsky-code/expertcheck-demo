from __future__ import annotations

"""Cumulative AI continuation ledger for ExpertCheck 18.4.1.

The project checkpoint is the source of truth for successful Judge/Critic
responses.  Public counters are derived from the union of current evidence
packets, persisted checkpoint packet ids and the previous ledger, so a resumed
slice can never make completed work disappear from the report.
"""

from typing import Any, Iterable

LEDGER_VERSION = "18.4.1-cumulative-ai-ledger-v2"
_CATEGORICAL_JUDGE = {"SUPPORTS", "CONTRADICTS"}


def _packet_id(row: dict[str, Any]) -> str:
    packet = row.get("semantic_evidence_packet")
    if not isinstance(packet, dict):
        return ""
    return str(packet.get("packet_id") or "").strip()


def packet_ids_from_rows(rows: Iterable[dict[str, Any]]) -> set[str]:
    """Return only packets that are actually eligible for Judge.

    Every atomic row may carry a semantic_evidence_packet (L0-L4), but the
    runtime sends only L4 packets whose checker explicitly allows consensus.
    Counting all packet ids made old snapshots look like hundreds of pending
    AI calls even though most rows were not eligible for semantic judgement.
    """
    packet_ids: set[str] = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        packet = row.get("semantic_evidence_packet")
        if not isinstance(packet, dict):
            continue
        if str(packet.get("evidence_level") or "").upper() != "L4":
            continue
        checker = packet.get("checker")
        if not isinstance(checker, dict) or not bool(checker.get("consensus_eligible")):
            continue
        packet_id = str(packet.get("packet_id") or "").strip()
        if packet_id:
            packet_ids.add(packet_id)
    return packet_ids


def _lane(checkpoint_domain: dict[str, Any] | None, role: str) -> dict[str, dict[str, Any]]:
    domain = checkpoint_domain if isinstance(checkpoint_domain, dict) else {}
    lane = domain.get(role)
    if not isinstance(lane, dict):
        return {}
    return {
        str(packet_id): dict(value)
        for packet_id, value in lane.items()
        if packet_id and isinstance(value, dict)
    }


def _previous_ids(previous_ledger_domain: dict[str, Any] | None) -> set[str]:
    previous = previous_ledger_domain if isinstance(previous_ledger_domain, dict) else {}
    return {str(value) for value in previous.get("packet_ids") or [] if str(value)}


def _requires_critic(judge: dict[str, Any]) -> bool:
    return str(judge.get("verdict") or "").upper() in _CATEGORICAL_JUDGE


def _last_runtime_event(audit: dict[str, Any], role: str) -> dict[str, Any]:
    calls = audit.get("critic_calls" if role == "CRITIC" else "judge_calls")
    if not isinstance(calls, list):
        return {}
    for call in reversed(calls):
        if not isinstance(call, dict) or not call.get("attempt"):
            continue
        state = str(call.get("runtime_state") or call.get("state") or "")
        error = str(call.get("error") or "")
        status = call.get("status_code")
        if state or error or status:
            return {
                "role": role,
                "state": state,
                "status_code": status,
                "provider": str(call.get("actual_provider") or call.get("configured_provider") or ""),
                "model": str(call.get("model") or ""),
                "error": error[:1200],
                "packet_ids": [str(value) for value in call.get("packet_ids") or []],
            }
    return {}


def reconcile_domain_audit(
    audit: dict[str, Any] | None,
    *,
    rows: Iterable[dict[str, Any]],
    checkpoint_domain: dict[str, Any] | None,
    previous_audit: dict[str, Any] | None = None,
    previous_ledger_domain: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return monotonic counters and a compact persistent domain ledger."""

    current = dict(audit or {})
    previous = dict(previous_audit or {})
    judge = _lane(checkpoint_domain, "judge")
    critic = _lane(checkpoint_domain, "critic")

    packet_ids = packet_ids_from_rows(rows)
    packet_ids.update(judge)
    packet_ids.update(critic)
    packet_ids.update(_previous_ids(previous_ledger_domain))

    # A previous build may know the aggregate total but not every packet id.
    # Preserve that number monotonically while migration discovers ids again.
    known_total = len(packet_ids)
    legacy_total = max(
        int(previous.get("cumulative_packet_total") or 0),
        int(previous.get("judge_candidates") or 0),
        int(current.get("judge_candidates") or 0),
        int((previous_ledger_domain or {}).get("packet_total") or 0),
    )
    packet_total = max(known_total, legacy_total)

    judge_ids = set(judge)
    critic_required_ids = {
        packet_id for packet_id, value in judge.items()
        if _requires_critic(value)
    }
    # Existing Critic responses are proof that a packet required Critic even if
    # an older raw Judge payload was compacted.
    critic_required_ids.update(critic)
    critic_ids = set(critic).intersection(critic_required_ids)

    judge_done = len(judge_ids)
    critic_required = len(critic_required_ids)
    critic_done = len(critic_ids)

    identified_pending = {
        packet_id for packet_id in packet_ids
        if packet_id not in judge_ids
        or (packet_id in critic_required_ids and packet_id not in critic_ids)
    }
    unidentified = max(0, packet_total - len(packet_ids))
    packages_pending = len(identified_pending) + unidentified
    packages_complete = max(0, packet_total - packages_pending)

    judge_pending = max(0, packet_total - judge_done)
    critic_pending = max(0, critic_required - critic_done)

    merged = dict(previous)
    merged.update(current)
    merged.update({
        "cumulative_ledger_version": LEDGER_VERSION,
        "cumulative_packet_total": packet_total,
        "judge_candidates": packet_total,
        "judge_responses": judge_done,
        "judge_pending": judge_pending,
        "not_selected": 0,
        "queue_remaining": judge_pending,
        "critic_required": critic_required,
        "critic_responses": critic_done,
        "critic_pending": critic_pending,
        "cumulative_responses": judge_done + critic_done,
        "unique_packages_complete": packages_complete,
        "unique_packages_pending": packages_pending,
        "package_completion_pct": round(100.0 * packages_complete / packet_total, 1) if packet_total else 100.0,
    })

    judge_event = _last_runtime_event(current, "JUDGE")
    critic_event = _last_runtime_event(current, "CRITIC")
    if judge_event:
        merged["last_judge_runtime_event"] = judge_event
    elif previous.get("last_judge_runtime_event"):
        merged["last_judge_runtime_event"] = dict(previous["last_judge_runtime_event"])
    if critic_event:
        merged["last_critic_runtime_event"] = critic_event
    elif previous.get("last_critic_runtime_event"):
        merged["last_critic_runtime_event"] = dict(previous["last_critic_runtime_event"])

    ledger = {
        "version": LEDGER_VERSION,
        "packet_total": packet_total,
        "packet_ids": sorted(packet_ids),
        "judge_ids": sorted(judge_ids),
        "critic_required_ids": sorted(critic_required_ids),
        "critic_ids": sorted(critic_ids),
        "judge_done": judge_done,
        "judge_pending": judge_pending,
        "critic_required": critic_required,
        "critic_done": critic_done,
        "critic_pending": critic_pending,
        "packages_complete": packages_complete,
        "packages_pending": packages_pending,
    }
    return merged, ledger


def queue_status_from_document(
    doc: dict[str, Any],
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    semantic = dict(doc.get("semantic_evidence_engine") or {})
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    root_ledger = checkpoint.get("_ledger") if isinstance(checkpoint.get("_ledger"), dict) else {}
    ledger_domains = dict((root_ledger or {}).get("domains") or {})

    assignment_rows = list(doc.get("assignment_atomic_compliance") or [])
    checklist_review = dict(doc.get("automatic_checklist_review") or {})
    checklist_atomic = dict(checklist_review.get("atomic_verification") or {})
    checklist_rows = list(checklist_atomic.get("atoms") or [])

    domain_rows = {"assignment": assignment_rows, "checklist": checklist_rows}
    totals = {
        "eligible": 0,
        "responses": 0,
        "judge_done": 0,
        "judge_remaining": 0,
        "critic_required": 0,
        "critic_done": 0,
        "critic_remaining": 0,
        "packages_complete": 0,
        "packages_remaining": 0,
        "quota_events": [],
        "domains": {},
    }

    for domain in ("assignment", "checklist"):
        audit = dict(semantic.get(domain) or {})
        if checkpoint:
            reconciled, ledger = reconcile_domain_audit(
                audit,
                rows=domain_rows[domain],
                checkpoint_domain=checkpoint.get(domain),
                previous_audit=audit,
                previous_ledger_domain=ledger_domains.get(domain),
            )
        else:
            reconciled = audit
            ledger = dict(ledger_domains.get(domain) or {})

        packet_total = int(reconciled.get("cumulative_packet_total") or reconciled.get("judge_candidates") or ledger.get("packet_total") or 0)
        judge_done = int(reconciled.get("judge_responses") or ledger.get("judge_done") or 0)
        judge_remaining = int(reconciled.get("judge_pending") or ledger.get("judge_pending") or max(0, packet_total - judge_done))
        critic_required = int(reconciled.get("critic_required") or ledger.get("critic_required") or 0)
        critic_done = int(reconciled.get("critic_responses") or ledger.get("critic_done") or 0)
        critic_remaining = int(reconciled.get("critic_pending") or ledger.get("critic_pending") or max(0, critic_required - critic_done))
        packages_complete = int(reconciled.get("unique_packages_complete") or ledger.get("packages_complete") or 0)
        packages_remaining = int(reconciled.get("unique_packages_pending") or ledger.get("packages_pending") or max(0, packet_total - packages_complete))

        domain_state = {
            "packet_total": packet_total,
            "judge_done": judge_done,
            "judge_remaining": judge_remaining,
            "critic_required": critic_required,
            "critic_done": critic_done,
            "critic_remaining": critic_remaining,
            "packages_complete": packages_complete,
            "packages_remaining": packages_remaining,
        }
        totals["domains"][domain] = domain_state
        totals["eligible"] += packet_total
        totals["judge_done"] += judge_done
        totals["judge_remaining"] += judge_remaining
        totals["critic_required"] += critic_required
        totals["critic_done"] += critic_done
        totals["critic_remaining"] += critic_remaining
        totals["responses"] += judge_done + critic_done
        totals["packages_complete"] += packages_complete
        totals["packages_remaining"] += packages_remaining

        for key in ("last_judge_runtime_event", "last_critic_runtime_event"):
            event = reconciled.get(key)
            if not isinstance(event, dict):
                continue
            state = str(event.get("state") or "").upper()
            status = event.get("status_code")
            if status == 429 or "QUOTA" in state or "RATE_LIMIT" in state:
                totals["quota_events"].append(dict(event))

    totals["judge"] = totals["judge_remaining"]
    totals["critic"] = totals["critic_remaining"]
    totals["total"] = totals["packages_remaining"]
    totals["operation_remaining"] = totals["judge_remaining"] + totals["critic_remaining"]
    totals["completion_pct"] = round(
        100.0 * totals["packages_complete"] / totals["eligible"], 1
    ) if totals["eligible"] else 100.0
    return totals
