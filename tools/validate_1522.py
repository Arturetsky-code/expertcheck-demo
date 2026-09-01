#!/usr/bin/env python3
"""Dependency-free release gate for ExpertCheck 15.2.2."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_reliability_snapshot_1522 import (  # noqa: E402
    test_corpus_fingerprint_changes_for_same_length_content,
    test_invalid_semantic_decision_is_not_persisted_in_checkpoint,
    test_project_snapshot_rechecks_quality_gate_without_source_pdf,
    test_project_snapshot_roundtrip_contains_rerunnable_page_corpus,
    test_quality_gate_accepts_addressable_values_rendered_in_sources,
    test_report_headline_reconciles_to_exported_specialist_queue,
    test_semantic_checkpoint_reuses_completed_packet_without_provider_call,
    test_xlsx_question_total_and_quality_gate_sheet_are_auditable,
)
from tests.test_workspace_resource_hotfix_1111 import (  # noqa: E402
    test_snapshot_signature_changes_when_semantic_checkpoint_advances,
)
from tools.validate_1521 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_semantic_checkpoint_reuses_completed_packet_without_provider_call,
    test_invalid_semantic_decision_is_not_persisted_in_checkpoint,
    test_snapshot_signature_changes_when_semantic_checkpoint_advances,
    test_report_headline_reconciles_to_exported_specialist_queue,
    test_xlsx_question_total_and_quality_gate_sheet_are_auditable,
    test_quality_gate_accepts_addressable_values_rendered_in_sources,
    test_project_snapshot_roundtrip_contains_rerunnable_page_corpus,
    test_project_snapshot_rechecks_quality_gate_without_source_pdf,
    test_corpus_fingerprint_changes_for_same_length_content,
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
        "version": "15.2.2-resumable-verification-snapshot",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "semantic_queue_is_resumable": True,
            "checkpoint_is_bound_to_exact_corpus": True,
            "report_totals_are_reconciled": True,
            "quality_gate_reasons_are_exported": True,
            "snapshot_is_recheckable_without_pdf": True,
        },
        "results": results,
    }
    (ROOT / "VALIDATION_1522.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
