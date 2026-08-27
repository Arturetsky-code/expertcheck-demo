#!/usr/bin/env python3
"""Re-check the saved 15.0 end-to-end result without repeating PDF extraction."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "VALIDATION_150_ALPHA1.json"
TARGET = ROOT / "VALIDATION_150_ALPHA1_GATE.json"


def main() -> int:
    summary = json.loads(SOURCE.read_text(encoding="utf-8"))
    sheets = summary.get("report_sheets") or {}
    confirmations = summary.get("report_confirmation") or {}
    checks = {
        "12 документов обработано": len((summary.get("input") or {}).get("files") or []) == 12,
        "ошибок конвейера нет": not ((summary.get("output") or {}).get("pipeline_errors") or []),
        "небезопасных автозакрытий нет": not ((summary.get("checklist") or {}).get("unsafe_automatic_closures") or []),
        "95 исполняемых пунктов ТХ": (summary.get("checklist") or {}).get("technology_rows") == 95,
        "все L4 имеют выполненный контракт": not (summary.get("l4_contract_violations") or []),
        "контроль качества отчёта пройден": (summary.get("quality_gate") or {}).get("status") == "PASSED",
        "служебные статусы русифицированы": not (summary.get("report_localization_leaks") or []),
        "комплектность отражена в отчётах": bool(confirmations) and all(value == "Подтверждена" for value in confirmations.values()),
        "AI-аудит есть в отчёте ГИПа": any("Отчёт_ГИПа" in name and "AI — сводка" in names for name, names in sheets.items()),
        "AI-аудит есть в техническом приложении": any("Техническое_приложение" in name and "AI — сводка" in names for name, names in sheets.items()),
        "контрольное расхождение компрессорной обнаружено": bool((summary.get("known_regression_cases") or {}).get("compressor_area_mismatch_detected")),
        "ошибка высоты 25 м удержана": bool((summary.get("known_regression_cases") or {}).get("pump_height_25_quarantined")),
    }
    payload = {
        "version": summary.get("version"),
        "status": "PASSED" if all(checks.values()) else "FAILED",
        "checks": checks,
        "metrics": {
            "checks": (summary.get("coverage_matrix") or {}).get("total"),
            "evidence_ready": (summary.get("coverage_matrix") or {}).get("evidence_ready"),
            "l4": ((summary.get("coverage_matrix") or {}).get("evidence_levels") or {}).get("L4"),
            "l5": ((summary.get("coverage_matrix") or {}).get("evidence_levels") or {}).get("L5"),
            "technology_rows": (summary.get("checklist") or {}).get("technology_rows"),
        },
    }
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
