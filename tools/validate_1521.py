#!/usr/bin/env python3
"""Dependency-free release gate for ExpertCheck 15.2.1."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_coverage_acceleration_1521 import (  # noqa: E402
    test_capacity_level_question_keeps_observed_value_and_source,
    test_categorical_numeric_result_has_satisfied_contract_and_report_gate_state,
    test_extended_budget_covers_project_sized_l4_queue_and_order_is_diversified,
    test_failover_treats_invalid_json_as_provider_failure,
    test_non_admitted_duplicates_are_explicitly_excluded_from_comparison,
    test_pump_height_25_is_preserved_and_routed_as_decimal_review_question,
    test_semantic_batch_uses_validated_failover_response,
)
from tests.test_release_version_152a1 import (  # noqa: E402
    test_ui_and_core_identify_release_1521,
)
from tools.validate_152a1 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_failover_treats_invalid_json_as_provider_failure,
    test_semantic_batch_uses_validated_failover_response,
    test_capacity_level_question_keeps_observed_value_and_source,
    test_categorical_numeric_result_has_satisfied_contract_and_report_gate_state,
    test_non_admitted_duplicates_are_explicitly_excluded_from_comparison,
    test_pump_height_25_is_preserved_and_routed_as_decimal_review_question,
    test_extended_budget_covers_project_sized_l4_queue_and_order_is_diversified,
    test_ui_and_core_identify_release_1521,
]


def main() -> int:
    results = []
    for test in TESTS:
        try:
            test()
            results.append({"test": test.__name__, "status": "PASSED"})
        except Exception as exc:
            results.append({
                "test": test.__name__,
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            })
    payload = {
        "version": "15.2.1-coverage-acceleration-reliability",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "invalid_json_triggers_failover": True,
            "l5_requires_independent_consensus": True,
            "non_admitted_facts_are_excluded": True,
            "decimal_anomaly_is_never_autocorrected": True,
        },
        "results": results,
    }
    (ROOT / "VALIDATION_1521.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
