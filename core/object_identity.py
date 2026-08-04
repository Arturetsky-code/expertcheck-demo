from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Iterable

from .object_register_engine import normalize_name, name_similarity, normalize_position

STOPWORDS = {
    "здание", "сооружение", "объект", "площадка", "комплекс", "проектируемый",
    "проектируемая", "проектируемое", "существующий", "существующая", "поз",
}


def _tokens(value: str) -> list[str]:
    normalized = normalize_name(value)
    return [token for token in normalized.split() if token and token not in STOPWORDS]


def _abbreviation(value: str) -> str:
    tokens = _tokens(value)
    return "".join(token[0] for token in tokens if token)


def _contains_abbreviation(short_name: str, long_name: str) -> bool:
    short_tokens = _tokens(short_name)
    long_tokens = _tokens(long_name)
    if len(short_tokens) != 1 or len(short_tokens[0]) < 2 or len(long_tokens) < 2:
        return False
    candidate = re.sub(r"[^а-яa-z0-9]", "", short_tokens[0])
    return candidate == _abbreviation(long_name)


@dataclass(frozen=True)
class IdentityDecision:
    score: float
    method: str
    reasons: tuple[str, ...]
    conflicting_position: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "method": self.method,
            "reasons": list(self.reasons),
            "conflicting_position": self.conflicting_position,
        }


class ObjectIdentityEngine:
    """Универсальное сопоставление реестровых записей без отраслевых условий."""

    def compare(
        self,
        left_name: str,
        right_name: str,
        left_position: str = "",
        right_position: str = "",
    ) -> IdentityDecision:
        lp = normalize_position(left_position)
        rp = normalize_position(right_position)
        if lp and rp:
            if lp == rp:
                text_score = name_similarity(left_name, right_name)
                return IdentityDecision(
                    score=max(0.97, text_score),
                    method="exact_position",
                    reasons=("совпала точная позиция по генплану",),
                )
            return IdentityDecision(
                score=0.0,
                method="position_conflict",
                reasons=("позиции по генплану различаются",),
                conflicting_position=True,
            )

        ln, rn = normalize_name(left_name), normalize_name(right_name)
        if not ln or not rn:
            return IdentityDecision(0.0, "insufficient", ("недостаточно данных для сопоставления",))
        if ln == rn:
            return IdentityDecision(0.99, "exact_name", ("совпало нормализованное наименование",))
        if ln in rn or rn in ln:
            return IdentityDecision(0.93, "contained_name", ("одно наименование входит в другое",))
        if _contains_abbreviation(left_name, right_name) or _contains_abbreviation(right_name, left_name):
            return IdentityDecision(0.92, "abbreviation", ("сокращение соответствует полному наименованию",))

        lt, rt = set(_tokens(left_name)), set(_tokens(right_name))
        common = lt & rt
        coverage = len(common) / max(1, min(len(lt), len(rt)))
        jaccard = len(common) / max(1, len(lt | rt))
        sequence = SequenceMatcher(None, ln, rn).ratio()
        score = 0.45 * coverage + 0.30 * jaccard + 0.25 * sequence
        if coverage >= 0.8 and len(common) >= 2:
            score = max(score, 0.87)
            method = "token_coverage"
            reasons = ("совпало большинство значимых слов",)
        else:
            method = "text_similarity"
            reasons = (f"текстовое сходство {score:.0%}",)
        return IdentityDecision(round(score, 3), method, reasons)

    def best_position_match(
        self,
        candidate: dict[str, Any],
        positioned: dict[str, list[dict[str, Any]]],
        threshold: float = 0.90,
        margin: float = 0.08,
    ) -> tuple[str, IdentityDecision | None, float]:
        scores: list[tuple[float, str, IdentityDecision]] = []
        candidate_name = str(candidate.get("_name") or "")
        for position, rows in positioned.items():
            decisions = [self.compare(candidate_name, str(row.get("_name") or "")) for row in rows]
            decision = max(decisions, key=lambda item: item.score)
            scores.append((decision.score, position, decision))
        scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
        if not scores:
            return "", None, 0.0
        top = scores[0]
        second_score = scores[1][0] if len(scores) > 1 else 0.0
        if top[0] >= threshold and top[0] - second_score >= margin:
            return top[1], top[2], second_score
        return "", top[2], second_score
