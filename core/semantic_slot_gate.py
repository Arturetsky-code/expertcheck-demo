from __future__ import annotations

import math
import re
from typing import Any

from .normalization import normalize_text


GATE_VERSION = "16.0-semantic-slot-contract-v1"

_STOPWORDS = {
    "проверить", "проверка", "наличие", "проект", "проектом", "проектной",
    "документации", "раздел", "часть", "должен", "должна", "должны",
    "требование", "требования", "согласно", "соответствие", "предусмотреть",
    "предусмотрен", "предусмотрена", "предусмотрены", "выполнить", "выполнен",
    "имеется", "указан", "указана", "представлен", "представлена", "приведен",
    "приведена", "отражен", "отражена", "участках", "устройства", "объекта",
    "значение", "значения", "показатель", "показателя",
}


def _norm(value: Any) -> str:
    return normalize_text(value).lower().replace("ё", "е")


def _stem(word: str) -> str:
    clean = re.sub(r"[^a-zа-я0-9-]", "", _norm(word))
    if len(clean) == 5 and clean[-1:] in "аяыиуюео":
        return clean[:-1]
    if len(clean) <= 5:
        return clean
    # A bounded prefix is intentionally conservative.  It tolerates Russian
    # inflection but does not turn a remote synonym into deterministic proof.
    return clean[:6]


def semantic_anchor_terms(requirement: Any) -> list[str]:
    anchors: list[str] = []
    for raw in re.findall(r"[a-zа-я0-9-]{4,}", _norm(requirement), re.I):
        if raw in _STOPWORDS or raw.isdigit():
            continue
        stem = _stem(raw)
        if stem and stem not in anchors:
            anchors.append(stem)
    return anchors[:14]


def evaluate_semantic_slots(
    requirement: Any,
    evidence: Any,
    *,
    minimum_coverage: float = 0.72,
    minimum_matches: int = 2,
) -> dict[str, Any]:
    """Fail closed when evidence covers only a generic fragment of a requirement.

    This gate is for deterministic positive verdicts.  A semantically related
    fragment that fails remains a candidate for independent Judge/Critic; it is
    never converted into a project defect merely because lexical slots are absent.
    """
    anchors = semantic_anchor_terms(requirement)
    evidence_words = {
        _stem(word) for word in re.findall(r"[a-zа-я0-9-]{4,}", _norm(evidence), re.I)
    }
    matched = [anchor for anchor in anchors if anchor in evidence_words]
    missing = [anchor for anchor in anchors if anchor not in evidence_words]
    coverage = 1.0 if not anchors else len(matched) / len(anchors)
    required_matches = min(len(anchors), max(1, minimum_matches))
    threshold_matches = max(required_matches, math.ceil(len(anchors) * minimum_coverage))
    passed = not anchors or len(matched) >= threshold_matches
    reasons: list[str] = []
    if not passed:
        reasons.append(
            "Адресный фрагмент покрывает недостаточно смысловых слотов требования: "
            f"{len(matched)} из {len(anchors)}."
        )
    return {
        "state": "PASSED" if passed else "BLOCKED",
        "version": GATE_VERSION,
        "coverage": round(coverage, 3),
        "anchors": anchors,
        "matched_anchors": matched,
        "missing_anchors": missing,
        "required_matches": threshold_matches,
        "reasons": reasons,
    }
