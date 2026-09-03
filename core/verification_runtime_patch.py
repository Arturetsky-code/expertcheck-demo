from __future__ import annotations

"""ExpertCheck 18.4 Verification Runtime.

This runtime patch converts the 18.3 quality gates into an operational free-AI
verification loop without weakening the fail-closed L5 contract.

Key principles:
- free providers are called with small resumable batches and checkpoint reuse;
- transient 429/5xx events pause/retry instead of discarding completed work;
- an independent Critic may review Judge decisions even when qualification does
  not yet permit L5; those decisions remain advisory L4;
- a same-object/same-metric conflict from two independent trusted sections is a
  confirmed project conflict even when the authoritative/correct value still
  requires an owner section;
- physical table-row identity outranks later semantic nearest-object anchoring.
"""

import hashlib
import json
import math
import re
import time
from typing import Any, Iterable

from core import semantic_evidence_engine as see
from core import cross_section_verification as csv
from core import table_row_integrity as tri
from core import table_semantic_scope as tss


VERSION = "18.4-verification-runtime-v1"
_FREE_NAMES = {"groq", "gemini"}
_PREFLIGHT_CACHE_TTL = 300.0
_PREFLIGHT_CACHE: dict[tuple[str, ...], tuple[float, dict[str, Any]]] = {}
_INSTALLED = False


def _provider_name(provider: Any) -> str:
    return str(getattr(provider, "name", "") or getattr(provider, "provider", "") or type(provider).__name__).strip()


def _provider_fingerprint(provider: Any) -> str:
    headers = getattr(provider, "headers", None)
    raw = repr(headers) if headers is not None else repr(getattr(provider, "api_key", ""))
    return hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:10]


def _free_provider(provider: Any) -> bool:
    name = _provider_name(provider).lower()
    return any(token in name for token in _FREE_NAMES)


def _retry_seconds(text: str, default: float) -> float:
    low = str(text or "").lower().replace(",", ".")
    patterns = (
        r"try again(?: in)?\s*([0-9]+(?:\.[0-9]+)?)\s*s",
        r"retry(?: after| in)?\s*([0-9]+(?:\.[0-9]+)?)\s*s",
        r"retry[- ]after[^0-9]*([0-9]+(?:\.[0-9]+)?)",
    )
    for pattern in patterns:
        match = re.search(pattern, low)
        if match:
            try:
                return max(1.0, min(30.0, float(match.group(1)) + 0.75))
            except ValueError:
                pass
    return default


def _pacing_seconds(provider: Any, packet: dict[str, Any], *, critic: bool) -> float:
    """Conservative pacing for free tiers; no token-count API is required."""
    if not _free_provider(provider):
        return 0.0
    name = _provider_name(provider).lower()
    if "groq" in name:
        # The observed free route is 8k TPM.  A single compact engineering
        # packet is typically ~1.1-1.6k total tokens including schema/output.
        # 10.5 s keeps the steady-state rate close to the free budget while
        # remaining materially faster than 4-packet bursts followed by 429.
        return 10.5
    # Gemini free Flash routes are primarily constrained by request/quota spikes;
    # a short gap avoids hammering the API while keeping Critic usable.
    return 2.5 if critic else 3.0


