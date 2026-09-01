from __future__ import annotations

import json
import math
import statistics
import time
from collections import Counter, defaultdict
from typing import Any

from .semantic_evidence_engine import JUDGE_JSON_SCHEMA, JUDGE_SYSTEM, JUDGE_VERDICTS, _extract_json


BENCHMARK_VERSION = "17.0-provider-qualification-v1"
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


def run_provider_benchmark(
    provider: Any,
    *,
    repeats: int = 3,
    batch_size: int = 5,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cases = list(cases or benchmark_cases())
    repeats = max(1, int(repeats))
    batch_size = max(1, int(batch_size))
    observations: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []

    def valid_contract(text: str) -> bool:
        parsed = _extract_json(text)
        decisions = parsed.get("decisions") if isinstance(parsed, dict) else None
        return bool(decisions is not None and isinstance(decisions, list) and all(
            isinstance(row, dict)
            and str(row.get("packet_id") or "")
            and str(row.get("verdict") or "").upper() in JUDGE_VERDICTS
            for row in decisions
        ))

    for repeat in range(1, repeats + 1):
        for offset in range(0, len(cases), batch_size):
            batch = cases[offset:offset + batch_size]
            payload = {"task": "provider_qualification", "packets": [row["packet"] for row in batch]}
            started = time.perf_counter()
            try:
                result = provider.generate_validated(
                    json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                    JUDGE_SYSTEM,
                    valid_contract,
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
            schema_ok = bool(ok and valid_contract(getattr(result, "text", "")))
            by_id = {
                str(row.get("packet_id") or ""): row
                for row in decisions or [] if isinstance(row, dict)
            }
            calls.append({
                "repeat": repeat,
                "batch": offset // batch_size + 1,
                "requested": len(batch),
                "ok": ok,
                "schema_ok": schema_ok,
                "provider": str(getattr(result, "provider", "") or getattr(provider, "name", "")),
                "model": str(getattr(result, "model", "") or getattr(provider, "model", "")),
                "status_code": getattr(result, "status_code", None) if result else None,
                "latency_ms": int(getattr(result, "latency_ms", 0) or wall_ms),
                "schema_mode": str(getattr(result, "schema_mode", "") or ""),
                "error": error[:500],
            })
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

    latencies = [int(row["latency_ms"]) for row in calls if row["ok"]]
    by_case: dict[str, list[str]] = defaultdict(list)
    for row in observations:
        by_case[row["case_id"]].append(row["actual"])
    repeatable = sum(len(set(values)) == 1 for values in by_case.values())
    metrics = {
        "request_success_pct": _percent(sum(row["ok"] for row in calls), len(calls)),
        "schema_adherence_pct": _percent(sum(row["schema_ok"] for row in calls), len(calls)),
        "semantic_accuracy_pct": _percent(sum(row["correct"] for row in observations), len(observations)),
        "false_positive_pct": _percent(sum(row["false_positive"] for row in observations), len(observations)),
        "repeatability_pct": _percent(repeatable, len(by_case)),
        "latency_p50_ms": int(statistics.median(latencies)) if latencies else 0,
        "latency_p95_ms": _percentile(latencies, 0.95),
        "calls": len(calls),
        "case_observations": len(observations),
    }
    gate_failures = []
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
        "qualified": not gate_failures,
        "gate_failures": gate_failures,
        "release_gates": dict(RELEASE_GATES),
        "calls": calls,
        "observations": observations,
        "policy": "Стенд использует только синтетические обезличенные пакеты и не передаёт проектные документы.",
    }


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
    }
    ordered_rows = comparison_rows(qualified)
    return [str(row["Кандидат"]) for row in ordered_rows]
