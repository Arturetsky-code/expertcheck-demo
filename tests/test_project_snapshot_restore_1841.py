from __future__ import annotations

import gzip
import json

from core.project_snapshot import (
    corpus_fingerprint,
    load_project_snapshot,
    project_snapshot_bytes,
    snapshot_to_workspace_payload,
)


def _pages():
    return [
        {"document": "ПЗ.pdf", "page": 1, "text": "Объект. Площадь застройки 54,3 м2."},
        {"document": "ПЗУ.pdf", "page": 2, "text": "Объект. Площадь застройки 48,7 м2."},
    ]


def test_old_snapshot_restores_without_pdf_and_without_checkpoint():
    pages = _pages()
    snapshot_id = corpus_fingerprint(pages)
    old_payload = {
        "format": "ExpertCheck Project Verification Snapshot",
        "version": "18.0-rerunnable-contracted-evidence-corpus",
        "analysis_snapshot": {
            "snapshot_id": snapshot_id,
            "page_corpus": pages,
            "quality_gate_inputs": {"object_registry": [], "comparisons": []},
        },
        "core_version": "18.4-verification-runtime",
        "documents": [{"Файл": "ПЗ.pdf", "Тип документа": "ПЗ", "Страниц": 1}],
        "findings": [],
        "comparisons": [],
        "assignment_atomic_compliance": [{
            "requirement_id": "A-1",
            "semantic_evidence_packet": {"packet_id": "A-1", "evidence_level": "L4"},
        }],
        "automatic_checklist_review": {"results": [], "atomic_verification": {"atoms": []}},
        "universal_project_fact_graph": {},
    }
    raw = gzip.compress(json.dumps(old_payload, ensure_ascii=False).encode("utf-8"))
    loaded = load_project_snapshot(raw)
    restored = snapshot_to_workspace_payload(loaded, project_name="Тест 77")

    assert restored["project_name"] == "Тест 77"
    assert restored["snapshot_restore_info"]["source_pdf_required"] is False
    assert restored["snapshot_restore_info"]["ai_checkpoint_restored"] is False
    assert restored["semantic_execution_checkpoint"]["_project_fingerprint"] == snapshot_id
    docs, findings, comparisons = restored["result"]
    assert docs[0]["analysis_snapshot"]["snapshot_id"] == snapshot_id
    assert docs[0]["snapshot_restored"] is True
    assert findings == []
    assert comparisons == []


def test_new_snapshot_roundtrips_ai_checkpoint():
    pages = _pages()
    snapshot_id = corpus_fingerprint(pages)
    documents = [{
        "Файл": "ПЗ.pdf",
        "Тип документа": "ПЗ",
        "Страниц": 1,
        "core_version": "18.4.1-cumulative-verification-runtime",
        "analysis_snapshot": {
            "snapshot_id": snapshot_id,
            "page_corpus": pages,
            "quality_gate_inputs": {"object_registry": [], "comparisons": []},
        },
        "assignment_atomic_compliance": [{
            "requirement_id": "A-1",
            "semantic_evidence_packet": {"packet_id": "A-1", "evidence_level": "L4"},
        }],
        "automatic_checklist_review": {"results": [], "atomic_verification": {"atoms": []}},
        "universal_project_fact_graph": {},
    }]
    checkpoint = {
        "_project_fingerprint": snapshot_id,
        "assignment": {
            "judge": {
                "A-1": {
                    "packet_id": "A-1",
                    "verdict": "SUPPORTS",
                    "provider": "Groq",
                    "model": "openai/gpt-oss-120b",
                }
            },
            "critic": {},
        },
        "checklist": {"judge": {}, "critic": {}},
    }

    raw = project_snapshot_bytes(
        documents,
        [],
        [],
        semantic_checkpoint=checkpoint,
        workspace_state={"project_name": "Тест 77"},
    )
    loaded = load_project_snapshot(raw)
    restored = snapshot_to_workspace_payload(loaded)

    assert restored["project_name"] == "Тест 77"
    assert restored["snapshot_restore_info"]["ai_checkpoint_restored"] is True
    assert restored["semantic_execution_checkpoint"]["assignment"]["judge"]["A-1"]["verdict"] == "SUPPORTS"


def test_checkpoint_is_rejected_when_snapshot_fingerprint_differs():
    pages = _pages()
    snapshot_id = corpus_fingerprint(pages)
    payload = {
        "version": "18.4.1-portable-project-with-ai-checkpoint",
        "analysis_snapshot": {"snapshot_id": snapshot_id, "page_corpus": pages},
        "documents": [{"Файл": "ПЗ.pdf"}],
        "findings": [],
        "comparisons": [],
        "semantic_execution_checkpoint": {
            "_project_fingerprint": "OTHER-PROJECT",
            "assignment": {"judge": {"A-1": {"verdict": "SUPPORTS"}}},
        },
    }
    restored = snapshot_to_workspace_payload(payload, project_name="Контроль")
    assert restored["semantic_execution_checkpoint"] == {"_project_fingerprint": snapshot_id}
    assert restored["snapshot_restore_info"]["ai_checkpoint_restored"] is False
