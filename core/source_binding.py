from __future__ import annotations

import hashlib
from typing import Any


def _clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def source_locator(item: dict[str, Any]) -> dict[str, Any]:
    """Return a stable physical/logical locator for one extracted fact.

    The locator intentionally separates document/page/table/row/cell identity from
    model confidence. It is used to decide whether two findings are genuinely
    independent confirmations or duplicates of the same extraction event.
    """
    locator = {
        "document": _clean(item.get("document")),
        "page": item.get("page"),
        "table_index": item.get("table_index", item.get("table_no")),
        "row_index": item.get("row_index", item.get("table_row")),
        "column_index": item.get("column_index", item.get("table_column")),
        "cell_ref": _clean(item.get("cell_ref") or item.get("source_cell")),
        "source_span": _clean(item.get("source_span") or item.get("bbox") or item.get("source_bbox") or item.get("coordinates")),
    }
    raw = "|".join(_clean(locator[k]) for k in ("document","page","table_index","row_index","column_index","cell_ref","source_span"))
    if not raw.strip("|"):
        raw = "|".join((_clean(item.get("document")), _clean(item.get("page")), _clean(item.get("evidence_id")), _clean(item.get("context"))[:120]))
    locator["source_fingerprint"] = "SRC-" + hashlib.blake2b(raw.encode("utf-8"), digest_size=8).hexdigest().upper()
    locator["physical_trace_level"] = physical_trace_level(locator)
    return locator


def physical_trace_level(locator_or_item: dict[str, Any]) -> str:
    locator = locator_or_item if "source_fingerprint" in locator_or_item else source_locator(locator_or_item)
    has_doc = bool(locator.get("document"))
    has_page = locator.get("page") not in (None, "")
    has_table = locator.get("table_index") not in (None, "")
    has_row = locator.get("row_index") not in (None, "")
    has_cell = locator.get("column_index") not in (None, "") or bool(locator.get("cell_ref")) or bool(locator.get("source_span"))
    if has_doc and has_page and has_table and has_row and has_cell:
        return "CELL_TRACE"
    if has_doc and has_page and has_table and has_row:
        return "ROW_TRACE"
    if has_doc and has_page:
        return "PAGE_TRACE"
    if has_doc:
        return "DOCUMENT_TRACE"
    return "WEAK_TRACE"


def independent_source_key(item: dict[str, Any]) -> str:
    loc = item.get("source_locator") if isinstance(item.get("source_locator"), dict) else source_locator(item)
    # Evidence from the same physical row is one source, even if several extractors found it.
    if loc.get("physical_trace_level") in {"CELL_TRACE", "ROW_TRACE"}:
        return str(loc.get("source_fingerprint"))
    return "|".join((_clean(item.get("document")), _clean(item.get("page")), _clean(item.get("evidence_id"))))
