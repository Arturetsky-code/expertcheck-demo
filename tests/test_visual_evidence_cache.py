import base64

import fitz

from core.visual_evidence_cache import (
    build_visual_evidence_cache,
    build_visual_page_batches,
    visual_page_requests,
)


class Upload:
    name = "АР.pdf"

    def __init__(self, data: bytes):
        self._data = data

    def getvalue(self):
        return self._data


def _pdf_bytes():
    doc = fitz.open()
    page = doc.new_page(width=420, height=297)
    page.insert_text((40, 60), "PLAN TEST", fontsize=18)
    data = doc.tobytes()
    doc.close()
    return data


def test_visual_page_requests_deduplicate_and_group_elements():
    items = [
        {
            "item_id": "I-1",
            "requirement_id": "R-1",
            "label": "Границы",
            "visual_kind": "PZU_SITE_LAYOUT",
            "selection_source": "GENERAL_PLAN_ENGINE",
            "candidate_pages": [{"document": "ПЗУ.pdf", "page": 4, "section": "ПЗУ"}],
        },
        {
            "item_id": "I-2",
            "requirement_id": "R-1",
            "label": "Коммуникации",
            "visual_kind": "PZU_SITE_LAYOUT",
            "selection_source": "GENERAL_PLAN_ENGINE",
            "candidate_pages": [{"document": "ПЗУ.pdf", "page": 4, "section": "ПЗУ"}],
        },
    ]
    requests = visual_page_requests(items)
    assert len(requests) == 1
    assert requests[0]["item_ids"] == ["I-1", "I-2"]
    assert requests[0]["labels"] == ["Границы", "Коммуникации"]


def test_visual_cache_renders_only_requested_page_and_is_resumable():
    items = [{
        "item_id": "I-1",
        "requirement_id": "R-1",
        "label": "Фасад",
        "visual_kind": "AR_FACADES",
        "selection_source": "DRAWING_INTELLIGENCE_V2",
        "candidate_pages": [{"document": "АР.pdf", "page": 1, "section": "АР"}],
    }]
    cache = build_visual_evidence_cache([Upload(_pdf_bytes())], items, max_pages=4)
    assert cache["cached_pages"] == 1
    assert cache["omitted_pages"] == 0
    assert cache["persisted_for_resume"] is True
    entry = cache["entries"][0]
    assert entry["document"] == "АР.pdf"
    assert entry["page"] == 1
    assert entry["image_bytes"] > 0
    assert base64.b64decode(entry["image_base64"])
    assert entry["image_sha256"]


def test_visual_page_batches_merge_two_items_on_one_cached_page():
    items = [
        {
            "item_id": "I-1",
            "requirement_id": "R-1",
            "label": "Границы",
            "candidate_pages": [{"document": "ПЗУ.pdf", "page": 4}],
        },
        {
            "item_id": "I-2",
            "requirement_id": "R-1",
            "label": "Коммуникации",
            "candidate_pages": [{"document": "ПЗУ.pdf", "page": 4}],
        },
    ]
    cache = {
        "entries": [{
            "cache_id": "VIS-1",
            "document": "ПЗУ.pdf",
            "page": 4,
            "mime_type": "image/jpeg",
            "image_sha256": "abc",
            "image_bytes": 100,
        }]
    }
    plan = build_visual_page_batches(items, cache)
    assert plan["page_batch_total"] == 1
    assert plan["unique_items_with_cached_page"] == 2
    assert plan["unresolved_item_total"] == 0
    assert plan["page_batches"][0]["item_count"] == 2
    assert plan["page_batches"][0]["labels"] == ["Границы", "Коммуникации"]


def test_visual_page_batches_fail_closed_without_cached_page():
    items = [{
        "item_id": "I-1",
        "requirement_id": "R-1",
        "label": "Разрез",
        "candidate_pages": [{"document": "АР.pdf", "page": 8}],
    }]
    plan = build_visual_page_batches(items, {"entries": []})
    assert plan["page_batch_total"] == 0
    assert plan["unique_items_with_cached_page"] == 0
    assert plan["unresolved_item_total"] == 1
