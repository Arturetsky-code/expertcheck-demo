from __future__ import annotations

import re
from typing import Iterable

from .contracts import Evidence25
from .routing import VerificationRoute


_BLOCKED_SOURCE_KINDS = {
    "TABLE_OF_CONTENTS",
    "TOC",
    "INDEX",
    "DOCUMENT_TITLE",
    "FILE_NAME_ONLY",
}

_ASSERTION_MARKERS = (
    "составляет",
    "предусмотр",
    "принят",
    "установ",
    "оборуд",
    "размещ",
    "обеспеч",
    "выполн",
    "проектом",
    "равн",
)


def _norm(value: str) -> str:
    return " ".join(str(value or "").strip().replace("ё", "е").casefold().split())


def _section_matches(section: str, expected_sections: tuple[str, ...]) -> bool:
    if not expected_sections:
        return True
    low = _norm(section)
    if not low:
        return False
    return any(
        _norm(expected) in low or low in _norm(expected)
        for expected in expected_sections
        if _norm(expected)
    )


def _looks_like_index_line(fragment: str) -> bool:
    text = " ".join(str(fragment or "").split())
    low = _norm(text)
    if any(marker in low for marker in _ASSERTION_MARKERS):
        return False
    if re.search(r"\.{3,}\s*\d+\s*$", text):
        return True
    # Numbered heading with no punctuation/statement verb and no engineering value.
    if re.match(r"^\d+(?:\.\d+)*\s+[A-Za-zА-Яа-яЁё]", text):
        has_value = bool(re.search(r"\d+[,.]?\d*\s*(?:м2|м²|м3|м³|т/ч|квт|мпа|час|%)\b", low))
        if not has_value and len(text.split()) <= 12:
            return True
    return False


def is_canonical_evidence(ev: Evidence25) -> bool:
    metadata = dict(ev.metadata or {})
    source_kind = str(ev.source_kind or ev.source_role or "").strip().upper()
    if not ev.addressable or not ev.canonical:
        return False
    if not ev.resolved_document.strip():
        return False
    if not isinstance(ev.page, int) or ev.page <= 0:
        return False
    if not str(ev.fragment or "").strip():
        return False
    if source_kind in _BLOCKED_SOURCE_KINDS:
        return False
    if metadata.get("is_toc") or metadata.get("is_index") or metadata.get("heading_only"):
        return False
    if _looks_like_index_line(ev.fragment):
        return False
    return True


def _structured_rank(ev: Evidence25) -> int:
    kind = str(ev.source_kind or "").strip().upper()
    if ev.cell_id or kind in {"TABLE_CELL", "TABLE_CELL_LOCKED"}:
        return 0
    if ev.row_id or kind in {"TABLE_ROW", "STRUCTURED_ROW"}:
        return 1
    if ev.table_id:
        return 2
    return 3


def qualify_evidence(
    candidates: Iterable[Evidence25],
    route: VerificationRoute,
) -> tuple[Evidence25, ...]:
    qualified = [
        ev
        for ev in candidates
        if is_canonical_evidence(ev)
        and _section_matches(ev.section or ev.resolved_document, route.expected_sections)
    ]
    if route.prefer_structured_source:
        qualified.sort(key=lambda ev: (_structured_rank(ev), ev.resolved_document, ev.page or 0, ev.evidence_id))
    return tuple(qualified)
