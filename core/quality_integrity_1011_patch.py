from __future__ import annotations

import math
from typing import Any

_INSTALLED = False
_ORIGINAL_BUILD = None
_SENTINELS = {"", "nan", "none", "null", "nat", "<na>"}


def _clean_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    text = str(value).strip()
    return "" if text.casefold() in _SENTINELS else text


def clean_source_text(value: Any) -> str:
    """Remove serialization sentinels without losing the human source trace."""
    text = _clean_scalar(value)
    if not text:
        return ""
    parts = [part.strip() for part in text.split(",")]
    parts = [part for part in parts if _clean_scalar(part)]
    return ", ".join(parts)


def compact_source_clean(rec: dict[str, Any] | None) -> str:
    row = dict(rec or {})
    parts: list[str] = []
    document_type = _clean_scalar(row.get("document_type"))
    section = _clean_scalar(row.get("section"))
    page = _clean_scalar(row.get("page"))
    table = _clean_scalar(row.get("table"))
    document = _clean_scalar(row.get("document"))
    if document_type:
        parts.append(document_type)
    if section:
        parts.append(section[:70])
    if page:
        parts.append(f"стр. {page}")
    if table:
        parts.append(table[:70])
    return ", ".join(parts) or document or "Источник не определён"


def _sanitize_assembly_row(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    for key in ("Источники", "Основание включения", "Канонический источник"):
        if key in result:
            result[key] = clean_source_text(result.get(key))
    return result


def install_quality_integrity_1011_patch() -> None:
    """Keep NaN-like runtime values out of engineer-facing object provenance."""
    global _INSTALLED, _ORIGINAL_BUILD
    if _INSTALLED:
        return

    from . import evidence_registry as evidence_registry
    from . import project_assembly as project_assembly

    evidence_registry.compact_source = compact_source_clean
    project_assembly.compact_source = compact_source_clean

    _ORIGINAL_BUILD = project_assembly.build_assembly_rows

    def build_assembly_rows_clean(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        rows = _ORIGINAL_BUILD(*args, **kwargs)
        return [_sanitize_assembly_row(row) for row in rows]

    project_assembly.build_assembly_rows = build_assembly_rows_clean
    _INSTALLED = True


__all__ = [
    "clean_source_text",
    "compact_source_clean",
    "install_quality_integrity_1011_patch",
]
