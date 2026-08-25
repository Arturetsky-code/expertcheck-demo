from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


MATRIX_VERSION = "1.0-coverage-reason-matrix"


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
        top_reasons = Counter(str(item.get("coverage_reason_code") or "UNSPECIFIED") for item in items).most_common(5)
        matrix.append({
            "archetype": archetype,
            "total": total,
            "completed": completed,
            "coverage_pct": round(100 * completed / max(1, total), 1),
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
    return {
        "version": MATRIX_VERSION,
        "total": total,
        "completed": completed,
        "coverage_pct": round(100 * completed / max(1, total), 1),
        "matrix": matrix,
        "reason_counts": dict(reason_counts.most_common()),
        "principle": "Покрытие считается только по завершённым доказательным контрактам; системные ограничения не являются замечаниями проекта.",
    }
