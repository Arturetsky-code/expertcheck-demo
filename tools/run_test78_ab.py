from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

from core.coverage_breakthrough import attach_coverage_executor_evidence
from core.directed_evidence import attach_directed_evidence
from core.page_evidence_store import is_assignment_source
from core25.runtime_bridge import run_assignment_runtime


_ARCHETYPE_BY_EXECUTOR = {
    "GENERIC_PRESENCE_EXECUTOR": "PRESENCE",
    "FENCING_COMPOSITE_EXECUTOR": "COMPOSITE_PRESENCE",
    "OPEN_CANOPY_DRAWING_EXECUTOR": "PRESENCE_PLUS_GRAPHIC_CONFIRMATION",
    "LIGHTING_COMPOSITE_EXECUTOR": "COMPOSITE_ENGINEERING",
    "LIGHTNING_GROUNDING_COMPOSITE_EXECUTOR": "COMPOSITE_ENGINEERING",
    "NEGATIVE_APPLICABILITY_EXECUTOR": "NEGATIVE_APPLICABILITY",
    "DESIGN_DETERMINED_EXECUTOR": "DESIGN_DETERMINED",
    "LANDSCAPING_DESIGN_DETERMINED_EXECUTOR": "DESIGN_DETERMINED_MULTI_EVIDENCE",
    "NORMATIVE_ASSERTION_EXECUTOR": "NORMATIVE_ASSERTION",
    "NORMATIVE_DESIGN_ADOPTION_EXECUTOR": "NORMATIVE_DESIGN_ADOPTION",
    "DYNAMIC_FOUNDATION_NORMATIVE_EXECUTOR": "NORMATIVE_CALCULATION_GRAPHIC",
    "EQUIPMENT_IDENTITY_AND_QUANTITY": "EQUIPMENT_IDENTITY_QUANTITY",
    "CAPACITY_AND_PROCESS_TOPOLOGY": "CAPACITY_PROCESS_TOPOLOGY",
}

_ARCHETYPE_BY_REASON = {
    "TYPED_VALUE_MATCH": "TYPED_VALUE_COMPARISON",
    "ASSIGNMENT_PRESENCE_CONFIRMED": "PRESENCE",
    "ASSIGNMENT_DESIGN_VALUE_CONFIRMED": "DESIGN_DETERMINED",
    "FACTUAL_NORMATIVE_ASSERTION_CONFIRMED": "NORMATIVE_ASSERTION",
    "NEGATIVE_APPLICABILITY_CONFIRMED": "NEGATIVE_APPLICABILITY",
    "ASSIGNMENT_NORMATIVE_DESIGN_ADOPTION_CONFIRMED": "NORMATIVE_DESIGN_ADOPTION",
    "ASSIGNMENT_DYNAMIC_FOUNDATION_NORMATIVE_CONFIRMED": "NORMATIVE_CALCULATION_GRAPHIC",
}


def _universal_archetype(row: dict) -> str:
    executor = str(row.get("coverage_executor") or "")
    reason = str(row.get("core25_reason_code") or "")
    return _ARCHETYPE_BY_EXECUTOR.get(executor) or _ARCHETYPE_BY_REASON.get(reason) or "UNCLASSIFIED_VERIFIED"


def _archetype_summary(rows: list[dict]) -> dict:
    verified = [row for row in rows if row.get("final_verification_kind") == "VERIFIED_OK"]
    counts = Counter(_universal_archetype(row) for row in verified)
    unclassified = int(counts.pop("UNCLASSIFIED_VERIFIED", 0))
    return {
        "universal_archetypes": len(counts),
        "verified_requirements_classified": sum(counts.values()),
        "verified_requirements_unclassified": unclassified,
        "archetypes": dict(sorted(counts.items())),
    }


