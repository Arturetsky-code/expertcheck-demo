from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code


PLAUSIBILITY_VERSION = "1.0-dimensional-source-guard"


def _num(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        number = float(str(value).replace("\u00a0", "").replace(" ", "").replace(",", "."))
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _owner(row: dict[str, Any]) -> str:
    return normalize_text(
        row.get("object_hint") or row.get("semantic_anchor_name")
        or row.get("object_name") or row.get("owner") or ""
    )


def _group_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("document") or ""),
        str(row.get("page") or ""),
        str(row.get("genplan_position") or row.get("semantic_anchor_position") or ""),
        _owner(row),
    )


def _block(
    row: dict[str, Any], *, reason: str, derived_height: float,
    decimal_candidate: float | None = None,
) -> None:
    row["engineering_plausibility_status"] = "BLOCKED_DIMENSIONAL_CONFLICT"
    row["engineering_plausibility_reason"] = reason
    row["engineering_derived_height"] = round(derived_height, 3)
    row["comparison_excluded"] = True
    row["comparison_exclusion_reason"] = reason
    row["project_understanding_binding"] = "Отклонено до проверки источника"
    row["fact_admission_decision"] = "HOLD"
    row["fact_admission_score"] = 0
    row["fact_admission_reasons"] = [reason]
    if decimal_candidate is not None:
        row["possible_decimal_separator_candidate"] = round(decimal_candidate, 3)


def apply_engineering_plausibility_guard(findings: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Quarantine dimensionally inconsistent source values without rewriting them.

    The guard does not "correct" project documentation.  It uses an independent
    dimensional relation only to decide whether a value is safe to admit into the
    project fact graph.  A suspicious value remains visible in diagnostics and can
    never create a compliance verdict until the source is checked.

    Primary invariant for buildings/structures with all three TEPs in the same
    source row: ``building volume / footprint area`` is an independent estimate of
    mean geometric height.  A declared height differing by more than 3x is held.
    This catches missing decimal separators such as 25 m versus 2.5 m while staying
    industry-independent.
    """
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in findings or []:
        if not _owner(row):
            continue
        groups[_group_key(row)].append(row)

    audit_rows: list[dict[str, Any]] = []
    checked = blocked = decimal_candidates = 0
    for key, rows in groups.items():
        by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_code[canonical_parameter_code(row.get("parameter_code"))].append(row)
        areas = [(value, row) for row in by_code.get("AREA_BUILD", []) if (value := _num(row.get("value"))) and value > 0]
        volumes = [(value, row) for row in by_code.get("VOLUME_BUILD", []) if (value := _num(row.get("value"))) and value > 0]
        heights = [(value, row) for row in by_code.get("HEIGHT_BUILD", []) if (value := _num(row.get("value"))) and value > 0]
        if not (areas and volumes and heights):
            continue

        # Prefer source rows sharing the same logical/physical locator.  When the
        # extractor emitted duplicates, select the closest consistent A/V pair.
        pair_candidates = []
        for area, area_row in areas:
            for volume, volume_row in volumes:
                derived = volume / area
                if 0.6 <= derived <= 80:
                    same_row = str(area_row.get("row_index") or area_row.get("table_row") or "") == str(volume_row.get("row_index") or volume_row.get("table_row") or "")
                    pair_candidates.append((1 if same_row else 0, derived, area_row, volume_row))
        if not pair_candidates:
            continue
        pair_candidates.sort(key=lambda item: (item[0], -abs(item[1] - 4.0)), reverse=True)
        _same_row, derived_height, area_row, volume_row = pair_candidates[0]

        for declared_height, height_row in heights:
            checked += 1
            ratio = declared_height / derived_height
            if 1 / 3 <= ratio <= 3:
                height_row.setdefault("engineering_plausibility_status", "PASSED_DIMENSIONAL_CHECK")
                continue
            decimal_candidate = None
            for candidate in (declared_height / 10, declared_height / 100, declared_height * 10):
                if math.isclose(candidate, derived_height, rel_tol=0.35, abs_tol=0.35):
                    decimal_candidate = candidate
                    decimal_candidates += 1
                    break
            reason = (
                f"Заявленная высота {declared_height:g} м размерно противоречит площади застройки "
                f"{_num(area_row.get('value')):g} м² и строительному объёму "
                f"{_num(volume_row.get('value')):g} м³: расчётная средняя высота около "
                f"{derived_height:.2f} м. Значение удержано как возможная ошибка исходного документа."
            )
            _block(height_row, reason=reason, derived_height=derived_height, decimal_candidate=decimal_candidate)
            blocked += 1
            audit_rows.append({
                "document": key[0], "page": key[1], "position": key[2], "object": key[3],
                "declared_height": declared_height, "derived_height": round(derived_height, 3),
                "possible_decimal_candidate": round(decimal_candidate, 3) if decimal_candidate is not None else None,
                "decision": "HOLD", "reason": reason,
            })

    return {
        "version": PLAUSIBILITY_VERSION,
        "checked_height_triplets": checked,
        "blocked_dimensional_conflicts": blocked,
        "decimal_separator_candidates": decimal_candidates,
        "items": audit_rows,
    }
