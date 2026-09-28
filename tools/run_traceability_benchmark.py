from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.assignment_verification_kernel import verify_assignment_requirement
from core.coverage_breakthrough import attach_coverage_executor_evidence
from core25.runtime_bridge import run_assignment_runtime


def run_case(case: dict) -> dict:
    requirement = copy.deepcopy(case["requirement"])
    pages = copy.deepcopy(case.get("pages") or [])

    direct = verify_assignment_requirement(requirement, pages)
    attach_coverage_executor_evidence([requirement], pages)
    row = run_assignment_runtime([requirement])["rows"][0]

    expected = str(case.get("expected") or "").upper()
    actual = str(row.get("final_verification_kind") or "").upper()
    passed = actual == expected

    if expected == "VERIFIED_OK":
        passed = passed and row.get("proof_state") == "PROVEN_MATCH"
        passed = passed and row.get("core25_reason_code") == "ASSIGNMENT_CROSS_DOCUMENT_TRACE_CONFIRMED"
        passed = passed and row.get("coverage_executor") == "CROSS_DOCUMENT_TRACE_EXECUTOR"

    return {
        "case_id": case.get("case_id"),
        "expected": expected,
        "actual": actual,
        "passed": bool(passed),
        "proof_state": row.get("proof_state"),
        "reason_code": row.get("core25_reason_code"),
        "coverage_executor": row.get("coverage_executor"),
        "direct_kernel": (direct or {}).get("verification_kernel"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ExpertCheck deterministic traceability contract benchmark")
    parser.add_argument("--benchmark", default="knowledge/benchmarks/traceability_contract_v1.json")
    parser.add_argument("--out-dir", default="benchmark_out")
    args = parser.parse_args()

    payload = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    cases = payload.get("cases") or []
    results = [run_case(case) for case in cases]
    passed = sum(item["passed"] for item in results)
    failed = len(results) - passed
    classification = "PASS" if failed == 0 else "FAIL"

    summary = {
        "benchmark_id": payload.get("benchmark_id"),
        "version": payload.get("version"),
        "classification": classification,
        "cases": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "traceability_benchmark.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Traceability contract benchmark",
        "",
        f"- classification: **{classification}**",
        f"- cases: **{len(results)}**",
        f"- passed: **{passed}**",
        f"- failed: **{failed}**",
        "",
        "| Case | Expected | Actual | Result |",
        "|---|---|---|---|",
    ]
    for item in results:
        lines.append(
            f"| {item['case_id']} | {item['expected']} | {item['actual']} | "
            + ("PASS" if item["passed"] else "FAIL") + " |"
        )
    (out_dir / "traceability_benchmark.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "benchmark_id": summary["benchmark_id"],
        "classification": classification,
        "cases": len(results),
        "passed": passed,
        "failed": failed,
    }, ensure_ascii=False))

    return 0 if classification == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
