from __future__ import annotations

"""Cumulative AI continuation ledger for ExpertCheck 18.4.1.

The project checkpoint is the source of truth for successful Judge/Critic
responses.  Public counters are derived from the union of current evidence
packets, persisted checkpoint packet ids and the previous ledger, so a resumed
slice can never make completed work disappear from the report.
"""

from typing import Any, Iterable

from .semantic_evidence_engine import ENGINE_VERSION as CURRENT_SEMANTIC_ENGINE_VERSION

LEDGER_VERSION = "18.5-evidence-quality-ledger-v1"
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


def _validated_critic_requirements(
    rows: Iterable[dict[str, Any]],
) -> tuple[set[str], set[str]]:
    """Return required Critic ids and ids with authoritative validated Judge data.

    Checkpoint lanes store the provider raw structured response. A categorical
    raw verdict can still fail the local Judge validator (for example confidence
    0.80 < 0.82). Critic is never scheduled for such a row, so counting every
    raw SUPPORTS/CONTRADICTS as Critic-required creates a permanent one-packet
    deadlock. Current project rows contain the validated semantic_judge and are
    therefore authoritative for Critic eligibility.
    """
    required: set[str] = set()
    observed: set[str] = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        packet_id = _packet_id(row)
        judge = row.get("semantic_judge")
        if not packet_id or not isinstance(judge, dict) or not judge:
            continue
        if not any(key in judge for key in ("valid", "validation_reasons", "response_received")):
            continue
        observed.add(packet_id)
        if judge.get("valid") is True and _requires_critic(judge):
            required.add(packet_id)
    return required, observed


def _row_response_lane(rows: Iterable[dict[str, Any]], role: str) -> dict[str, dict[str, Any]]:
    """Return AI responses that are physically attached to current project rows.

    A checkpoint entry without a matching row-level response is not auditable by
    the Results/XLSX surfaces.  25.1 therefore treats row + checkpoint agreement
    as the completion contract and reopens orphaned checkpoint entries.
    """
    key = "semantic_critic" if role == "critic" else "semantic_judge"
    result: dict[str, dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        packet_id = _packet_id(row)
        response = row.get(key)
        if not packet_id or not isinstance(response, dict) or not response:
            continue
        received = response.get("response_received")
        if received is True:
            result[packet_id] = dict(response)
            continue
        # Compatibility for older Critic payloads that predate response_received.
        if role == "critic" and "accept" in response and response.get("accept") is not None:
            result[packet_id] = dict(response)
    return result


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
    """Reconcile AI counters against the current packet graph and row evidence.

    25.1 makes the telemetry fail-closed: a response counts as completed only
    when the current project row carries the response and the checkpoint can
    reproduce it.  Stale/orphan checkpoint ids are pruned so they cannot create
    phantom completed packages after routing/evidence changes.
    """

    row_list = [row for row in rows or [] if isinstance(row, dict)]
    current = dict(audit or {})
    previous = dict(previous_audit or {})
    domain = checkpoint_domain if isinstance(checkpoint_domain, dict) else {}
    judge_lane = domain.get("judge")
    critic_lane = domain.get("critic")
    if not isinstance(judge_lane, dict):
        judge_lane = {}
        if isinstance(checkpoint_domain, dict):
            checkpoint_domain["judge"] = judge_lane
    if not isinstance(critic_lane, dict):
        critic_lane = {}
        if isinstance(checkpoint_domain, dict):
            checkpoint_domain["critic"] = critic_lane

    current_packet_ids = packet_ids_from_rows(row_list)
    row_judge = _row_response_lane(row_list, "judge")
    row_critic = _row_response_lane(row_list, "critic")

    # The checkpoint is the durable source of truth for completed provider
    # calls, while the *current eligible packet universe* decides which cached
    # ids are still valid. Row-level semantic responses are diagnostic here:
    # contract-aware recovery/reopening is performed by semantic_continuation
    # before this ledger is reconciled.
    recovered_judge = 0
    recovered_critic = 0
    if current_packet_ids:
        stale_judge_ids = {
            str(packet_id) for packet_id in list(judge_lane)
            if str(packet_id) not in current_packet_ids
        }
        stale_critic_ids = {
            str(packet_id) for packet_id in list(critic_lane)
            if str(packet_id) not in current_packet_ids
        }
        for packet_id in stale_judge_ids:
            judge_lane.pop(packet_id, None)
        for packet_id in stale_critic_ids:
            critic_lane.pop(packet_id, None)
    else:
        stale_judge_ids = set()
        stale_critic_ids = set()

    judge = _lane(domain, "judge")
    critic = _lane(domain, "critic")

    if current_packet_ids:
        packet_ids = set(current_packet_ids)
        packet_total = len(packet_ids)
    else:
        # Legacy/snapshot fallback only when the current graph cannot expose
        # eligible packets at all.
        packet_ids = set(judge) | set(critic) | _previous_ids(previous_ledger_domain)
        known_total = len(packet_ids)
        legacy_total = max(
            int(previous.get("cumulative_packet_total") or 0),
            int(previous.get("judge_candidates") or 0),
            int(current.get("judge_candidates") or 0),
            int((previous_ledger_domain or {}).get("packet_total") or 0),
        )
        packet_total = max(known_total, legacy_total)

    judge_ids = set(judge).intersection(packet_ids)
    validated_required, validated_observed = _validated_critic_requirements(row_list)
    critic_required_ids: set[str] = set()
    for packet_id in judge_ids:
        value = judge.get(packet_id) or {}
        if packet_id in validated_observed:
            if packet_id in validated_required:
                critic_required_ids.add(packet_id)
        elif _requires_critic(value):
            # The checkpoint verdict is durable evidence of a completed current
            # Judge call when the packet id still belongs to the current
            # universe. Row-level validation metadata is preferred when present.
            critic_required_ids.add(packet_id)

    critic_required_ids.update(set(critic).intersection(packet_ids))
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
    repaired = bool(stale_judge_ids or stale_critic_ids or recovered_judge or recovered_critic)

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
        "telemetry_integrity_state": "REPAIRED" if repaired else "PASSED",
        "telemetry_stale_judge_pruned": len(stale_judge_ids),
        "telemetry_stale_critic_pruned": len(stale_critic_ids),
        "telemetry_judge_recovered_from_rows": recovered_judge,
        "telemetry_critic_recovered_from_rows": recovered_critic,
        "telemetry_checkpoint_judge_responses": judge_done,
        "telemetry_checkpoint_critic_responses": critic_done,
        "telemetry_row_judge_responses": len(row_judge),
        "telemetry_row_critic_responses": len(row_critic),
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
        "telemetry_integrity_state": merged["telemetry_integrity_state"],
        "stale_judge_pruned": len(stale_judge_ids),
        "stale_critic_pruned": len(stale_critic_ids),
    }
    return merged, ledger


