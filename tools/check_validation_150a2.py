#!/usr/bin/env python3
"""Re-check the saved Alpha 2 end-to-end and regression results."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "VALIDATION_150_ALPHA2.json"
UNIT_SOURCE = ROOT / "VALIDATION_150_ALPHA2_UNIT.json"
TARGET = ROOT / "VALIDATION_150_ALPHA2_GATE.json"


def main() -> int:
    summary = json.loads(SOURCE.read_text(encoding="utf-8"))
    unit = json.loads(UNIT_SOURCE.read_text(encoding="utf-8"))
    sheets = summary.get("report_sheets") or {}
    confirmations = summary.get("report_confirmation") or {}
    question_rows = summary.get("report_question_rows") or {}
    coverage = summary.get("coverage_matrix") or {}
    archetypes = {row.get("archetype"): row for row in coverage.get("matrix") or []}
    numeric = archetypes.get("NUMERIC_VALUE") or {}
    required_atomic_headers = {
        "Оператор условия", "Нормализованное требуемое значение", "Значение проекта",
        "Единица сравнения", "Условие выполнено", "Семейство проверяющего механизма",
        "Режим проверяющего механизма",
    }
    atomic_headers = summary.get("report_atomic_headers") or {}
    detailed_atomic_headers = [
        set(headers) for name, headers in atomic_headers.items()
        if "Резюме_руководителя" not in name
    ]
    checks = {
        "12 документов обработано": len((summary.get("input") or {}).get("files") or []) == 12,
        "ошибок конвейера нет": not ((summary.get("output") or {}).get("pipeline_errors") or []),
        "29 регрессионных сценариев пройдено": unit.get("tests") == 29 and unit.get("failed") == 0,
        "615 предметных проверок": coverage.get("total") == 615,
        "95 пунктов ТХ": (summary.get("checklist") or {}).get("technology_rows") == 95,
        "небезопасных автозакрытий нет": not ((summary.get("checklist") or {}).get("unsafe_automatic_closures") or []),
        "все L4 имеют показываемое доказательство": not (summary.get("l4_contract_violations") or []),
        "138 строгих пакетов L4": (coverage.get("evidence_levels") or {}).get("L4") == 138,
        "числовой контур не содержит ложный заголовок": numeric.get("total") == 4,
        "все числовые условия имеют адресный материал": numeric.get("evidence_ready") == numeric.get("total") == 4,
        "контроль качества отчёта пройден": (summary.get("quality_gate") or {}).get("status") == "PASSED",
        "служебные статусы русифицированы": not (summary.get("report_localization_leaks") or []),
        "числовые поля есть в подробных отчётах": bool(detailed_atomic_headers) and all(
            required_atomic_headers.issubset(headers) for headers in detailed_atomic_headers
        ),
        "комплектность отражена в отчётах": bool(confirmations) and all(
            value == "Подтверждена" for value in confirmations.values()
        ),
        "подтверждённые расхождения отделены от вопросов": bool(sheets) and all(
            "Подтверждённые расхождения" in names and "Вопросы специалисту" in names
            for names in sheets.values()
        ),
        "в подробных отчётах сохранены все вопросы": sum(
            value == 367 for name, value in question_rows.items() if "Резюме_руководителя" not in name
        ) == 2,
        "контрольное расхождение компрессорной обнаружено": bool(
            (summary.get("known_regression_cases") or {}).get("compressor_area_mismatch_detected")
        ),
        "ошибка высоты 25 м удержана": bool(
            (summary.get("known_regression_cases") or {}).get("pump_height_25_quarantined")
        ),
    }
    payload = {
        "version": summary.get("version"),
        "status": "PASSED" if all(checks.values()) else "FAILED",
        "checks": checks,
        "metrics": {
            "checks": coverage.get("total"),
            "evidence_ready": coverage.get("evidence_ready"),
            "evidence_coverage_pct": coverage.get("evidence_coverage_pct"),
            "l4": (coverage.get("evidence_levels") or {}).get("L4"),
            "l5": (coverage.get("evidence_levels") or {}).get("L5"),
            "numeric_constraints": numeric.get("total"),
            "technology_rows": (summary.get("checklist") or {}).get("technology_rows"),
            "unit_scenarios": unit.get("tests"),
        },
    }
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
