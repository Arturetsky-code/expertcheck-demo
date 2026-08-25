from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import workspace_store


class _DoNotSerialize:
    def __str__(self):
        raise AssertionError("the evidence payload must not be serialized for a rerun signature")


def _state():
    return {
        "project_name": "Test",
        "analysis_time": "2026-08-24T16:10",
        "result": [[{
            "core_version": "11.1.1",
            "report_quality_gate": {"status": "PASSED"},
            "evidence_graph": {"large": _DoNotSerialize()},
        }], [{"finding": _DoNotSerialize()}], []],
        "object_registry_confirmed": False,
        "object_assembly_rows": [{
            "Ключ": "1|pump",
            "Включить": True,
            "Решение пользователя": "Подтверждённый объект",
            "Комментарий пользователя": "",
            "_evidence": [_DoNotSerialize()],
        }],
        "completeness_user_confirmed": False,
        "completeness_decisions": {},
        "checklist_run": None,
        "checklist_user_results": {},
        "risk_user_decisions": {},
        "object_learning_examples": [],
    }


def test_snapshot_signature_does_not_walk_evidence_payload():
    state = _state()
    first = workspace_store.snapshot_signature(state)
    state["object_registry_confirmed"] = True
    second = workspace_store.snapshot_signature(state)
    assert first != second
    state["checklist_run"] = {"results": []}
    third = workspace_store.snapshot_signature(state)
    assert second != third


def test_session_snapshot_does_not_pre_serialize_result():
    def forbidden(*args, **kwargs):
        raise AssertionError("session_snapshot must not serialize the full result")

    with patch.object(workspace_store.json, "dumps", forbidden):
        snapshot = workspace_store.session_snapshot(_state())
    assert snapshot["result"][0][0]["core_version"] == "11.1.1"


def test_streaming_workspace_codec_roundtrip_without_json_dumps():
    payload = {"text": "доказательство" * 1000, "rows": [{"id": index} for index in range(50)]}

    def forbidden(*args, **kwargs):
        raise AssertionError("streaming codec must not allocate json.dumps output")

    with patch.object(workspace_store.json, "dumps", forbidden):
        encoded = workspace_store._json_bytes(payload)
    assert workspace_store._from_json_bytes(encoded) == payload


def test_only_first_document_keeps_run_level_evidence_after_pipeline_source_change():
    source = (ROOT / "core" / "pipeline.py").read_text(encoding="utf-8")
    assert "for doc_index, doc in enumerate(documents):" in source
    assert "if doc_index:\n            continue" in source


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
