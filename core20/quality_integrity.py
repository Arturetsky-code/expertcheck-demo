from __future__ import annotations

"""Dependency-light helpers for Alpha 10.1 result integrity.

These functions intentionally avoid pandas/Streamlit so the same semantics are
used by the UI and by the Core20 CI regression suite.
"""

from typing import Any


_EMPTY_TEXT = {"", "nan", "none", "null", "nat"}


def present(value: Any) -> bool:
    """Return False for empty/NaN-like values without importing pandas."""
    if value is None:
        return False
    try:
        if value != value:  # float('nan') and compatible scalar NaN values
            return False
    except (TypeError, ValueError):
        pass
    if isinstance(value, str) and value.strip().casefold() in _EMPTY_TEXT:
        return False
    if isinstance(value, (list, tuple, set, dict)) and not value:
        return False
    return True


def as_list(value: Any) -> list[str]:
    """Normalise legacy scalar/list fields used by cross-section gates."""
    if not present(value):
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if present(item) and str(item).strip()]
    return [str(value).strip()]


def safe_count(value: Any) -> int:
    """Convert report-facing counters without leaking NaN or negatives."""
    try:
        number = float(value or 0)
        if number != number:
            return 0
        return max(0, int(number))
    except (TypeError, ValueError, OverflowError):
        return 0


def consensus_counts(coverage: dict[str, Any] | None, normative: dict[str, Any] | None) -> tuple[int, int, int]:
    """Return current Judge+Critic totals for matrix and normative proof streams."""
    matrix = safe_count((coverage or {}).get("semantic_consensus_completed"))
    normative_state = normative or {}
    normative_count = (
        0
        if normative_state.get("semantic_proof_stale")
        else safe_count(normative_state.get("semantic_proof_applied"))
    )
    return matrix, normative_count, matrix + normative_count


__all__ = ["present", "as_list", "safe_count", "consensus_counts"]
