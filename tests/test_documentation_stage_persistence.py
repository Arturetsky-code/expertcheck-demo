from __future__ import annotations

from core.workspace_store import session_snapshot, snapshot_signature


def test_documentation_stage_is_persisted_in_workspace_snapshot():
    payload = session_snapshot({
        "project_name": "Тест ПД",
        "documentation_stage": "ПД",
        "result": None,
    })

    assert payload["documentation_stage"] == "ПД"


def test_documentation_stage_changes_workspace_signature():
    pd_payload = session_snapshot({
        "project_name": "Тест",
        "documentation_stage": "ПД",
        "result": None,
    })
    rd_payload = session_snapshot({
        "project_name": "Тест",
        "documentation_stage": "РД",
        "result": None,
    })

    assert snapshot_signature(pd_payload) != snapshot_signature(rd_payload)
