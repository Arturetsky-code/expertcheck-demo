from __future__ import annotations

import re
from datetime import date
from typing import Any

_POSITION_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){0,5}$")
_CLASSIFIER_RE = re.compile(r"^\d{2}\.\d{2}\.\d{3}\.\d{3}$")
_DATE_SEPARATORS_RE = re.compile(r"^(?P<a>\d{1,4})[./-](?P<b>\d{1,2})[./-](?P<c>\d{1,4})(?:[ T].*)?$")


def is_date_like_position(value: Any) -> bool:
    """Return True for values that are much more likely dates than GP positions.

    Handles dd.mm.yy, dd.mm.yyyy, yyyy.mm.dd and common slash/dash variants.
    A syntactically valid calendar date is always rejected as a position.
    """
    text = re.sub(r"\s+", "", str(value or "").strip())
    match = _DATE_SEPARATORS_RE.fullmatch(text)
    if not match:
        return False
    a, b, c = (int(match.group(name)) for name in ("a", "b", "c"))
    candidates: list[tuple[int, int, int]] = []
    # dd.mm.yy / dd.mm.yyyy
    # Two-digit years are ambiguous with hierarchical GP positions (3.3.20).
    # Reject them as dates only when the first component cannot be a month-like
    # hierarchy component (>12). Four-digit years remain unambiguous dates.
    if 1 <= a <= 31 and 1 <= b <= 12 and (1900 <= c <= 2199 or (20 <= c <= 99 and a > 12)):
        year = 2000 + c if c <= 69 else (1900 + c if c <= 99 else c)
        candidates.append((year, b, a))
    # yyyy.mm.dd
    if 1900 <= a <= 2199 and 1 <= b <= 12 and 1 <= c <= 31:
        candidates.append((a, b, c))
    for year, month, day in candidates:
        try:
            date(year, month, day)
            return True
        except ValueError:
            continue
    return False


def normalize_genplan_position(value: Any, *, allow_integer: bool = True) -> str:
    text = re.sub(r"\s+", "", str(value or "").strip()).replace(",", ".")
    if not text or not _POSITION_RE.fullmatch(text) or _CLASSIFIER_RE.fullmatch(text):
        return ""
    if not allow_integer and "." not in text:
        return ""
    if is_date_like_position(text):
        return ""
    try:
        parts = [int(part) for part in text.split(".")]
    except ValueError:
        return ""
    if any(part > 999 for part in parts):
        return ""
    return text
