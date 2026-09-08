from __future__ import annotations

from core.project_knowledge_recovery import recover_project_knowledge
from core.project_snapshot import snapshot_to_workspace_payload


def _registry():
    return [{
        "Позиция по ГП": "4.10",
        "Наименование объекта": "Компрессорная",
        "Количество": 1,
        "Статус": "Подтверждено ПЗ и генпланом",
        "Источники": "ПЗ, ПЗУ",
    }]


def _findings():
    return [{
        "parameter_code": "AREA_BUILD",
        "parameter_name": "Площадь застройки",
        "object_hint": "Компрессорная",
        "genplan_position": "4.10",
        "value": 54.3,
        "value_text": "54,3",
        "unit": "м2",
        "document": "ПЗ.pdf",
        "document_type": "ПЗ",
        "page": 12,
        "binding_status": "ROW_LOCKED",
        "row_integrity_status": "CONFIRMED",
    }]


def _comparisons():
    return [{
        "check_id": "CORE-XSEC-COMP-AREA",
        "object": "Компрессорная",
        "parameter_code": "AREA_BUILD",
        "parameter": "Площадь застройки",
        "status": "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ",
        "values_by_section": {"ПЗ": ["54,3 м2"], "ПЗУ": ["48,7 м2"]},
        "verification_evidence": [
            {"document": "ПЗ.pdf", "page": 12, "section": "ПЗ", "value": 54.3},
            {"document": "ПЗУ.pdf", "page": 5, "section": "ПЗУ", "value": 48.7},
        ],
    }]


def test_old_snapshot_quality_gate_inputs_restore_registry_passports_and_cross_section():
    documents = [{
        "Файл": "ПЗ.pdf",
        "snapshot_restored": True,
        "analysis_snapshot": {
            "snapshot_id": "SNAP-186",
            "quality_gate_inputs": {
                "object_registry": _registry(),
                "comparisons": _comparisons(),
            },
        },
    }]
    findings = _findings()
    comparisons = []
    summary = recover_project_knowledge(documents, findings, comparisons)

    assert summary["objects"] == 1
    assert summary["passports"] == 1
    assert summary["cross_section_checks"] == 1
    assert comparisons[0]["check_id"] == "CORE-XSEC-COMP-AREA"
    assert documents[0]["consolidated_registry"][0]["Наименование объекта"] == "Компрессорная"
    assert documents[0]["object_passports"][0]["name"] == "Компрессорная"
    assert documents[0]["project_understanding"]["objects"][0]["name"] == "Компрессорная"
    assert documents[0]["project_knowledge_model"]["summary"]["source_pdf_required"] is False


def test_snapshot_workspace_restore_lifts_embedded_project_knowledge_without_pdf():
    payload = {
        "version": "18.4.1-portable-project-with-ai-checkpoint",
        "analysis_snapshot": {
            "snapshot_id": "SNAP-186",
            "page_corpus": [{"document": "ПЗ.pdf", "page": 1, "text": "контроль"}],
            "quality_gate_inputs": {
                "object_registry": _registry(),
                "comparisons": _comparisons(),
            },
        },
        "documents": [{"Файл": "ПЗ.pdf"}],
        "findings": _findings(),
        "comparisons": [],
        "workspace_state": {"project_name": "Тест 77"},
    }
    # snapshot_to_workspace_payload expects a fingerprint-consistent payload only
    # after load_project_snapshot; direct unit use is valid for project model recovery.
    restored = snapshot_to_workspace_payload(payload, project_name="Тест 77")
    docs, findings, comparisons = restored['result']
    assert docs[0]["snapshot_restored"] is True
    assert len(docs[0]["consolidated_registry"]) == 1
    assert len(docs[0]["object_passports"]) == 1
    assert len(comparisons) == 1
    assert restored["snapshot_restore_info"]["project_knowledge_recovered"] is True
    assert restored["snapshot_restore_info"]["objects_recovered"] == 1
    assert restored["snapshot_restore_info"]["cross_section_checks_recovered"] == 1
    assert restored["object_registry_confirmed"] is False


def test_recovery_does_not_auto_confirm_user_object_decisions():
    documents = [{
        "snapshot_restored": True,
        "analysis_snapshot": {"quality_gate_inputs": {"object_registry": _registry(), "comparisons": []}},
    }]
    recover_project_knowledge(documents, _findings(), [])
    assert "object_registry_confirmed" not in documents[0]