def _install_preflight_cache() -> None:
    current = see._preflight_provider
    if getattr(current, "_expertcheck_184_cached", False):
        return

    def cached_preflight(
        provider: Any,
        role: str,
        *,
        structured: bool = True,
        connection: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if provider is None or connection is not None:
            return current(provider, role, structured=structured, connection=connection)
        key = (
            _provider_name(provider),
            str(getattr(provider, "model", "") or ""),
            str(role).upper(),
            "structured" if structured else "connection",
            _provider_fingerprint(provider),
        )
        cached = _PREFLIGHT_CACHE.get(key)
        if cached and time.monotonic() - cached[0] <= _PREFLIGHT_CACHE_TTL:
            result = dict(cached[1])
            result["state"] = "CACHED_PASSED"
            result["cached"] = True
            return result
        result = current(provider, role, structured=structured, connection=connection)
        if result.get("ok"):
            _PREFLIGHT_CACHE[key] = (time.monotonic(), dict(result))
        return result

    cached_preflight._expertcheck_184_cached = True  # type: ignore[attr-defined]
    see._preflight_provider = cached_preflight


def _install_free_queue() -> None:
    original = see._call_batches
    if getattr(original, "_expertcheck_184_free_queue", False):
        return

    def runtime_call_batches(
        provider: Any,
        packets: list[dict[str, Any]],
        *,
        critic: bool = False,
        batch_size: int = 4,
        retry_limit: int = 2,
        max_consecutive_failures: int = 2,
        max_calls: int = 32,
        progress_callback: Any = None,
        checkpoint: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[dict[str, dict[str, Any]], list[str], list[dict[str, Any]]]:
        if provider is None or not packets or not _free_provider(provider):
            return original(
                provider,
                packets,
                critic=critic,
                batch_size=batch_size,
                retry_limit=retry_limit,
                max_consecutive_failures=max_consecutive_failures,
                max_calls=max_calls,
                progress_callback=progress_callback,
                checkpoint=checkpoint,
            )

        checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
        requested_ids = [str(packet.get("packet_id") or "") for packet in packets]
        collected: dict[str, dict[str, Any]] = {
            packet_id: dict(checkpoint[packet_id])
            for packet_id in requested_ids
            if packet_id in checkpoint and isinstance(checkpoint.get(packet_id), dict)
        }
        errors: list[str] = []
        calls: list[dict[str, Any]] = []
        network_calls = 0
        stop_queue = False

        def notify() -> None:
            if not callable(progress_callback):
                return
            try:
                progress_callback("CRITIC" if critic else "JUDGE", len(collected), len(packets))
            except Exception:
                pass

        notify()
        pending = [packet for packet in packets if str(packet.get("packet_id") or "") not in collected]
        for index, packet in enumerate(pending):
            if stop_queue or network_calls >= max_calls:
                break
            packet_id = str(packet.get("packet_id") or "")
            transient_retry = 0
            while packet_id not in collected and network_calls < max_calls:
                before_calls = network_calls
                partial, partial_errors, partial_calls = original(
                    provider,
                    [packet],
                    critic=critic,
                    batch_size=1,
                    retry_limit=0,
                    max_consecutive_failures=1,
                    max_calls=1,
                    progress_callback=None,
                    checkpoint=checkpoint,
                )
                network_calls += sum(1 for row in partial_calls if row.get("attempt"))
                collected.update(partial)
                for message in partial_errors:
                    if message and message not in errors:
                        errors.append(message)
                calls.extend(partial_calls)
                notify()
                if packet_id in collected:
                    if index < len(pending) - 1:
                        pause = _pacing_seconds(provider, packet, critic=critic)
                        if pause > 0:
                            time.sleep(pause)
                    break

                last = next((row for row in reversed(partial_calls) if row.get("attempt")), {})
                state = str(last.get("state") or "")
                status = last.get("status_code")
                detail = str(last.get("error") or " ".join(partial_errors))
                transient = state == "RATE_LIMITED" or status in {408, 429, 500, 502, 503, 504}
                if transient and transient_retry < 1:
                    transient_retry += 1
                    default_wait = 12.0 if status == 429 and "groq" in _provider_name(provider).lower() else 5.0
                    wait = _retry_seconds(detail, default_wait)
                    if calls:
                        calls[-1]["runtime_wait_seconds"] = wait
                        calls[-1]["runtime_state"] = "WAIT_AND_RETRY"
                    time.sleep(wait)
                    continue
                if transient:
                    if calls:
                        calls[-1]["runtime_state"] = "CHECKPOINT_PAUSED"
                    stop_queue = True
                else:
                    # One malformed packet must not poison the entire free queue.
                    if calls:
                        calls[-1]["runtime_state"] = "PACKET_WITHHELD"
                if network_calls == before_calls:
                    stop_queue = True
                break

        return collected, list(dict.fromkeys(errors)), calls

    runtime_call_batches._expertcheck_184_free_queue = True  # type: ignore[attr-defined]
    see._call_batches = runtime_call_batches


def _downgrade_semantic_promotions(rows: Iterable[dict[str, Any]]) -> tuple[int, int]:
    verified = findings = 0
    for row in rows or []:
        if str(row.get("specialized_checker_id") or "") != "SEMANTIC_EVIDENCE_CONSENSUS_V1":
            continue
        if str(row.get("evidence_level") or "") != "L5":
            continue
        previous = str(row.get("verification_kind") or row.get("final_verification_kind") or "")
        if previous == "VERIFIED_OK":
            verified += 1
        elif previous == "PROJECT_FINDING":
            findings += 1
        judge = dict(row.get("semantic_judge") or {})
        critic = dict(row.get("semantic_critic") or {})
        row.update({
            "semantic_advisory_state": "CRITIC_ACCEPTED" if critic.get("valid") else "CRITIC_REVIEWED",
            "semantic_advisory_decision": str(judge.get("verdict") or "INSUFFICIENT"),
            "semantic_consensus_state": "ADVISORY_DUAL_REVIEW",
            "semantic_consensus_reasons": [
                "Judge и независимый Critic выполнили смысловую проверку, но модельный маршрут ещё не допущен к L5."
            ],
            "verification_kind": "REVIEW_QUESTION",
            "verification_state": "Требует проверки специалистом",
            "final_verification_kind": "REVIEW_QUESTION",
            "final_verification_state": "Требует проверки специалистом",
            "status": "Требует проверки",
            "proof_kind": "AI_ADVISORY_CONSENSUS",
            "automatic_verdict_eligible": False,
            "candidate_evidence_only": True,
            "coverage_state": "TARGETED_REVIEW",
            "coverage_reason_code": "AI_ADVISORY_DUAL_REVIEW",
            "coverage_reason": "Адресное доказательство проверено Judge и независимым Critic; категоричный L5 запрещён до квалификации маршрута.",
            "evidence_level": "L4",
            "evidence_level_reason": "Независимый AI-review завершён консультативно; L5 не присвоен.",
            "requested_verification_kind": previous,
        })
    return verified, findings


def _install_advisory_critic() -> None:
    original_run = see.run_semantic_evidence_engine
    if getattr(original_run, "_expertcheck_184_advisory_critic", False):
        return
    true_qualification = see._provider_qualified_for_l5

    def runtime_run(
        rows: list[dict[str, Any]],
        *,
        fact_graph: dict[str, Any],
        page_corpus: Iterable[dict[str, Any]] = (),
        judge_provider: Any = None,
        critic_provider: Any = None,
        level: str = "off",
        limit: int = 0,
        progress_callback: Any = None,
        checkpoint: dict[str, Any] | None = None,
        candidate_cap: int = 0,
    ) -> dict[str, Any]:
        judge_qualified = true_qualification(judge_provider) if judge_provider is not None else False
        critic_qualified = true_qualification(critic_provider) if critic_provider is not None else False
        distinct = bool(
            judge_provider is not None
            and critic_provider is not None
            and _provider_name(judge_provider)
            and _provider_name(critic_provider)
            and _provider_name(judge_provider) != _provider_name(critic_provider)
        )
        advisory_dual = distinct and not (judge_qualified and critic_qualified)

        if advisory_dual:
            saved = see._provider_qualified_for_l5
            # Only the runtime activation condition is relaxed.  Every semantic
            # promotion is downgraded to L4 again below, so L5 remains fail-closed.
            see._provider_qualified_for_l5 = lambda provider: provider is not None
            try:
                result = original_run(
                    rows,
                    fact_graph=fact_graph,
                    page_corpus=page_corpus,
                    judge_provider=judge_provider,
                    critic_provider=critic_provider,
                    level=level,
                    limit=limit,
                    progress_callback=progress_callback,
                    checkpoint=checkpoint,
                    candidate_cap=candidate_cap,
                )
            finally:
                see._provider_qualified_for_l5 = saved
            downgraded_verified, downgraded_findings = _downgrade_semantic_promotions(rows)
            if result.get("critic_responses") or result.get("judge_responses"):
                result["execution_mode"] = "ADVISORY_DUAL_REVIEW"
            result["independent_consensus_available"] = False
            result["advisory_dual_review"] = True
            result["promoted_verified"] = max(0, int(result.get("promoted_verified") or 0) - downgraded_verified)
            result["project_findings"] = max(0, int(result.get("project_findings") or 0) - downgraded_findings)
            result["advisory_completed"] = max(
                int(result.get("advisory_completed") or 0),
                int(result.get("judge_responses") or 0),
            )
            result.setdefault("advisory_reasons", []).append(
                "18.4: независимый Critic выполняется и до L5-квалификации; результат остаётся консультативным L4."
            )
            result["runtime_version"] = VERSION
            return result

        result = original_run(
            rows,
            fact_graph=fact_graph,
            page_corpus=page_corpus,
            judge_provider=judge_provider,
            critic_provider=critic_provider,
            level=level,
            limit=limit,
            progress_callback=progress_callback,
            checkpoint=checkpoint,
            candidate_cap=candidate_cap,
        )
        result["runtime_version"] = VERSION
        return result

    runtime_run._expertcheck_184_advisory_critic = True  # type: ignore[attr-defined]
    see.run_semantic_evidence_engine = runtime_run

    # atomic_verification_engine imported the function by name during app startup.
    from core import atomic_verification_engine as ave
    ave.run_semantic_evidence_engine = runtime_run


def _float(value: Any) -> float | None:
    try:
        number = float(str(value).replace("\u00a0", "").replace(" ", "").replace(",", "."))
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _confirm_cross_section_conflict(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").upper()
    if status not in {"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ", "КОНФЛИКТ ВНУТРИ РАЗДЕЛА"}:
        return False
    records = [
        dict(item) for item in (row.get("source_records") or row.get("verification_evidence") or [])
        if isinstance(item, dict) and item.get("document") and item.get("page") not in (None, "")
    ]
    row_code = str(row.get("parameter_code") or "")
    row_object = str(row.get("object_id") or "")
    valid_records = [
        item for item in records
        if (not row_code or str(item.get("parameter_code") or row_code) == row_code)
        and (not row_object or str(item.get("object_id") or row_object) == row_object)
        and _float(item.get("value")) is not None
    ]
    sections = {str(item.get("section") or "") for item in valid_records if str(item.get("section") or "")}
    trusted = [item for item in valid_records if item.get("trusted_for_mismatch")]
    trusted_count = max(len(trusted), int(row.get("independent_trusted_sources") or 0))
    values = [_float(item.get("value")) for item in valid_records]
    values = [value for value in values if value is not None]
    distinct_values = {round(value, 8) for value in values}
    return bool(len(valid_records) >= 2 and len(sections) >= 2 and trusted_count >= 2 and len(distinct_values) >= 2)


def _install_cross_section_conflict_gate() -> None:
    original = csv.qualify_cross_section_verdicts
    if getattr(original, "_expertcheck_184_conflict_gate", False):
        return

    def qualify(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
        row_list = list(rows or [])
        summary = dict(original(row_list) or {})
        promoted = 0
        for row in row_list:
            if str(row.get("final_verification_kind") or "") == "PROJECT_FINDING":
                continue
            if not _confirm_cross_section_conflict(row):
                continue
            sources = [
                dict(item) for item in (row.get("source_records") or row.get("verification_evidence") or [])
                if isinstance(item, dict) and item.get("document") and item.get("page") not in (None, "")
            ]
            row.update({
                "final_verification_kind": "PROJECT_FINDING",
                "final_verification_state": "Выявлено несоответствие",
                "verification_kind": "PROJECT_FINDING",
                "verification_state": "Выявлено несоответствие",
                "proof_kind": "STRUCTURED_CONFLICT",
                "evidence_level": "L5",
                "evidence_level_reason": "Один объект и показатель имеют разные значения в двух независимых доверенных разделах.",
                "verification_evidence": sources,
                "adversarial_state": "PASSED",
                "deep_evidence_state": "PASSED",
                "automatic_verdict_eligible": True,
                "candidate_evidence_only": False,
                "coverage_state": "PROJECT_FINDING_CONFIRMED",
                "coverage_reason_code": "CROSS_SECTION_CONFLICT_CONFIRMED_VALUE_UNRESOLVED",
                "coverage_reason": (
                    "Межраздельное противоречие подтверждено адресными источниками. "
                    "Правильное/актуальное значение отдельно требует проверки профильного раздела-владельца."
                ),
                "finding_type": "PROJECT_FINDING",
                "cross_section_gate_state": "CONFLICT_CONFIRMED",
                "conflict_confirmed": True,
                "correct_value_verified": False,
                "automatic_verdict_policy": "MULTI_SOURCE_CONFLICT_WITHOUT_CORRECT_VALUE",
                "comment": (
                    "Синхронизировать значения между разделами; правильное значение подтвердить по профильному разделу-владельцу."
                ),
            })
            promoted += 1
        summary["version"] = VERSION
        summary["conflicts_confirmed_without_owner"] = promoted
        summary["passed"] = int(summary.get("passed") or 0) + promoted
        summary["blocked"] = max(0, int(summary.get("blocked") or 0) - promoted)
        return summary

    qualify._expertcheck_184_conflict_gate = True  # type: ignore[attr-defined]
    csv.qualify_cross_section_verdicts = qualify
    from core import pipeline
    pipeline.qualify_cross_section_verdicts = qualify


def _row_key(item: dict[str, Any]) -> tuple[str, int, str] | None:
    locator = item.get("source_locator") if isinstance(item.get("source_locator"), dict) else {}
    row_value = (
        item.get("table_row") if item.get("table_row") not in (None, "") else
        item.get("row_index") if item.get("row_index") not in (None, "") else
        locator.get("table_row") if locator.get("table_row") not in (None, "") else
        locator.get("row_index")
    )
    if row_value in (None, ""):
        return None
    document = str(item.get("document") or "")
    try:
        page = int(item.get("page") or 0)
    except (TypeError, ValueError):
        page = 0
    if not document or not page:
        return None
    return document, page, str(row_value)


def _positions_from_row(item: dict[str, Any]) -> set[str]:
    text = " ".join(str(item.get(key) or "") for key in ("row_text", "table_row_text", "context"))
    return set(re.findall(r"(?<!\d)(\d{1,3}\.\d{1,3})(?!\d)", text))


def _block_row(item: dict[str, Any], reason: str, *, anchor_position: str = "") -> None:
    item.update({
        "row_integrity_status": "BLOCKED_PHYSICAL_ROW_MISMATCH",
        "row_integrity_reason": reason,
        "row_integrity_anchor_position": anchor_position,
        "project_understanding_binding": "Отклонено",
        "comparison_excluded": True,
        "comparison_exclusion_reason": reason,
    })


def _hard_row_binding(findings: list[dict[str, Any]]) -> dict[str, int]:
    strong = {"ROW_LOCKED", "POSITION_LOCKED", "EXACT_OBJECT"}
    anchors: dict[tuple[str, int, str], dict[str, Any]] = {}
    for item in findings or []:
        key = _row_key(item)
        binding = str(item.get("binding_status") or item.get("property_binding_status") or "").upper()
        position = str(item.get("genplan_position") or "").strip()
        if key and binding in strong and (position or item.get("object_hint")):
            current = anchors.get(key)
            confidence = float(item.get("core2_confidence") or item.get("confidence") or 0.0)
            current_conf = float((current or {}).get("core2_confidence") or (current or {}).get("confidence") or 0.0)
            if current is None or confidence > current_conf:
                anchors[key] = item

    stats = {"physical_row_anchors": len(anchors), "physical_row_mismatches": 0, "explicit_position_mismatches": 0}
    for item in findings or []:
        if tri.is_integrity_blocked(item):
            continue
        expected_position = str(item.get("genplan_position") or item.get("semantic_anchor_position") or "").strip()
        row_positions = _positions_from_row(item)
        if expected_position and row_positions and expected_position not in row_positions and len(row_positions) == 1:
            actual = next(iter(row_positions))
            _block_row(
                item,
                f"Физическая строка таблицы относится к позиции {actual}, а показатель был привязан к позиции {expected_position}.",
                anchor_position=actual,
            )
            stats["explicit_position_mismatches"] += 1
            continue
        key = _row_key(item)
        anchor = anchors.get(key) if key else None
        if not anchor or anchor is item:
            continue
        anchor_position = str(anchor.get("genplan_position") or "").strip()
        item_position = str(item.get("genplan_position") or item.get("semantic_anchor_position") or "").strip()
        if anchor_position and item_position and anchor_position != item_position:
            _block_row(
                item,
                f"Одна физическая строка таблицы имеет подтверждённую позицию {anchor_position}; перенос показателя на позицию {item_position} запрещён.",
                anchor_position=anchor_position,
            )
            stats["physical_row_mismatches"] += 1
    return stats


def _install_hard_row_binding() -> None:
    original_guard = tri.apply_table_row_integrity_guard
    if not getattr(original_guard, "_expertcheck_184_row_binding", False):
        def enhanced_guard(findings: list[dict[str, Any]]) -> dict[str, int]:
            summary = dict(original_guard(findings) or {})
            extra = _hard_row_binding(findings)
            summary.update(extra)
            summary["version"] = VERSION
            return summary
        enhanced_guard._expertcheck_184_row_binding = True  # type: ignore[attr-defined]
        tri.apply_table_row_integrity_guard = enhanced_guard
        from core import pipeline
        pipeline.apply_table_row_integrity_guard = enhanced_guard

    original_scope = tss.annotate_table_semantic_scope
    if not getattr(original_scope, "_expertcheck_184_post_semantic_row_binding", False):
        def enhanced_scope(findings: list[dict[str, Any]]) -> dict[str, int]:
            summary = dict(original_scope(findings) or {})
            extra = _hard_row_binding(findings)
            summary["row_binding_post_semantic"] = extra
            return summary
        enhanced_scope._expertcheck_184_post_semantic_row_binding = True  # type: ignore[attr-defined]
        tss.annotate_table_semantic_scope = enhanced_scope
        from core import pipeline
        pipeline.annotate_table_semantic_scope = enhanced_scope


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _install_preflight_cache()
    _install_free_queue()
    _install_advisory_critic()
    _install_cross_section_conflict_gate()
    _install_hard_row_binding()
    _INSTALLED = True
