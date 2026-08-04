from __future__ import annotations

def calculate_confidence(*, genplan_match=False, exact_name=False, table_recognized=False,
                         unit_match=False, cross_document_confirmation=False,
                         legacy_score: float | None = None) -> tuple[float, dict[str, float]]:
    factors = {
        "position_gp": 0.30 if genplan_match else 0.0,
        "exact_name": 0.20 if exact_name else 0.0,
        "table": 0.20 if table_recognized else 0.0,
        "unit": 0.10 if unit_match else 0.0,
        "cross_document": 0.20 if cross_document_confirmation else 0.0,
    }
    score = sum(factors.values())
    if legacy_score is not None:
        score = max(score, min(float(legacy_score), 1.0) * 0.85)
    return round(min(score, 1.0), 3), factors
