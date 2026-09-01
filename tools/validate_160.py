#!/usr/bin/env python3
"""Dependency-free critical release gate for ExpertCheck 16.0."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_quality_leap_160 import (  # noqa: E402
    test_failover_repairs_contract_only_after_independent_lanes_fail,
    test_unrelated_safety_barrier_confirmation_is_not_promoted_to_l5,
    test_gold_standard_contains_all_critical_regressions,
    test_judge_must_affirm_entity_and_property_not_merely_omit_them,
    test_semantic_slots_accept_exact_drawing_artifact_title,
    test_semantic_slots_block_machine_guard_as_traffic_geometry_proof,
    test_specialist_queue_is_topical_and_bounded,
    test_structured_response_recovery_accepts_wrappers_arrays_and_single_rows,
)
from tools.validate_1525 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_gold_standard_contains_all_critical_regressions,
    test_semantic_slots_block_machine_guard_as_traffic_geometry_proof,
    test_semantic_slots_accept_exact_drawing_artifact_title,
    test_unrelated_safety_barrier_confirmation_is_not_promoted_to_l5,
    test_structured_response_recovery_accepts_wrappers_arrays_and_single_rows,
    test_failover_repairs_contract_only_after_independent_lanes_fail,
    test_judge_must_affirm_entity_and_property_not_merely_omit_them,
    test_specialist_queue_is_topical_and_bounded,
]


def main() -> int:
    results = []
    for index, test in enumerate(TESTS, 1):
        try:
            test()
            results.append({"test": f"QC-{index:03d}", "status": "PASSED"})
        except Exception as exc:
            results.append({
                "test": f"QC-{index:03d}", "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            })

    gold = json.loads((ROOT / "knowledge" / "quality_gold_standard_v1.json").read_text(encoding="utf-8"))
    payload = {
        "version": "16.0-quality-leap",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "release_gates": gold["release_gates"],
        "quality_policy": {
            "critical_regressions_fail_release": True,
            "semantic_slot_contract_is_fail_closed": True,
            "judge_entity_and_property_are_mandatory": True,
            "malformed_json_has_bounded_repair": True,
            "ai_queue_is_resumable_and_reported_truthfully": True,
            "candidate_coverage_is_separate_from_l5": True,
        },
        "results": results,
    }
    (ROOT / "VALIDATION_160.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
