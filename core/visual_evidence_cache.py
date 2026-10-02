from __future__ import annotations

import base64
import hashlib
from collections import defaultdict
from typing import Any, Iterable

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional runtime dependency
    fitz = None


CACHE_VERSION = "25.2-visual-evidence-cache-alpha1"


def _uploaded_name(value: Any) -> str:
    return str(getattr(value, "name", "") or "")


def visual_page_requests(
    visual_item_queue: Iterable[dict[str, Any]] | None,
    *,
    max_pages: int = 24,
) -> list[dict[str, Any]]:
    """Build a deterministic page-render plan from element-level Visual Proof work.

    One page may serve several elements and several normative contracts. The
    function is routing only: it never changes a proof/verdict.
    """
    grouped: dict[tuple[str, int], dict[str, Any]] = {}
    for item in visual_item_queue or []:
        if not isinstance(item, dict):
            continue
        for rank, page in enumerate(item.get("candidate_pages") or [], 1):
            if not isinstance(page, dict):
                continue
            document = str(page.get("document") or "").strip()
            try:
                page_no = int(page.get("page") or 0)
            except (TypeError, ValueError):
                page_no = 0
            if not document or page_no <= 0:
                continue
            key = (document, page_no)
            row = grouped.setdefault(key, {
                "document": document,
                "page": page_no,
                "section": str(page.get("section") or ""),
                "selection_sources": [],
                "visual_kinds": [],
                "item_ids": [],
                "requirement_ids": [],
                "labels": [],
                "best_rank": rank,
            })
            row["best_rank"] = min(int(row.get("best_rank") or rank), rank)
            selection_source = str(
                page.get("selection_source")
                or item.get("selection_source")
                or ""
            ).strip()
            visual_kind = str(item.get("visual_kind") or "").strip()
            item_id = str(item.get("item_id") or "").strip()
            requirement_id = str(item.get("requirement_id") or "").strip()
            label = str(item.get("label") or "").strip()
            for field, value in (
                ("selection_sources", selection_source),
                ("visual_kinds", visual_kind),
                ("item_ids", item_id),
                ("requirement_ids", requirement_id),
                ("labels", label),
            ):
                if value and value not in row[field]:
                    row[field].append(value)

    ordered = sorted(
        grouped.values(),
        key=lambda row: (
            int(row.get("best_rank") or 99),
            -len(row.get("item_ids") or []),
            str(row.get("document") or ""),
            int(row.get("page") or 0),
        ),
    )
    return ordered[:max(0, int(max_pages or 0))]


def _read_uploaded_bytes(uploaded: Any) -> bytes:
    if hasattr(uploaded, "getvalue"):
        return bytes(uploaded.getvalue())
    if hasattr(uploaded, "seek"):
        uploaded.seek(0)
    data = uploaded.read() if hasattr(uploaded, "read") else bytes(uploaded)
    if hasattr(uploaded, "seek"):
        uploaded.seek(0)
    return bytes(data)


def _render_page(
    page: Any,
    *,
    target_dpi: int,
    jpeg_quality: int,
    max_side: int,
) -> tuple[bytes, str, int, int, int]:
    rect = page.rect
    longest_points = max(float(rect.width or 1.0), float(rect.height or 1.0))
    bounded_dpi = min(
        int(target_dpi),
        max(54, int(float(max_side) * 72.0 / longest_points)),
    )
    zoom = float(bounded_dpi) / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False, colorspace=fitz.csRGB)
    try:
        payload = pix.tobytes("jpeg", jpg_quality=int(jpeg_quality))
        mime = "image/jpeg"
    except Exception:
        payload = pix.tobytes("png")
        mime = "image/png"
    return payload, mime, int(pix.width), int(pix.height), bounded_dpi


