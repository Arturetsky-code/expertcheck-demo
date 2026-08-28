#!/usr/bin/env python3
"""Dependency-free release gate for ExpertCheck 15.1 Alpha 1.1."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_coverage_consensus_151a1 import (  # noqa: E402
    test_advisory_lane_is_bounded_and_reports_progress,
    test_assignment_extractor_reuses_existing_page_corpus,
    test_transport_failure_opens_semantic_circuit_breaker,
)
from tools.validate_151a1 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_advisory_lane_is_bounded_and_reports_progress,
    test_transport_failure_opens_semantic_circuit_breaker,
    test_assignment_extractor_reuses_existing_page_corpus,
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
        "version": "15.1-alpha1.1-assignment-resilience",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "results": results,
    }
    (ROOT / "VALIDATION_151_ALPHA1_1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
