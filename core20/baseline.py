from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BaselineMetric:
    key: str
    expected: float
    policy: str = "AT_LEAST"
    description: str = ""


@dataclass(frozen=True)
class GoldenCase:
    case_id: str
    object_name: str
    parameter_code: str
    expected_kind: str
    expected_values: tuple[float, ...] = ()
    expected_position: str = ""
    notes: str = ""


BASELINE_18_7_3: dict[str, BaselineMetric] = {
    "objects_confirmed": BaselineMetric("objects_confirmed", 36, "EXACT", "Подтверждённый Trusted Object Registry"),
    "passport_characteristics": BaselineMetric("passport_characteristics", 137, "AT_LEAST", "Характеристики подтверждённых паспортов"),
    "cross_section_comparisons": BaselineMetric("cross_section_comparisons", 99, "EXACT", "Сформированные межраздельные сопоставления"),
    "cross_section_l5": BaselineMetric("cross_section_l5", 45, "AT_LEAST", "Строго завершённые межраздельные проверки"),
    "project_findings": BaselineMetric("project_findings", 1, "EXACT", "Доказанные проблемы проекта на Test 77"),
    "specialist_questions": BaselineMetric("specialist_questions", 346, "AT_MOST", "Адресные вопросы специалисту"),
    "review_packages": BaselineMetric("review_packages", 26, "AT_MOST", "Рабочие пакеты после compression"),
    "verified_checks": BaselineMetric("verified_checks", 49, "AT_LEAST", "Проверки с доказательством"),
    "system_limitations": BaselineMetric("system_limitations", 319, "AT_MOST", "Ограничения автоматического покрытия"),
}


GOLDEN_CASES_18_7_3: tuple[GoldenCase, ...] = (
    GoldenCase(
        "GOLD-COMPRESSOR-AREA-CONFLICT", "Компрессорная", "AREA_BUILD", "PROJECT_FINDING",
        (54.3, 48.7), "4.5",
        "Факт конфликта должен быть доказан; правильное значение без owner-раздела не утверждается.",
    ),
    GoldenCase(
        "GOLD-DEDUSTING-AREA", "Модуль обеспыливания", "AREA_BUILD", "VERIFIED_OK",
        (23.5,), "4.12",
        "23,5 м² не должно мигрировать к зданию проборазделки.",
    ),
    GoldenCase(
        "GOLD-SAMPLE-PREP-AREA", "Здание проборазделки", "AREA_BUILD", "VERIFIED_OK",
        (89.9,), "4.13",
        "89,9 м² остаётся физически и семантически привязано к строке здания проборазделки.",
    ),
)


def evaluate_baseline(observed: dict[str, Any]) -> dict[str, Any]:
    checks=[]
    for key, metric in BASELINE_18_7_3.items():
        raw=observed.get(key)
        try:
            value=float(raw)
        except (TypeError, ValueError):
            checks.append({
                "key":key,"passed":False,"expected":metric.expected,"observed":raw,
                "policy":metric.policy,"description":metric.description,"reason":"MISSING_OR_NON_NUMERIC",
            })
            continue
        if metric.policy=='EXACT':
            passed=value==metric.expected
        elif metric.policy=='AT_MOST':
            passed=value<=metric.expected
        else:
            passed=value>=metric.expected
        checks.append({
            "key":key,"passed":passed,"expected":metric.expected,"observed":value,
            "policy":metric.policy,"description":metric.description,
        })
    return {
        "baseline":"18.7.3-Test77",
        "passed":all(item["passed"] for item in checks),
        "failed":[item["key"] for item in checks if not item["passed"]],
        "checks":checks,
    }
