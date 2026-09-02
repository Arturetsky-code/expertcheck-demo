#!/usr/bin/env python3
"""Stage 1 gate for ExpertCheck 18.0 Verified Platform."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_171_proof import TESTS as PROOF_TESTS  # noqa: E402
from tests.test_project_data_contract_180 import (  # noqa: E402
    test_contract_fingerprint_is_repeatable,
    test_contract_rejects_non_mapping_result_rows,
    test_contract_repairs_mixed_public_result_values,
    test_individual_report_failure_is_isolated,
    test_snapshot_roundtrip_enforces_contract_without_source_pdf,
    test_technical_report_exposes_data_contract_audit,
    test_ten_repeated_xlsx_and_snapshot_exports_are_stable,
    test_ui_frames_migrates_legacy_result_once_and_persists_contract,
)


TESTS = list(PROOF_TESTS) + [
    test_contract_repairs_mixed_public_result_values,
    test_contract_fingerprint_is_repeatable,
    test_contract_rejects_non_mapping_result_rows,
    test_ui_frames_migrates_legacy_result_once_and_persists_contract,
    test_snapshot_roundtrip_enforces_contract_without_source_pdf,
    test_technical_report_exposes_data_contract_audit,
    test_individual_report_failure_is_isolated,
    test_ten_repeated_xlsx_and_snapshot_exports_are_stable,
]


def main() -> int:
    results = []
    for index, test in enumerate(TESTS, 1):
        try:
            test()
            results.append({"test": f"STAGE1-{index:03d}", "status": "PASSED"})
        except Exception as exc:
            results.append({
                "test": f"STAGE1-{index:03d}",
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            })
    payload = {
        "version": "18.0-stage1-project-data-contract",
        "stage": "Стабильное ядро и единый контракт данных",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "verified_core_inherited": True,
            "public_result_contract_required": True,
            "legacy_result_migration_required": True,
            "snapshot_contract_required": True,
            "report_contract_required": True,
            "isolated_report_failures_required": True,
            "stable_result_fingerprint_required": True,
            "stability_runs": 10,
            "xlsx_report_kinds_per_run": 3,
        },
        "results": results,
    }
    output = ROOT / "VALIDATION_180_STAGE1.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