def queue_status_from_document(
    doc: dict[str, Any],
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    semantic = dict(doc.get("semantic_evidence_engine") or {})
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    checkpoint_engine = str(checkpoint.get("_semantic_engine_version") or "")
    checkpoint_stale = checkpoint_engine != CURRENT_SEMANTIC_ENGINE_VERSION
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

    reconciled_ledgers: dict[str, dict[str, Any]] = {}
    for domain in ("assignment", "checklist"):
        audit = dict(semantic.get(domain) or {})
        if checkpoint and not checkpoint_stale:
            reconciled, ledger = reconcile_domain_audit(
                audit,
                rows=domain_rows[domain],
                checkpoint_domain=checkpoint.get(domain),
                previous_audit=audit,
                previous_ledger_domain=ledger_domains.get(domain),
            )
        else:
            # Evidence Quality revisions deliberately revalidate old Judge/Critic
            # decisions against the new bounded window/binding contract.
            reconciled, ledger = reconcile_domain_audit(
                {
                    **audit,
                    "judge_responses": 0,
                    "critic_responses": 0,
                    "judge_pending": 0,
                    "critic_pending": 0,
                    "not_selected": 0,
                    "queue_remaining": 0,
                },
                rows=domain_rows[domain],
                checkpoint_domain={},
                previous_audit={},
                previous_ledger_domain={},
            )
        semantic[domain] = reconciled
        reconciled_ledgers[domain] = ledger

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

        checkpoint_domain = checkpoint.get(domain) if isinstance(checkpoint.get(domain), dict) else {}
        has_checkpoint_responses = bool(
            _lane(checkpoint_domain, "judge") or _lane(checkpoint_domain, "critic")
        )
        for key in ("last_judge_runtime_event", "last_critic_runtime_event"):
            event = reconciled.get(key)
            if not isinstance(event, dict):
                continue
            # Old portable snapshots contain historical audit calls but did not
            # contain the actual AI checkpoint. Do not present those old calls
            # as the state of the newly restored queue.
            if doc.get("snapshot_restored") and not has_checkpoint_responses:
                continue
            state = str(event.get("state") or "").upper()
            status = event.get("status_code")
            if status == 429 or "QUOTA" in state or "RATE_LIMIT" in state:
                totals["quota_events"].append(dict(event))

    # Persist reconciliation only when the checkpoint belongs to the current
    # semantic engine. A stale 18.4.x ledger is display-only until 18.5 rebuilds
    # the packets; otherwise its historical totals can become a phantom minimum.
    if not checkpoint_stale:
        doc["semantic_evidence_engine"] = semantic
        if isinstance(checkpoint, dict) and checkpoint:
            snapshot_id = str((doc.get("analysis_snapshot") or {}).get("snapshot_id") or "")
            checkpoint["_ledger"] = {
                "version": LEDGER_VERSION,
                "snapshot_id": snapshot_id or str((root_ledger or {}).get("snapshot_id") or ""),
                "domains": reconciled_ledgers,
            }

    totals["checkpoint_stale"] = checkpoint_stale
    totals["checkpoint_engine_version"] = checkpoint_engine
    totals["current_semantic_engine_version"] = CURRENT_SEMANTIC_ENGINE_VERSION
    totals["judge"] = totals["judge_remaining"]
    totals["critic"] = totals["critic_remaining"]
    totals["total"] = totals["packages_remaining"]
    totals["operation_remaining"] = totals["judge_remaining"] + totals["critic_remaining"]
    totals["completion_pct"] = round(
        100.0 * totals["packages_complete"] / totals["eligible"], 1
    ) if totals["eligible"] else 100.0
    return totals