def _row_summary(row: dict) -> dict:
    return {
        "requirement_id": row.get("requirement_id"),
        "final_verification_kind": row.get("final_verification_kind"),
        "proof_state": row.get("proof_state"),
        "core25_reason_code": row.get("core25_reason_code"),
        "coverage_executor": row.get("coverage_executor"),
        "requirement_type": row.get("requirement_type"),
        "requirement_scope": row.get("requirement_scope"),
        "expected_sections": list(row.get("expected_sections") or []),
        "core25_admission_stage": row.get("core25_admission_stage"),
        "core25_raw_candidate_count": int(row.get("core25_raw_candidate_count") or 0),
        "core25_verified_candidate_count": int(row.get("core25_verified_candidate_count") or 0),
        "core25_qualified_evidence_count": int(row.get("core25_qualified_evidence_count") or 0),
        "core25_binding_counts": dict(row.get("core25_binding_counts") or {}),
        "core25_binding_reason_codes": dict(row.get("core25_binding_reason_codes") or {}),
        "candidate_kind_counts": dict(Counter(
            str(item.get("evidence_kind") or "")
            for item in (row.get("directed_evidence_candidates") or [])
            if isinstance(item, dict)
        )),
        "max_matched_terms": max(
            [len(item.get("matched_terms") or []) for item in (row.get("directed_evidence_candidates") or []) if isinstance(item, dict)] or [0]
        ),
        "max_matched_normative_refs": max(
            [len(item.get("matched_normative_refs") or []) for item in (row.get("directed_evidence_candidates") or []) if isinstance(item, dict)] or [0]
        ),
    }


def _review_frontier(rows: list[dict], limit: int = 12) -> list[dict]:
    review = [row for row in rows if row.get("final_verification_kind") == "REVIEW_QUESTION"]
    review.sort(
        key=lambda row: (
            int(row.get("core25_verified_candidate_count") or 0),
            int(row.get("core25_qualified_evidence_count") or 0),
            int(row.get("core25_raw_candidate_count") or 0),
            bool(row.get("coverage_executor")),
        ),
        reverse=True,
    )
    return [
        {
            "requirement_id": row.get("requirement_id"),
            "requirement_type": row.get("requirement_type"),
            "requirement_scope": row.get("requirement_scope"),
            "expected_sections": row.get("expected_sections") or [],
            "admission_stage": row.get("core25_admission_stage"),
            "raw_candidates": int(row.get("core25_raw_candidate_count") or 0),
            "verified_candidates": int(row.get("core25_verified_candidate_count") or 0),
            "qualified_evidence": int(row.get("core25_qualified_evidence_count") or 0),
            "coverage_executor": row.get("coverage_executor"),
            "proof_reason": row.get("core25_reason_code"),
            "binding_counts": row.get("core25_binding_counts") or {},
            "binding_reason_codes": row.get("core25_binding_reason_codes") or {},
            "candidate_kind_counts": row.get("candidate_kind_counts") or {},
            "max_matched_terms": int(row.get("max_matched_terms") or 0),
            "max_matched_normative_refs": int(row.get("max_matched_normative_refs") or 0),
        }
        for row in review[:limit]
    ]


def _private_review_frontier(rows: list[dict], limit: int = 8) -> list[dict]:
    review = [row for row in rows if row.get("final_verification_kind") == "REVIEW_QUESTION"]
    review.sort(
        key=lambda row: (
            int(row.get("core25_verified_candidate_count") or 0),
            int(row.get("core25_qualified_evidence_count") or 0),
            int(row.get("core25_raw_candidate_count") or 0),
            bool(row.get("coverage_executor")),
        ),
        reverse=True,
    )
    result = []
    for row in review[:limit]:
        candidates = []
        for item in row.get("directed_evidence_candidates") or []:
            if not isinstance(item, dict):
                continue
            candidates.append({
                "evidence_state": item.get("evidence_state"),
                "evidence_kind": item.get("evidence_kind"),
                "document": item.get("document"),
                "document_type": item.get("document_type"),
                "page": item.get("page"),
                "context": item.get("context") or item.get("exact_clause") or item.get("source_trace"),
                "score": item.get("score"),
                "object": item.get("object"),
                "owner_match": item.get("owner_match"),
                "parameter_code": item.get("parameter_code"),
                "value": item.get("value"),
                "unit": item.get("unit"),
                "matched_terms": item.get("matched_terms") or [],
                "matched_normative_refs": item.get("matched_normative_refs") or [],
                "condition_id": item.get("condition_id"),
                "condition_label": item.get("condition_label"),
            })
        result.append({
            "requirement_id": row.get("requirement_id"),
            "requirement_text": row.get("requirement_text"),
            "source_row_title": row.get("source_row_title"),
            "requirement_type": row.get("requirement_type"),
            "requirement_scope": row.get("requirement_scope"),
            "expected_sections": row.get("expected_sections") or [],
            "evidence_contract_v2": row.get("evidence_contract_v2") or {},
            "coverage_executor": row.get("coverage_executor"),
            "coverage_executor_status": row.get("coverage_executor_status"),
            "core25_reason_code": row.get("core25_reason_code"),
            "core25_admission_stage": row.get("core25_admission_stage"),
            "core25_binding_counts": row.get("core25_binding_counts") or {},
            "core25_binding_reason_codes": row.get("core25_binding_reason_codes") or {},
            "candidates": candidates,
        })
    return result


