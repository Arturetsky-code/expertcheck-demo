#!/usr/bin/env python3
"""Critical release gate for ExpertCheck 17.0 Verified Core."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_verified_core_170 import (  # noqa: E402
    test_false_barrier_l5_cannot_reappear_in_exported_gip_xlsx,
    test_final_gate_blocks_real_false_barrier_l5_even_if_previous_layers_passed,
    test_final_gate_preserves_addressable_deterministic_numeric_verdict,
    test_groq_uses_strict_json_schema_without_unstructured_retry,
    test_openrouter_free_is_rejected_from_verified_core,
    test_provider_benchmark_has_thirty_anonymous_cases_and_strict_gates,
    test_provider_ranking_excludes_unqualified_candidate_and_selects_stable_winner,
)
from tools.validate_160 import TESTS as BASE_TESTS  # noqa: E402


TESTS = list(BASE_TESTS) + [
    test_provider_benchmark_has_thirty_anonymous_cases_and_strict_gates,
    test_provider_ranking_excludes_unqualified_candidate_and_selects_stable_winner,
    test_openrouter_free_is_rejected_from_verified_core,
    test_groq_uses_strict_json_schema_without_unstructured_retry,
    test_final_gate_blocks_real_false_barrier_l5_even_if_previous_layers_passed,
    test_final_gate_preserves_addressable_deterministic_numeric_verdict,
    test_false_barrier_l5_cannot_reappear_in_exported_gip_xlsx,
]


def main() -> int:
    results = []
    for index, test in enumerate(TESTS, 1):
        try:
            test()
            results.append({"test": f"VC-{index:03d}", "status": "PASSED"})
        except Exception as exc:
            results.append({
                "test": f"VC-{index:03d}",
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            })

    payload = {
        "version": "17.0-verified-core",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "strict_provider_schema": True,
            "random_free_router_forbidden": True,
            "provider_benchmark_required": True,
            "independent_judge_critic_required_for_semantic_l5": True,
            "final_verdict_gate_is_fail_closed": True,
            "exported_reports_cannot_bypass_final_gate": True,
            "verified_vertical_core_is_bounded": True,
        },
        "results": results,
    }
    (ROOT / "VALIDATION_170.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