def build_visual_evidence_cache(
    pdf_files: Iterable[Any] | None,
    visual_item_queue: Iterable[dict[str, Any]] | None,
    *,
    target_dpi: int = 108,
    jpeg_quality: int = 72,
    max_side: int = 2600,
    max_pages: int = 24,
    max_page_bytes: int = 2_200_000,
    max_total_bytes: int = 24_000_000,
) -> dict[str, Any]:
    """Render only pages needed by Visual Proof and persist them as compact images.

    The cache intentionally stores page pixels, not complete PDFs. It is safe to
    resume later because every entry is bound to document + page + image hash.
    """
    requests = visual_page_requests(visual_item_queue, max_pages=max_pages)
    base = {
        "version": CACHE_VERSION,
        "planned_pages": len(requests),
        "cached_pages": 0,
        "omitted_pages": 0,
        "image_bytes": 0,
        "entries": [],
        "audit": [],
        "persisted_for_resume": True,
        "principle": (
            "Кэш содержит только адресные страницы Visual Proof. Наличие страницы "
            "или текстового маркера само по себе не подтверждает графическое требование."
        ),
    }
    if not requests:
        return base
    if fitz is None:
        base["audit"].append({"decision": "unavailable", "reason": "PyMuPDF недоступен"})
        base["omitted_pages"] = len(requests)
        return base

    file_map = {
        _uploaded_name(uploaded): uploaded
        for uploaded in (pdf_files or [])
        if _uploaded_name(uploaded)
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for request in requests:
        grouped[str(request.get("document") or "")].append(request)

    total_bytes = 0
    for document, doc_requests in grouped.items():
        uploaded = file_map.get(document)
        if uploaded is None:
            for request in doc_requests:
                base["audit"].append({
                    "document": document,
                    "page": request.get("page"),
                    "decision": "source_pdf_unavailable",
                })
            continue
        try:
            data = _read_uploaded_bytes(uploaded)
            pdf = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:
            for request in doc_requests:
                base["audit"].append({
                    "document": document,
                    "page": request.get("page"),
                    "decision": "open_error",
                    "reason": str(exc)[:300],
                })
            continue

        try:
            for request in doc_requests:
                page_no = int(request.get("page") or 0)
                if page_no < 1 or page_no > len(pdf):
                    base["audit"].append({
                        "document": document,
                        "page": page_no,
                        "decision": "page_out_of_range",
                    })
                    continue

                rendered = None
                # Prefer the requested quality, then step down to stay bounded.
                for dpi in dict.fromkeys((target_dpi, 96, 84, 72)):
                    try:
                        candidate = _render_page(
                            pdf[page_no - 1],
                            target_dpi=int(dpi),
                            jpeg_quality=jpeg_quality,
                            max_side=max_side,
                        )
                    except Exception as exc:
                        base["audit"].append({
                            "document": document,
                            "page": page_no,
                            "decision": "render_error",
                            "reason": str(exc)[:300],
                        })
                        candidate = None
                    if candidate is None:
                        continue
                    rendered = candidate
                    if len(candidate[0]) <= max_page_bytes:
                        break

                if rendered is None:
                    continue
                payload, mime, width, height, dpi_used = rendered
                if len(payload) > max_page_bytes:
                    base["audit"].append({
                        "document": document,
                        "page": page_no,
                        "decision": "page_too_large",
                        "bytes": len(payload),
                    })
                    continue
                if total_bytes + len(payload) > max_total_bytes:
                    base["audit"].append({
                        "document": document,
                        "page": page_no,
                        "decision": "total_cache_limit",
                        "bytes": len(payload),
                    })
                    continue

                digest = hashlib.sha256(payload).hexdigest()
                cache_id = f"VIS-{digest[:16]}"
                base["entries"].append({
                    "cache_id": cache_id,
                    "document": document,
                    "page": page_no,
                    "section": request.get("section") or "",
                    "selection_sources": list(request.get("selection_sources") or []),
                    "visual_kinds": list(request.get("visual_kinds") or []),
                    "item_ids": list(request.get("item_ids") or []),
                    "requirement_ids": list(request.get("requirement_ids") or []),
                    "labels": list(request.get("labels") or []),
                    "best_rank": int(request.get("best_rank") or 0),
                    "mime_type": mime,
                    "width": width,
                    "height": height,
                    "dpi": dpi_used,
                    "image_sha256": digest,
                    "image_bytes": len(payload),
                    "image_base64": base64.b64encode(payload).decode("ascii"),
                })
                total_bytes += len(payload)
        finally:
            pdf.close()

    base["cached_pages"] = len(base["entries"])
    base["omitted_pages"] = max(0, len(requests) - len(base["entries"]))
    base["image_bytes"] = total_bytes
    return base


def build_visual_page_batches(
    visual_item_queue: Iterable[dict[str, Any]] | None,
    cache: dict[str, Any] | None,
) -> dict[str, Any]:
    """Group element-level visual work by cached page for a future vision call."""
    entries = [
        dict(row) for row in ((cache or {}).get("entries") or [])
        if isinstance(row, dict)
    ]
    by_page = {
        (str(row.get("document") or ""), int(row.get("page") or 0)): row
        for row in entries
        if row.get("document") and int(row.get("page") or 0) > 0
    }
    batches: dict[tuple[str, int], dict[str, Any]] = {}
    unresolved = []
    unique_items = set()

    for item in visual_item_queue or []:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("item_id") or "")
        matched = False
        for rank, page in enumerate(item.get("candidate_pages") or [], 1):
            if not isinstance(page, dict):
                continue
            document = str(page.get("document") or "")
            try:
                page_no = int(page.get("page") or 0)
            except (TypeError, ValueError):
                page_no = 0
            cached = by_page.get((document, page_no))
            if cached is None:
                continue
            matched = True
            unique_items.add(item_id)
            key = (document, page_no)
            batch = batches.setdefault(key, {
                "batch_id": f"VIS-BATCH-{cached.get('cache_id') or len(batches)+1}",
                "cache_id": cached.get("cache_id") or "",
                "document": document,
                "page": page_no,
                "mime_type": cached.get("mime_type") or "",
                "image_sha256": cached.get("image_sha256") or "",
                "image_bytes": int(cached.get("image_bytes") or 0),
                "items": [],
            })
            batch["items"].append({
                "item_id": item_id,
                "requirement_id": item.get("requirement_id") or "",
                "element_id": item.get("element_id") or "",
                "label": item.get("label") or "",
                "topic": item.get("topic") or "",
                "candidate_rank": rank,
                "localization_source": item.get("localization_source") or "",
                "review_question": item.get("review_question") or "",
            })
        if not matched:
            unresolved.append({
                "item_id": item_id,
                "requirement_id": item.get("requirement_id") or "",
                "label": item.get("label") or "",
                "candidate_page_count": item.get("candidate_page_count") or 0,
            })

    ordered = sorted(
        batches.values(),
        key=lambda batch: (
            str(batch.get("document") or ""),
            int(batch.get("page") or 0),
        ),
    )
    for batch in ordered:
        batch["item_count"] = len(batch.get("items") or [])
        batch["labels"] = list(dict.fromkeys(
            str(item.get("label") or "")
            for item in batch.get("items") or []
            if str(item.get("label") or "")
        ))

    return {
        "version": CACHE_VERSION,
        "page_batches": ordered,
        "page_batch_total": len(ordered),
        "unique_items_with_cached_page": len(unique_items),
        "unresolved_items": unresolved,
        "unresolved_item_total": len(unresolved),
        "principle": (
            "Один page-batch объединяет все элементы, проверяемые на одной сохранённой странице. "
            "Это будущая единица вызова vision-модели; verdict здесь не формируется."
        ),
    }
