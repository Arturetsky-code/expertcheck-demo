from __future__ import annotations
import re
from difflib import SequenceMatcher

def normalize_name(value: str) -> str:
    value = (value or "").lower().replace("ё", "е")
    value = re.sub(r"^\s*\d+(?:\.\d+)*\s*[-–—:]?\s*", "", value)
    value = re.sub(r"[^а-яa-z0-9]+", " ", value)
    stop = {"здание", "сооружение", "проектируемый", "проектируемая", "проектируемое"}
    return " ".join(x for x in value.split() if x not in stop)

def object_similarity(a: str, b: str, position_a: str = "", position_b: str = "") -> tuple[float, list[str]]:
    reasons=[]
    if position_a and position_b and position_a == position_b:
        return 1.0, ["совпала позиция по генплану"]
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0, ["недостаточно данных"]
    ratio = SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / max(1, len(ta | tb))
    score = 0.55 * ratio + 0.45 * jaccard
    if na == nb:
        score = max(score, 0.98); reasons.append("совпало нормализованное наименование")
    elif na in nb or nb in na:
        score = max(score, 0.90); reasons.append("одно наименование входит в другое")
    else:
        reasons.append(f"текстовое сходство {score:.0%}")
    return round(score, 3), reasons
