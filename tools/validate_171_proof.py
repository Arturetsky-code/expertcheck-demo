#!/usr/bin/env python3
"""Critical release gate for ExpertCheck 17.1 Proof."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_170 import TESTS as VERIFIED_CORE_TESTS  # noqa: E402
from tests.test_cross_section_proof_th import (  # noqa: E402
    test_cross_section_is_first_class_review_domain_and_th_metric,
    test_different_physical_units_never_form_false_comparison,
    test_missing_page_blocks_categorical_cross_section_result,
    test_report_counts_cross_section_finding_once_and_exports_proof_route,
    test_th_owner_and_control_mismatch_is_addressable_project_finding,
    test_th_owner_and_pz_control_create_verified_l5_without_ai,
    test_two_control_sections_cannot_replace_missing_th_owner,
)


TESTS = list(VERIFIED_CORE_TESTS) + [
    test_th_owner_and_pz_control_create_verified_l5_without_ai,
    test_th_owner_and_control_mismatch_is_addressable_project_finding,
    test_two_control_sections_cannot_replace_missing_th_owner,
    test_different_physical_units_never_form_false_comparison,
    test_missing_page_blocks_categorical_cross_section_result,
    test_cross_section_is_first_class_review_domain_and_th_metric,
    test_report_counts_cross_section_finding_once_and_exports_proof_route,
]


def main() -> int:
    results = []
    for index, test in enumerate(TESTS, 1):
        try:
            test()
            results.append({"test": f"PROOF-{index:03d}", "status": "PASSED"})
        except Exception as exc:
            results.append({
                "test": f"PROOF-{index:03d}",
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            })
    payload = {
        "version": "17.1-proof-th-cross-section",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "verified_core_inherited": True,
            "same_object_property_scope_unit_required": True,
            "owner_to_control_route_required": True,
            "two_addressable_independent_sources_required": True,
            "ai_not_required_for_cross_section_verdict": True,
            "report_double_count_forbidden": True,
        },
        "results": results,
    }
    output = ROOT / "VALIDATION_171_PROOF.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
