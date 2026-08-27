#!/usr/bin/env python3
"""Dependency-free gate for the 15.0 Alpha 2 corrective release."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_semantic_agents_150a1 import TESTS as ALPHA1_TESTS  # noqa: E402
from tests.test_end_to_end_verification_150a2 import (  # noqa: E402
    test_adaptive_search_pattern_does_not_demote_numeric_recipe,
    test_critic_provider_is_called_once_for_one_judge_decision,
    test_equipment_atoms_keep_precise_equipment_owner,
    test_external_packet_is_limited_to_four_short_evidence_fragments,
    test_failed_preflight_blocks_bulk_evidence_calls,
    test_l4_always_has_visible_addressable_evidence,
    test_new_service_codes_are_localized,
    test_nonnumeric_row_heading_does_not_inherit_numeric_kind,
    test_numeric_checker_accepts_canonical_property_alias,
    test_report_keeps_weak_mismatch_as_a_specialist_question,
    test_report_uses_the_admitted_finding_class_instead_of_raw_status,
    test_stale_parent_measurement_is_not_inherited_by_line_count_atom,
    test_units_bind_to_their_own_numeric_occurrence,
)


TESTS = [
    *ALPHA1_TESTS,
    test_units_bind_to_their_own_numeric_occurrence,
    test_stale_parent_measurement_is_not_inherited_by_line_count_atom,
    test_nonnumeric_row_heading_does_not_inherit_numeric_kind,
    test_equipment_atoms_keep_precise_equipment_owner,
    test_adaptive_search_pattern_does_not_demote_numeric_recipe,
    test_numeric_checker_accepts_canonical_property_alias,
    test_l4_always_has_visible_addressable_evidence,
    test_critic_provider_is_called_once_for_one_judge_decision,
    test_failed_preflight_blocks_bulk_evidence_calls,
    test_external_packet_is_limited_to_four_short_evidence_fragments,
    test_report_uses_the_admitted_finding_class_instead_of_raw_status,
    test_report_keeps_weak_mismatch_as_a_specialist_question,
    test_new_service_codes_are_localized,
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
        "version": "15.0-alpha2-end-to-end-verification",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "results": results,
    }
    (ROOT / "VALIDATION_150_ALPHA2_UNIT.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
