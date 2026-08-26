#!/usr/bin/env python3
"""Dependency-free quality gate for the Semantic Evidence Judge/Critic pair."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_semantic_evidence_engine_140a1 import (  # noqa: E402
    test_ai_contradiction_requires_explicit_machine_readable_conflict,
    test_critic_concern_blocks_promotion,
    test_explicit_conflict_survives_independent_consensus,
    test_external_agent_payload_is_bounded_and_pseudonymised,
    test_hallucinated_evidence_id_is_rejected_before_critic,
    test_independent_judge_and_critic_promote_only_to_l5,
    test_normative_clause_remains_specialist_only_without_verified_kb_clause,
    test_packet_reaches_l4_only_with_addressable_contract_ready_evidence,
    test_same_actual_provider_blocks_consensus_even_for_two_configured_roles,
)


TESTS = [
    test_packet_reaches_l4_only_with_addressable_contract_ready_evidence,
    test_independent_judge_and_critic_promote_only_to_l5,
    test_same_actual_provider_blocks_consensus_even_for_two_configured_roles,
    test_hallucinated_evidence_id_is_rejected_before_critic,
    test_critic_concern_blocks_promotion,
    test_ai_contradiction_requires_explicit_machine_readable_conflict,
    test_explicit_conflict_survives_independent_consensus,
    test_normative_clause_remains_specialist_only_without_verified_kb_clause,
    test_external_agent_payload_is_bounded_and_pseudonymised,
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
        "version": "14.0-alpha1-semantic-evidence-engine",
        "tests": len(results),
        "passed": sum(row["status"] == "PASSED" for row in results),
        "failed": sum(row["status"] == "FAILED" for row in results),
        "results": results,
    }
    (ROOT / "AI_AGENT_VALIDATION_140_ALPHA1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
