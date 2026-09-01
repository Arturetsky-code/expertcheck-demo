#!/usr/bin/env python3
"""Release gate for ExpertCheck 15.2.5."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_checklist_runtime_stability_1525 import (  # noqa: E402
    test_checklist_parent_does_not_duplicate_full_atomic_conditions,
    test_deferred_checklist_queue_keeps_report_incomplete,
    test_initial_checklist_ai_is_deferred_but_full_target_is_preserved,
    test_persisted_deep_review_does_not_duplicate_page_corpus,
    test_resumable_batch_selects_next_packets_after_checkpoint,
)
from tools.validate_1524 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_initial_checklist_ai_is_deferred_but_full_target_is_preserved,
    test_resumable_batch_selects_next_packets_after_checkpoint,
    test_checklist_parent_does_not_duplicate_full_atomic_conditions,
    test_persisted_deep_review_does_not_duplicate_page_corpus,
    test_deferred_checklist_queue_keeps_report_incomplete,
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
        "version": "15.2.5-checklist-stability-resumable-queue",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "initial_checklist_run_finishes_before_external_ai_queue": True,
            "continuation_advances_to_new_checkpoint_packets": True,
            "full_coverage_target_is_preserved": True,
            "atomic_conditions_are_stored_once": True,
            "page_corpus_is_not_duplicated_in_deep_review": True,
            "recoverable_ui_errors_preserve_current_session": True,
        },
        "results": results,
    }
    (ROOT / "VALIDATION_1525.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
