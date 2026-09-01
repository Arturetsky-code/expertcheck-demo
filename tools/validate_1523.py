#!/usr/bin/env python3
"""Dependency-free release gate for ExpertCheck 15.2.3."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_reliability_hotfix_1523 import (  # noqa: E402
    test_failed_quality_gate_forces_preliminary_xlsx_status_and_stable_question_id,
    test_parent_aggregation_keeps_failed_l5_gate_visible_to_quality_gate,
    test_parent_aggregation_preserves_l5_gate_and_addressable_evidence,
    test_report_ids_are_stable_and_never_export_nan,
    test_semantic_continuation_rechecks_snapshot_without_source_pdf,
)
from tools.validate_1522 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_parent_aggregation_preserves_l5_gate_and_addressable_evidence,
    test_parent_aggregation_keeps_failed_l5_gate_visible_to_quality_gate,
    test_report_ids_are_stable_and_never_export_nan,
    test_failed_quality_gate_forces_preliminary_xlsx_status_and_stable_question_id,
    test_semantic_continuation_rechecks_snapshot_without_source_pdf,
]


def main() -> int:
    results = []
    for test in TESTS:
        try:
            test()
            results.append({"test": test.__name__, "status": "PASSED"})
        except Exception as exc:
            results.append({
                "test": test.__name__, "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            })
    payload = {
        "version": "15.2.3-reliability-hotfix-ai-continuation",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "l5_gate_metadata_survives_parent_aggregation": True,
            "failed_quality_gate_forces_preliminary_report": True,
            "report_ids_are_stable": True,
            "ai_queue_continues_without_source_pdf": True,
            "judge_and_critic_counters_are_separate": True,
        },
        "results": results,
    }
    (ROOT / "VALIDATION_1523.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
