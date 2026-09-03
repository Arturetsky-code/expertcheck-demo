from __future__ import annotations

import json
import math
import re
import statistics
import time
from collections import Counter, defaultdict
from typing import Any

from .semantic_evidence_engine import (
    JUDGE_JSON_SCHEMA,
    JUDGE_SYSTEM,
    _extract_json,
    valid_structured_contract,
)


BENCHMARK_VERSION = "18.1-provider-qualification-v2"
RELEASE_GATES = {
    "request_success_pct": 98.0,
    "schema_adherence_pct": 100.0,
    "semantic_accuracy_pct": 95.0,
    "false_positive_pct": 1.0,
    "repeatability_pct": 95.0,
}


def _case(
    case_id: str,
    requirement: str,
    evidence: str,
    expected: str,
    *,
    entity: str,
    property_code: str,
    category: str,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "category": category,
        "expected_verdict": expected,
        "packet": {
            "packet_id": case_id,
            "domain": "provider_benchmark",
            "requirement": requirement,
            "object": entity,
            "property_code": property_code,
            "required_modality": "EXPLICIT",
            "critical_qualifiers": [],
            "evidence": [{
                "evidence_id": f"{case_id}-E1",
                "source_locator": "DOC-A, стр. 1",
                "text": evidence,
            }],
            "policy": "Использовать только переданный фрагмент. Отсутствие доказательства не является несоответствием.",
        },
    }


def benchmark_cases() -> list[dict[str, Any]]:
    """Thirty synthetic, non-project packets spanning common failure modes."""
    cases: list[dict[str, Any]] = []
    for index in range(1, 6):
        entity = f"Корпус {index}"
        value = 100 + index * 10
        cases.extend([
            _case(
                f"PQ-NUM-{index:02d}",
                f"Для объекта «{entity}» производительность должна составлять {value} т/ч.",
                f"Производительность объекта «{entity}» составляет {value} т/ч.",
                "SUPPORTS", entity=entity, property_code="CAPACITY", category="EXACT_VALUE",
            ),
            _case(
                f"PQ-ENTITY-{index:02d}",
                f"Для объекта «{entity}» площадь застройки должна составлять {value} м².",
                f"Площадь застройки объекта «Склад {index}» составляет {value} м².",
                "OTHER_ENTITY", entity=entity, property_code="AREA_BUILD", category="ENTITY_BINDING",
            ),
            _case(
                f"PQ-METRIC-{index:02d}",
                f"Для объекта «{entity}» площадь застройки должна составлять {value} м².",
                f"Общая площадь объекта «{entity}» составляет {value} м².",
                "OTHER_METRIC", entity=entity, property_code="AREA_BUILD", category="METRIC_BINDING",
            ),
            _case(
                f"PQ-GENERIC-{index:02d}",
                f"Предусмотреть уширение обочины у барьерного дорожного ограждения участка {index}.",
                f"Территория участка {index} ограждается сетчатыми панелями высотой 2,0 м.",
                "INSUFFICIENT", entity=f"Участок {index}", property_code="ROAD_SHOULDER_WIDENING", category="FALSE_LEXICAL_MATCH",
            ),
            _case(
                f"PQ-PRESENCE-{index:02d}",
                f"В разделе должен быть представлен расчёт численности персонала объекта «{entity}».",
                f"Расчёт численности персонала объекта «{entity}»: ИТР — {index + 2}, рабочие — {index + 8}.",
                "SUPPORTS", entity=entity, property_code="STAFF_CALCULATION", category="EXPLICIT_PRESENCE",
            ),
            _case(
                f"PQ-MISSING-{index:02d}",
                f"Для объекта «{entity}» предусмотреть защиту от импульсных перенапряжений.",
                f"Для объекта «{entity}» выполнены расчёт заземления и система уравнивания потенциалов.",
                "INSUFFICIENT", entity=entity, property_code="SURGE_PROTECTION", category="MISSING_QUALIFIER",
            ),
        ])
    return cases


def _percent(numerator: int | float, denominator: int | float) -> float:
    return round(100.0 * float(numerator) / max(1.0, float(denominator)), 1)


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return int(ordered[index])


def _valid_contract(text: str) -> bool:
    return valid_structured_contract(text)


