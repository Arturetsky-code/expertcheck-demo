#!/usr/bin/env python3
"""Dependency-free release gate for ExpertCheck 15.1 Alpha 1."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_coverage_consensus_151a1 import (  # noqa: E402
    test_addressable_structured_trace_closes_only_l1_presence,
    test_failed_critic_preflight_falls_back_to_advisory_judge,
    test_normative_registry_distinguishes_verified_unverified_and_missing,
    test_reports_expose_grouped_review_queue,
    test_review_questions_are_grouped_without_losing_detail,
)
from tools.validate_end_to_end_150a2 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_review_questions_are_grouped_without_losing_detail,
    test_failed_critic_preflight_falls_back_to_advisory_judge,
    test_normative_registry_distinguishes_verified_unverified_and_missing,
    test_addressable_structured_trace_closes_only_l1_presence,
    test_reports_expose_grouped_review_queue,
]


def main() -> int:
    results = []
    for test in TESTS:
        try:
            test()
            results.append({"test": test.__name__, "status": "PASSED"})
        except Exception as exc:
            results.append({"test": test.__name__, "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"})
    payload = {
        "version": "15.1-alpha1-coverage-consensus",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "results": results,
    }
    (ROOT / "VALIDATION_151_ALPHA1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
