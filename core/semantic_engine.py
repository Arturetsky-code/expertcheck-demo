from __future__ import annotations
import re
from difflib import SequenceMatcher

GENERIC_WORDS = {
    "здание", "сооружение", "проектируемый", "проектируемая", "проектируемое",
    "площадка", "объект", "комплекс", "помещение",
}


def normalize_name(value: str) -> str:
    value = (value or "").lower().replace("ё", "е")
    value = re.sub(r"^\s*\d+(?:\.\d+)*\s*[-–—:]?\s*", "", value)
    value = re.sub(r"\b(?:поз(?:иция)?\.?\s*)?\d+(?:\.\d+)+\b", " ", value)
    value = re.sub(r"[^а-яa-z0-9]+", " ", value)
    return " ".join(token for token in value.split() if token not in GENERIC_WORDS)


def object_similarity(a: str, b: str, position_a: str = "", position_b: str = "") -> tuple[float, list[str]]:
    reasons: list[str] = []
    if position_a and position_b and position_a == position_b:
        return 1.0, ["совпала позиция по генплану"]
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0, ["недостаточно данных"]
    ratio = SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    intersection = ta & tb
    jaccard = len(intersection) / max(1, len(ta | tb))
    coverage = len(intersection) / max(1, min(len(ta), len(tb)))
    score = 0.40 * ratio + 0.35 * jaccard + 0.25 * coverage
    if na == nb:
        score = max(score, 0.99)
        reasons.append("совпало нормализованное наименование")
    elif na in nb or nb in na:
        score = max(score, 0.92)
        reasons.append("одно наименование входит в другое")
    elif coverage >= 0.80 and len(intersection) >= 2:
        score = max(score, 0.86)
        reasons.append("совпало большинство значимых слов")
    else:
        reasons.append(f"текстовое сходство {score:.0%}")
    if position_a and position_b and position_a != position_b:
        score = min(score, 0.74)
        reasons.append("позиции по генплану различаются")
    return round(score, 3), reasons