def _execute_batch(
    provider: Any,
    batch: list[dict[str, Any]],
    *,
    repeat: int,
    batch_number: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = {"task": "provider_qualification", "packets": [row["packet"] for row in batch]}
    started = time.perf_counter()
    try:
        result = provider.generate_validated(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            JUDGE_SYSTEM,
            _valid_contract,
            json_schema=JUDGE_JSON_SCHEMA,
        )
    except Exception as exc:
        result = None
        error = f"{type(exc).__name__}: {exc}"
    else:
        error = str(getattr(result, "error", "") or "")
    wall_ms = round((time.perf_counter() - started) * 1000)
    ok = bool(result and getattr(result, "ok", False))
    parsed = _extract_json(getattr(result, "text", "")) if ok else {}
    decisions = parsed.get("decisions") if isinstance(parsed, dict) else []
    schema_ok = bool(ok and _valid_contract(getattr(result, "text", "")))
    by_id = {
        str(row.get("packet_id") or ""): row
        for row in decisions or [] if isinstance(row, dict)
    }
    call = {
        "repeat": repeat,
        "batch": batch_number,
        "requested": len(batch),
        "ok": ok,
        "schema_ok": schema_ok,
        "provider": str(getattr(result, "provider", "") or getattr(provider, "name", "")),
        "model": str(getattr(result, "model", "") or getattr(provider, "model", "")),
        "status_code": getattr(result, "status_code", None) if result else None,
        "latency_ms": int(getattr(result, "latency_ms", 0) or wall_ms),
        "schema_mode": str(getattr(result, "schema_mode", "") or ""),
        "error": error[:500],
    }
    observations = []
    for case in batch:
        decision = dict(by_id.get(case["case_id"]) or {})
        actual = str(decision.get("verdict") or "NO_RESPONSE").upper()
        expected = str(case["expected_verdict"])
        observations.append({
            "repeat": repeat,
            "case_id": case["case_id"],
            "category": case["category"],
            "expected": expected,
            "actual": actual,
            "correct": actual == expected,
            "false_positive": expected != "SUPPORTS" and actual == "SUPPORTS",
            "response_received": bool(decision),
            "reason": str(decision.get("reason") or "")[:500],
        })
    return call, observations


def _finalize(
    provider: Any,
    cases: list[dict[str, Any]],
    repeats: int,
    batch_size: int,
    calls: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    *,
    completed: bool,
    transport_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    expected_calls = repeats * math.ceil(len(cases) / batch_size)
    expected_observations = len(cases) * repeats
    received = [row for row in observations if row.get("response_received")]
    latencies = [int(row["latency_ms"]) for row in calls if row["ok"]]
    by_case: dict[str, list[str]] = defaultdict(list)
    for row in received:
        by_case[row["case_id"]].append(row["actual"])
    repeatable = sum(
        len(values) == repeats and len(set(values)) == 1
        for values in by_case.values()
    )
    metrics = {
        "benchmark_completion_pct": _percent(len(calls), expected_calls),
        "request_success_pct": _percent(sum(row["ok"] for row in calls), expected_calls),
        "schema_adherence_pct": _percent(sum(row["schema_ok"] for row in calls), expected_calls),
        "response_coverage_pct": _percent(len(received), expected_observations),
        "semantic_accuracy_pct": _percent(sum(row["correct"] for row in received), len(received)),
        "false_positive_pct": _percent(sum(row["false_positive"] for row in received), len(received)),
        "repeatability_pct": _percent(repeatable, len(cases)),
        "latency_p50_ms": int(statistics.median(latencies)) if latencies else 0,
        "latency_p95_ms": _percentile(latencies, 0.95),
        "calls": len(calls),
        "expected_calls": expected_calls,
        "case_observations": len(observations),
        "response_observations": len(received),
        "rate_limit_events": sum(
            str(row.get("status_code")) == "429" for row in (transport_events or [])
        ),
    }
    gate_failures = []
    if not completed or len(calls) != expected_calls:
        gate_failures.append(
            f"benchmark_completion_pct: {metrics['benchmark_completion_pct']} (барьер 100.0)"
        )
    for metric, threshold in RELEASE_GATES.items():
        value = float(metrics[metric])
        passed = value <= threshold if metric == "false_positive_pct" else value >= threshold
        if not passed:
            gate_failures.append(f"{metric}: {value} (барьер {threshold})")
    actual = Counter((row["provider"], row["model"]) for row in calls if row["ok"])
    return {
        "version": BENCHMARK_VERSION,
        "configured_provider": str(getattr(provider, "name", "") or type(provider).__name__),
        "configured_model": str(getattr(provider, "model", "") or ""),
        "actual_routes": [
            {"provider": provider_name, "model": model, "calls": count}
            for (provider_name, model), count in actual.most_common()
        ],
        "cases": len(cases),
        "repeats": repeats,
        "metrics": metrics,
        "completed": bool(completed and len(calls) == expected_calls),
        "qualified": bool(completed and len(calls) == expected_calls and not gate_failures),
        "gate_failures": gate_failures,
        "release_gates": dict(RELEASE_GATES),
        "calls": list(calls),
        "transport_events": list(transport_events or []),
        "observations": list(observations),
        "policy": "Стенд использует только синтетические обезличенные пакеты и не передаёт проектные документы.",
    }


def _retry_after_seconds(error: str, *, default: int = 60) -> int:
    match = re.search(
        r"(?:try again in|retry[- ]after)\s*([0-9]+(?:\.[0-9]+)?)\s*(ms|s|sec|seconds)?",
        str(error or ""),
        flags=re.I,
    )
    if not match:
        return default
    delay = float(match.group(1))
    if str(match.group(2) or "").lower() == "ms":
        delay /= 1000
    return max(1, math.ceil(delay) + 2)


def start_provider_benchmark(
    provider: Any,
    *,
    repeats: int = 3,
    batch_size: int = 5,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    selected_cases = list(cases or benchmark_cases())
    repeats = max(1, int(repeats))
    batch_size = max(1, int(batch_size))
    total_calls = repeats * math.ceil(len(selected_cases) / batch_size)
    return {
        "version": BENCHMARK_VERSION,
        "configured_provider": str(getattr(provider, "name", "") or type(provider).__name__),
        "configured_model": str(getattr(provider, "model", "") or ""),
        "cases": len(selected_cases),
        "repeats": repeats,
        "batch_size": batch_size,
        "total_calls": total_calls,
        "next_call_index": 0,
        "calls": [],
        "observations": [],
        "transport_events": [],
        "cooldown_until": 0.0,
        "retry_after_seconds": 0,
        "blocked": False,
        "completed": False,
    }


def advance_provider_benchmark(
    provider: Any,
    state: dict[str, Any] | None = None,
    *,
    max_calls: int = 3,
    now: float | None = None,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run a bounded, resumable qualification slice.

    HTTP 429 and temporary provider failures do not become semantic answers and
    do not advance the logical batch cursor.  The caller persists the returned
    state and resumes it after the reported cooldown.
    """
    selected_cases = list(cases or benchmark_cases())
    state = dict(state or {})
    expected_provider = str(getattr(provider, "name", "") or type(provider).__name__)
    expected_model = str(getattr(provider, "model", "") or "")
    if (
        state.get("version") != BENCHMARK_VERSION
        or state.get("configured_provider") != expected_provider
        or state.get("configured_model") != expected_model
        or int(state.get("cases") or 0) != len(selected_cases)
    ):
        state = start_provider_benchmark(provider, cases=selected_cases)
    if state.get("completed") or state.get("blocked"):
        return state

    current_time = float(time.time() if now is None else now)
    cooldown_until = float(state.get("cooldown_until") or 0.0)
    if current_time < cooldown_until:
        state["retry_after_seconds"] = max(1, math.ceil(cooldown_until - current_time))
        return state
    state["cooldown_until"] = 0.0
    state["retry_after_seconds"] = 0

    repeats = int(state.get("repeats") or 3)
    batch_size = int(state.get("batch_size") or 5)
    batches_per_repeat = math.ceil(len(selected_cases) / batch_size)
    total_calls = repeats * batches_per_repeat
    logical_calls = list(state.get("calls") or [])
    observations = list(state.get("observations") or [])
    transport_events = list(state.get("transport_events") or [])
    processed = 0
    while int(state.get("next_call_index") or 0) < total_calls and processed < max(1, int(max_calls)):
        call_index = int(state.get("next_call_index") or 0)
        repeat = call_index // batches_per_repeat + 1
        batch_number = call_index % batches_per_repeat + 1
        offset = (batch_number - 1) * batch_size
        batch = selected_cases[offset:offset + batch_size]
        call, batch_observations = _execute_batch(
            provider, batch, repeat=repeat, batch_number=batch_number,
        )
        status_code = int(call.get("status_code") or 0)
        if status_code in {0, 408, 429, 500, 502, 503, 504}:
            transport_events.append(call)
            delay = _retry_after_seconds(
                str(call.get("error") or ""),
                default=60 if status_code == 429 else 15,
            )
            state["cooldown_until"] = current_time + delay
            state["retry_after_seconds"] = delay
            state["last_transport_error"] = str(call.get("error") or "")[:500]
            break
        logical_calls.append(call)
        observations.extend(batch_observations)
        state["next_call_index"] = call_index + 1
        processed += 1
        if status_code in {401, 402, 403}:
            state["blocked"] = True
            state["last_transport_error"] = str(call.get("error") or "")[:500]
            break

    state["calls"] = logical_calls
    state["observations"] = observations
    state["transport_events"] = transport_events
    state["total_calls"] = total_calls
    state["retry_after_seconds"] = int(state.get("retry_after_seconds") or 0)
    completed = int(state.get("next_call_index") or 0) >= total_calls
    state["completed"] = completed
    if completed:
        state["cooldown_until"] = 0.0
        state["retry_after_seconds"] = 0
    if not completed and not state.get("blocked") and processed >= max(1, int(max_calls)):
        # Three five-packet calls are the observed safe slice for Groq's free
        # 8K TPM tier.  A minute boundary keeps the next slice deterministic.
        if expected_provider.lower() == "groq":
            state["cooldown_until"] = current_time + 60
            state["retry_after_seconds"] = 60
    state["summary"] = _finalize(
        provider, selected_cases, repeats, batch_size,
        logical_calls, observations, completed=completed,
        transport_events=transport_events,
    )
    return state


def run_provider_benchmark(
    provider: Any,
    *,
    repeats: int = 3,
    batch_size: int = 5,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Synchronous benchmark retained for deterministic tests and CLI use."""
    selected_cases = list(cases or benchmark_cases())
    calls: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    for repeat in range(1, max(1, int(repeats)) + 1):
        for offset in range(0, len(selected_cases), max(1, int(batch_size))):
            call, batch_observations = _execute_batch(
                provider,
                selected_cases[offset:offset + max(1, int(batch_size))],
                repeat=repeat,
                batch_number=offset // max(1, int(batch_size)) + 1,
            )
            calls.append(call)
            observations.extend(batch_observations)
    return _finalize(
        provider, selected_cases, max(1, int(repeats)), max(1, int(batch_size)),
        calls, observations, completed=True,
    )


def comparison_rows(results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for label, result in results.items():
        metrics = dict(result.get("metrics") or {})
        rows.append({
            "Кандидат": label,
            "Модель": result.get("configured_model") or "—",
            "Квалифицирован": "Да" if result.get("qualified") else "Нет",
            "API, %": metrics.get("request_success_pct", 0),
            "JSON Schema, %": metrics.get("schema_adherence_pct", 0),
            "Смысловая точность, %": metrics.get("semantic_accuracy_pct", 0),
            "Ложные подтверждения, %": metrics.get("false_positive_pct", 0),
            "Повторяемость, %": metrics.get("repeatability_pct", 0),
            "p95, мс": metrics.get("latency_p95_ms", 0),
        })
    return sorted(
        rows,
        key=lambda row: (
            row["Квалифицирован"] == "Да",
            row["Смысловая точность, %"],
            row["API, %"],
            -row["Ложные подтверждения, %"],
            -row["p95, мс"],
        ),
        reverse=True,
    )


def qualified_ranking(results: dict[str, dict[str, Any]]) -> list[str]:
    """Return qualified candidates in the same deterministic order as the UI."""
    qualified = {
        label: result for label, result in results.items()
        if bool((result or {}).get("qualified"))
        and bool((result or {}).get("completed"))
        and (result or {}).get("version") == BENCHMARK_VERSION
    }
    ordered_rows = comparison_rows(qualified)
    return [str(row["Кандидат"]) for row in ordered_rows]
