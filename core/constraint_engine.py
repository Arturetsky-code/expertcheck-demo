from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from .normalization import normalize_text
from .property_intelligence import normalize_engineering_value


ENGINE_VERSION = "1.0-numeric-constraint-engine"
SUPPORTED_OPERATORS = {"EQ", "NE", "GE", "GT", "LE", "LT", "BETWEEN"}


@dataclass(frozen=True)
class NumericConstraint:
    operator: str
    unit: str
    value: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    minimum_inclusive: bool = True
    maximum_inclusive: bool = True


def _number(value: Any) -> float | None:
    try:
        number = float(str(value).replace("\u00a0", "").replace(" ", "").replace(",", "."))
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def infer_comparison_operator(text: Any, value_start: int | None = None) -> str:
    """Infer a mathematical operator only from an explicit local marker."""
    source = normalize_text(text).lower().replace("ё", "е")
    prefix = source[:value_start] if value_start is not None else source
    prefix = prefix[-64:]
    rules = (
        (r"(?:не\s+менее|не\s+ниже|как\s+минимум|минимум|≥|>=)\s*$", "GE"),
        (r"(?:не\s+более|не\s+выше|как\s+максимум|максимум|≤|<=)\s*$", "LE"),
        (r"(?:более|свыше|выше|>)\s*$", "GT"),
        (r"(?:менее|ниже|<)\s*$", "LT"),
        (r"(?:не\s+равн(?:о|а)|≠|!=)\s*$", "NE"),
        (r"(?:равн(?:о|а)|составляет|=)\s*$", "EQ"),
    )
    for pattern, operator in rules:
        if re.search(pattern, prefix, re.I):
            return operator
    return "EQ"


def constraint_from_atom(atom: dict[str, Any]) -> NumericConstraint | None:
    operator = str(atom.get("comparison_operator") or "EQ").upper()
    if operator not in SUPPORTED_OPERATORS:
        return None
    unit = str(atom.get("unit") or "").strip()
    if operator == "BETWEEN":
        minimum = _number(atom.get("required_min"))
        maximum = _number(atom.get("required_max"))
        if minimum is None or maximum is None:
            return None
        if minimum > maximum:
            minimum, maximum = maximum, minimum
        return NumericConstraint(
            operator=operator,
            unit=unit,
            minimum=minimum,
            maximum=maximum,
            minimum_inclusive=bool(atom.get("minimum_inclusive", True)),
            maximum_inclusive=bool(atom.get("maximum_inclusive", True)),
        )
    value = _number(atom.get("required_value"))
    return NumericConstraint(operator=operator, unit=unit, value=value) if value is not None else None


def _canonical_value(value: float, unit: str, parameter_code: str) -> tuple[float, str]:
    normalized = normalize_engineering_value({
        "parameter_code": parameter_code,
        "value": value,
        "unit": unit,
    })
    if normalized is None:
        return value, unit
    return normalized.value, normalized.unit


def canonicalize_constraint(constraint: NumericConstraint, parameter_code: str) -> NumericConstraint:
    samples = [value for value in (constraint.value, constraint.minimum, constraint.maximum) if value is not None]
    if not samples:
        return constraint
    converted = [_canonical_value(value, constraint.unit, parameter_code) for value in samples]
    units = {unit for _, unit in converted}
    if len(units) != 1:
        return constraint
    values = iter(value for value, _ in converted)
    return NumericConstraint(
        operator=constraint.operator,
        unit=next(iter(units)),
        value=next(values) if constraint.value is not None else None,
        minimum=next(values) if constraint.minimum is not None else None,
        maximum=next(values) if constraint.maximum is not None else None,
        minimum_inclusive=constraint.minimum_inclusive,
        maximum_inclusive=constraint.maximum_inclusive,
    )


def canonicalize_observed(value: Any, unit: Any, parameter_code: str) -> tuple[float, str] | None:
    number = _number(value)
    if number is None:
        return None
    return _canonical_value(number, str(unit or ""), parameter_code)


def _tolerance(reference: float) -> float:
    return max(0.0001, abs(reference) * 0.0005)


def evaluate_numeric_constraint(constraint: NumericConstraint, observed: float) -> dict[str, Any]:
    operator = constraint.operator
    satisfied = False
    delta: float | None = None
    if operator in {"EQ", "NE", "GE", "GT", "LE", "LT"}:
        required = float(constraint.value)
        delta = observed - required
        close = math.isclose(required, observed, rel_tol=0.002, abs_tol=_tolerance(required))
        satisfied = {
            "EQ": close,
            "NE": not close,
            "GE": observed > required or close,
            "GT": observed > required and not close,
            "LE": observed < required or close,
            "LT": observed < required and not close,
        }[operator]
    elif operator == "BETWEEN":
        minimum = float(constraint.minimum)
        maximum = float(constraint.maximum)
        lower_close = math.isclose(observed, minimum, rel_tol=0.002, abs_tol=_tolerance(minimum))
        upper_close = math.isclose(observed, maximum, rel_tol=0.002, abs_tol=_tolerance(maximum))
        lower_ok = observed > minimum or (constraint.minimum_inclusive and lower_close)
        upper_ok = observed < maximum or (constraint.maximum_inclusive and upper_close)
        satisfied = lower_ok and upper_ok
        if observed < minimum:
            delta = observed - minimum
        elif observed > maximum:
            delta = observed - maximum
        else:
            delta = 0.0
    return {
        "engine_version": ENGINE_VERSION,
        "operator": operator,
        "satisfied": satisfied,
        "observed": observed,
        "required": constraint.value,
        "required_min": constraint.minimum,
        "required_max": constraint.maximum,
        "unit": constraint.unit,
        "delta": delta,
    }


def requirement_text(constraint: NumericConstraint) -> str:
    labels = {"EQ": "равно", "NE": "не равно", "GE": "не менее", "GT": "более", "LE": "не более", "LT": "менее"}
    if constraint.operator == "BETWEEN":
        return f"от {constraint.minimum:g} до {constraint.maximum:g} {constraint.unit}".strip()
    return f"{labels.get(constraint.operator, constraint.operator)} {constraint.value:g} {constraint.unit}".strip()
