from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class CoverageBudget:
    review_mode: str
    ai_level: str
    assignment_semantic_limit: int
    checklist_semantic_limit: int
    policy: str = "ALL_ADDRESSABLE_L4_WITH_FAIL_CLOSED_CONSENSUS"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def coverage_budget(review_mode: str = "extended", ai_level: str = "extended") -> CoverageBudget:
    """Budget addressable L4 packets according to the user-visible review mode."""
    mode = str(review_mode or "extended").strip().lower()
    level = str(ai_level or "extended").strip().lower()
    if level in {"off", "helper", "отключён", "помощник"}:
        return CoverageBudget(mode, level, 0, 0, "DETERMINISTIC_ONLY")
    if mode == "quick":
        return CoverageBudget(mode, level, 40, 80, "BOUNDED_HIGH_PRIORITY_L4")
    if mode == "full" or level in {"maximum", "максимальный"}:
        return CoverageBudget(mode, level, 1000, 5000)
    return CoverageBudget(mode, level, 200, 800)


def diversified_candidate_order(packets: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interleave checker families before applying any configured queue cap."""
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for packet in packets or []:
        checker = packet.get("checker") or {}
        key = (
            str(packet.get("domain") or ""),
            str(checker.get("checker_family") or ""),
            ",".join(str(value) for value in packet.get("expected_sections") or []),
        )
        buckets.setdefault(key, []).append(packet)
    for rows in buckets.values():
        rows.sort(
            key=lambda packet: max(
                [int(item.get("retrieval_score") or item.get("score") or 0) for item in packet.get("evidence") or []]
                or [0]
            ),
            reverse=True,
        )
    ordered: list[dict[str, Any]] = []
    keys = sorted(buckets)
    while keys:
        next_keys: list[tuple[str, str, str]] = []
        for key in keys:
            rows = buckets[key]
            if rows:
                ordered.append(rows.pop(0))
            if rows:
                next_keys.append(key)
        keys = next_keys
    return ordered
