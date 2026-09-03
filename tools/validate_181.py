#!/usr/bin/env python3
"""Critical gate for ExpertCheck 18.1 Resilient Free AI."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_180_stage1 import TESTS as PLATFORM_TESTS  # noqa: E402
from tests.test_resilient_free_ai_181 import (  # noqa: E402
    test_free_groq_gemini_failover_route_is_available,
    test_gemini_uses_native_json_schema_and_auth_header,
    test_expired_benchmark_cooldown_is_cleared_before_resume,
    test_groq_benchmark_slice_stops_before_free_tpm_burst,
    test_local_contract_rejects_incomplete_schema_even_after_http_success,
    test_rate_limit_diagnostic_reports_safe_retry,
    test_rate_limit_is_checkpointed_without_poisoning_semantic_metrics,
    test_semantic_roles_require_current_completed_qualification_for_l5,
    test_unqualified_production_provider_cannot_promote_semantic_l5,
)


TESTS = list(PLATFORM_TESTS) + [
    test_gemini_uses_native_json_schema_and_auth_header,
    test_free_groq_gemini_failover_route_is_available,
    test_expired_benchmark_cooldown_is_cleared_before_resume,
    test_rate_limit_is_checkpointed_without_poisoning_semantic_metrics,
    test_groq_benchmark_slice_stops_before_free_tpm_burst,
    test_local_contract_rejects_incomplete_schema_even_after_http_success,
    test_rate_limit_diagnostic_reports_safe_retry,
    test_semantic_roles_require_current_completed_qualification_for_l5,
    test_unqualified_production_provider_cannot_promote_semantic_l5,
]


def main() -> int:
    results = []
    for index, test in enumerate(TESTS, 1):
        try:
            test()
            results.append({"test": f"AI181-{index:03d}", "status": "PASSED"})
        except Exception as exc:
            results.append({
                "test": f"AI181-{index:03d}",
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            })
    payload = {
        "version": "18.1-resilient-free-ai",
        "stage": "Устойчивые бесплатные AI-роли Groq/Gemini",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "quality_policy": {
            "verified_platform_inherited": True,
            "gemini_native_json_schema_required": True,
            "groq_gemini_independent_route_supported": True,
            "rate_limits_are_transport_events": True,
            "qualification_is_resumable": True,
            "l5_requires_two_qualified_providers": True,
        },
        "results": results,
    }
    output = ROOT / "VALIDATION_181.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
