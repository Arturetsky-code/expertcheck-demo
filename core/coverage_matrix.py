from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


MATRIX_VERSION = "2.0-strict-and-evidence-coverage-matrix"


def build_coverage_matrix(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate completed checks and automation gaps by evidence archetype."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    reason_counts: Counter[str] = Counter()
    for raw in rows or []:
        row = dict(raw)
        archetype = str(row.get("coverage_archetype") or "UNCLASSIFIED")
        grouped[archetype].append(row)
        reason = str(row.get("coverage_reason_code") or "UNSPECIFIED")
        reason_counts[reason] += 1

    matrix = []
    for archetype, items in sorted(grouped.items()):
        kinds = Counter(str(item.get("verification_kind") or "INFORMATIONAL").upper() for item in items)
        total = len(items)
        completed = kinds["VERIFIED_OK"] + kinds["PROJECT_FINDING"]
        recipes = Counter(str(item.get("recipe_status") or "").upper() for item in items)
        levels = Counter(str(item.get("evidence_level") or "L0").upper() for item in items)
        evidence_ready = levels["L3"] + levels["L4"] + levels["L5"]
        consensus = sum(
            str(item.get("semantic_consensus_state") or "").upper() == "PASSED"
            or int(item.get("semantic_consensus_completed") or 0) > 0
            for item in items
        )
        top_reasons = Counter(str(item.get("coverage_reason_code") or "UNSPECIFIED") for item in items).most_common(5)
        matrix.append({
            "archetype": archetype,
            "total": total,
            "completed": completed,
            "coverage_pct": round(100 * completed / max(1, total), 1),
            "evidence_ready": evidence_ready,
            "evidence_coverage_pct": round(100 * evidence_ready / max(1, total), 1),
            "semantic_consensus_completed": consensus,
            "evidence_levels": {level: levels.get(level, 0) for level in ("L0", "L1", "L2", "L3", "L4", "L5")},
            "verified_ok": kinds["VERIFIED_OK"],
            "project_findings": kinds["PROJECT_FINDING"],
            "review_questions": kinds["REVIEW_QUESTION"],
            "system_limitations": kinds["SYSTEM_LIMITATION"],
            "trusted_recipes": recipes["TRUSTED"],
            "experimental_recipes": recipes["EXPERIMENTAL"],
            "retrieval_only_recipes": recipes["RETRIEVAL_ONLY"],
            "top_gap_reasons": [{"code": code, "count": count} for code, count in top_reasons],
        })

    total = sum(row["total"] for row in matrix)
    completed = sum(row["completed"] for row in matrix)
    evidence_ready = sum(row["evidence_ready"] for row in matrix)
    consensus_completed = sum(row["semantic_consensus_completed"] for row in matrix)
    total_levels = Counter()
    for row in matrix:
        total_levels.update(row.get("evidence_levels") or {})
    return {
        "version": MATRIX_VERSION,
        "total": total,
        "completed": completed,
        "coverage_pct": round(100 * completed / max(1, total), 1),
        "evidence_ready": evidence_ready,
        "evidence_coverage_pct": round(100 * evidence_ready / max(1, total), 1),
        "semantic_consensus_completed": consensus_completed,
        "evidence_levels": {level: total_levels.get(level, 0) for level in ("L0", "L1", "L2", "L3", "L4", "L5")},
        "matrix": matrix,
        "reason_counts": dict(reason_counts.most_common()),
        "principle": "Строгое покрытие считается только по завершённым контрактам L5; доказательное покрытие L3–L5 отдельно показывает, где система уже нашла адресный материал. Ограничения системы не являются замечаниями проекта.",
    }
