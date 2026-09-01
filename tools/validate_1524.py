#!/usr/bin/env python3
"""Release gate for ExpertCheck 15.2.4."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_ai_resilience_readiness_1524 import (  # noqa: E402
    test_addressable_drawing_title_closes_only_l1_presence_check,
    test_batch_contract_failure_splits_to_single_packets_without_losing_queue,
    test_failover_isolates_forbidden_provider_and_uses_next_lane,
    test_integrity_pass_does_not_claim_verification_is_complete,
    test_json_recovery_preserves_closed_rows_from_truncated_root_array,
    test_preflight_checks_working_json_contract_not_only_connectivity,
    test_structured_parameter_presence_closes_safe_checklist_l2_check,
)
from tools.validate_1523 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_json_recovery_preserves_closed_rows_from_truncated_root_array,
    test_failover_isolates_forbidden_provider_and_uses_next_lane,
    test_batch_contract_failure_splits_to_single_packets_without_losing_queue,
    test_preflight_checks_working_json_contract_not_only_connectivity,
    test_structured_parameter_presence_closes_safe_checklist_l2_check,
    test_addressable_drawing_title_closes_only_l1_presence_check,
    test_integrity_pass_does_not_claim_verification_is_complete,
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
        "version": "15.2.4-ai-resilience-verification-readiness",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "malformed_json_is_recovered_without_invention": True,
            "failed_batch_is_split_without_losing_successes": True,
            "provider_failures_are_isolated": True,
            "preflight_validates_real_contract": True,
            "integrity_and_verification_readiness_are_separate": True,
            "safe_presence_checkers_are_executable": True,
            "not_found_is_not_a_project_finding": True,
        },
        "results": results,
    }
    (ROOT / "VALIDATION_1524.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