def _counts(rows: list[dict], proven_deviations: int) -> dict:
    kinds = Counter(row.get("final_verification_kind") for row in rows)
    verified = int(kinds.get("VERIFIED_OK", 0))
    review = int(kinds.get("REVIEW_QUESTION", 0))
    return {
        "requirements": len(rows),
        "VERIFIED_OK": verified,
        "REVIEW_QUESTION": review,
        "proven_deviations": int(proven_deviations),
        "strict_categorical_if_deviations_unchanged": verified + int(proven_deviations),
    }


def run(fixture: dict) -> dict:
    requirements = copy.deepcopy(list(fixture.get("requirements") or []))
    corpus = list(fixture.get("page_corpus") or [])
    project_corpus = [page for page in corpus if not is_assignment_source(page)]

    attach_directed_evidence(requirements, project_corpus)
    coverage = attach_coverage_executor_evidence(requirements, project_corpus)
    runtime = run_assignment_runtime(requirements, object_registry=[])
    runtime_rows = list(runtime.get("rows") or [])
    current_rows = [_row_summary(row) for row in runtime_rows]

    baseline_rows = list(fixture.get("baseline_rows") or [])
    before = {row["requirement_id"]: row for row in baseline_rows}
    after = {row["requirement_id"]: row for row in current_rows}
    before_ids = set(before)
    after_ids = set(after)

    missing_ids = sorted(before_ids - after_ids)
    added_ids = sorted(after_ids - before_ids)
    changed = []
    for requirement_id in sorted(before_ids & after_ids):
        b = before[requirement_id]
        a = after[requirement_id]
        if b.get("final_verification_kind") == a.get("final_verification_kind"):
            continue
        changed.append({
            "requirement_id": requirement_id,
            "before_kind": b.get("final_verification_kind"),
            "after_kind": a.get("final_verification_kind"),
            "before_proof": b.get("proof_state"),
            "after_proof": a.get("proof_state"),
            "before_reason": b.get("core25_reason_code"),
            "after_reason": a.get("core25_reason_code"),
            "before_executor": b.get("coverage_executor"),
            "after_executor": a.get("coverage_executor"),
        })

    gains = [
        row for row in changed
        if row["before_kind"] != "VERIFIED_OK" and row["after_kind"] == "VERIFIED_OK"
    ]
    regressions = [
        row for row in changed
        if row["before_kind"] == "VERIFIED_OK" and row["after_kind"] != "VERIFIED_OK"
    ]
    other_changes = [row for row in changed if row not in gains and row not in regressions]

    if missing_ids or added_ids:
        classification = "REQUIREMENT_SET_CHANGED"
    elif regressions:
        classification = "REGRESSION"
    elif len(changed) == 0:
        classification = "NO_CHANGE"
    elif len(gains) == 1 and len(changed) == 1:
        classification = "SINGLE_GAIN"
    elif len(changed) > 1:
        classification = "MULTI_CHANGE_AUDIT_REQUIRED"
    else:
        classification = "CHANGE_AUDIT_REQUIRED"

    proven_deviations = int(fixture.get("proven_deviations") or 0)
    return {
        "schema_version": 1,
        "benchmark": fixture.get("benchmark") or "Test78",
        "baseline_label": fixture.get("baseline_label"),
        "baseline_source_sha": fixture.get("baseline_source_sha"),
        "classification": classification,
        "baseline": _counts(baseline_rows, proven_deviations),
        "current": _counts(current_rows, proven_deviations),
        "requirement_set": {"missing_ids": missing_ids, "added_ids": added_ids},
        "changed_requirements": changed,
        "gains": gains,
        "regressions": regressions,
        "other_changes": other_changes,
        "review_frontier": _review_frontier(current_rows),
        "_private_review_frontier": _private_review_frontier(runtime_rows),
        "archetype_coverage": {
            "baseline": _archetype_summary(baseline_rows),
            "current": _archetype_summary(current_rows),
        },
        "coverage_summary": {
            "executor_hits": coverage.get("executor_hits"),
            "with_candidates": coverage.get("with_candidates"),
            "verified_candidates": coverage.get("verified_candidates"),
            "executors": coverage.get("executors") or {},
        },
    }


