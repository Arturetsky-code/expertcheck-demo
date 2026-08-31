#!/usr/bin/env python3
"""Dependency-free release gate for ExpertCheck 15.2 Alpha 1."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_quality_gate_103a2 import (  # noqa: E402
    test_pzu_tep_row_has_physical_trace_and_is_admitted,
    test_two_trusted_tep_rows_reveal_area_discrepancy,
)
from tests.test_verification_kernel_104a1 import (  # noqa: E402
    test_assignment_capacity_checker_does_not_compare_total_with_operating_throughput,
)
from tests.test_verification_quality_rebuild_152a1 import (  # noqa: E402
    test_administrative_customer_word_is_not_an_engineering_qualifier,
    test_annual_capacity_unit_is_atomic_and_project_scoped,
    test_capacity_semantics_distinguish_total_from_operating_throughput,
    test_equipment_cannot_own_building_footprint_even_when_row_locked,
    test_operating_throughput_cannot_be_a_total_capacity_finding,
    test_project_annual_capacity_can_close_on_exact_addressable_fact,
    test_pz_capacity_unit_recovers_year_split_after_slash,
    test_scope_annotation_preserves_prior_plausibility_exclusion,
    test_shift_duration_atom_inherits_typed_parent_parameter_and_route,
    test_shift_duration_closes_on_exact_directed_project_clause,
    test_standalone_known_section_title_is_not_an_actionable_check,
)
from tools.validate_151a11 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_shift_duration_atom_inherits_typed_parent_parameter_and_route,
    test_shift_duration_closes_on_exact_directed_project_clause,
    test_annual_capacity_unit_is_atomic_and_project_scoped,
    test_administrative_customer_word_is_not_an_engineering_qualifier,
    test_capacity_semantics_distinguish_total_from_operating_throughput,
    test_operating_throughput_cannot_be_a_total_capacity_finding,
    test_assignment_capacity_checker_does_not_compare_total_with_operating_throughput,
    test_project_annual_capacity_can_close_on_exact_addressable_fact,
    test_equipment_cannot_own_building_footprint_even_when_row_locked,
    test_scope_annotation_preserves_prior_plausibility_exclusion,
    test_pz_capacity_unit_recovers_year_split_after_slash,
    test_standalone_known_section_title_is_not_an_actionable_check,
    test_pzu_tep_row_has_physical_trace_and_is_admitted,
    test_two_trusted_tep_rows_reveal_area_discrepancy,
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
        "version": "15.2-alpha1-verification-quality-rebuild",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "not_found_is_violation": False,
            "capacity_semantic_level_required": True,
            "equipment_building_footprint_blocked": True,
        },
        "results": results,
    }
    (ROOT / "VALIDATION_152_ALPHA1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