def markdown(result: dict) -> str:
    b = result["baseline"]
    c = result["current"]
    lines = [
        "# Test78 deterministic A/B",
        "",
        f"- Classification: **{result['classification']}**",
        f"- Baseline: **{b['VERIFIED_OK']} VERIFIED_OK / {b['REVIEW_QUESTION']} REVIEW**",
        f"- Current: **{c['VERIFIED_OK']} VERIFIED_OK / {c['REVIEW_QUESTION']} REVIEW**",
        f"- Strict categorical (if the separately audited deviations are unchanged): **{c['strict_categorical_if_deviations_unchanged']}/56**",
        f"- Changed requirements: **{len(result['changed_requirements'])}**",
        f"- Universal archetypes (current VERIFIED_OK): **{result['archetype_coverage']['current']['universal_archetypes']}**",
        f"- VERIFIED_OK not yet mapped to a universal archetype: **{result['archetype_coverage']['current']['verified_requirements_unclassified']}**",
        "",
    ]
    if result["changed_requirements"]:
        lines.extend(["## Changed requirement IDs", ""])
        for row in result["changed_requirements"]:
            lines.append(
                f"- `{row['requirement_id']}`: `{row['before_kind']}` → `{row['after_kind']}` "
                f"({row.get('after_reason') or '—'}; {row.get('after_executor') or '—'})"
            )
        lines.append("")
    if result["requirement_set"]["missing_ids"] or result["requirement_set"]["added_ids"]:
        lines.extend([
            "## Requirement-set drift",
            "",
            f"- Missing IDs: {', '.join(result['requirement_set']['missing_ids']) or 'none'}",
            f"- Added IDs: {', '.join(result['requirement_set']['added_ids']) or 'none'}",
            "",
        ])
    lines.extend([
        "> Fixed 56-requirement denominator; project page text is never emitted to logs or output artifacts.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out-dir", default="benchmark_out")
    parser.add_argument("--private-out", default="")
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    result = run(fixture)
    private_frontier = result.pop("_private_review_frontier", [])
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "test78_ab.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "test78_ab.md").write_text(markdown(result), encoding="utf-8")
    if args.private_out:
        private_path = Path(args.private_out)
        private_path.parent.mkdir(parents=True, exist_ok=True)
        private_path.write_text(
            json.dumps({
                "schema_version": 1,
                "benchmark": result.get("benchmark"),
                "baseline_source_sha": result.get("baseline_source_sha"),
                "frontier": private_frontier,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(json.dumps({
        "classification": result["classification"],
        "baseline": result["baseline"],
        "current": result["current"],
        "changed_ids": [row["requirement_id"] for row in result["changed_requirements"]],
        "archetype_coverage": result["archetype_coverage"]["current"],
        "review_frontier": result["review_frontier"][:8],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
