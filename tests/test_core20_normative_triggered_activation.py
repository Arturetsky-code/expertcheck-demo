from pathlib import Path

from core20.normative_execution import NormativeExecutionEngine20
from core20.normative_foundation import NormativeKnowledgeFoundation20


ROOT = Path(__file__).resolve().parents[1] / "knowledge"


def _engine():
    return NormativeExecutionEngine20(NormativeKnowledgeFoundation20(ROOT))


def test_gost_change_contracts_are_registered_but_dormant_without_change_evidence():
    documents = [{"Файл": "Раздел ПД №1_ПЗ.pdf", "Тип документа": "ПЗ"}]
    pages = [{
        "document": "Раздел ПД №1_ПЗ.pdf",
        "document_type": "ПЗ",
        "page": 3,
        "text": "Пояснительная записка. Общие сведения о проектируемом объекте.",
    }]

    result = _engine().run(documents, pages)
    ids = {row["requirement_id"] for row in result["rows"]}

    assert "GOST21101-2026-7.3.1-CHANGE-NUMBER" not in ids
    assert "GOST21101-2026-7.4.1-PD-INDEPENDENT-CHANGES" not in ids
    assert result["registered_contracts"] >= result["active_contracts"] + 2
    assert result["inactive_triggered_contracts"] >= 2
    inactive = {
        row["requirement_id"]: row
        for row in result["inactive_triggered_contract_rows"]
    }
    assert inactive["GOST21101-2026-7.3.1-CHANGE-NUMBER"]["activation_reason_code"] == "PROJECT_TRIGGER_NOT_FOUND"
    assert inactive["GOST21101-2026-7.4.1-PD-INDEPENDENT-CHANGES"]["activation_reason_code"] == "PROJECT_TRIGGER_NOT_FOUND"


def test_gost_change_contract_activates_when_numbered_change_is_addressable():
    documents = [{"Файл": "Раздел ПД №1_ПЗ.pdf", "Тип документа": "ПЗ"}]
    pages = [{
        "document": "Раздел ПД №1_ПЗ.pdf",
        "document_type": "ПЗ",
        "page": 2,
        "text": (
            "Таблица регистрации изменений. Изм. 1. "
            "Номер изменения указан для настоящего документа."
        ),
    }]

    result = _engine().run(documents, pages)
    row = next(
        item for item in result["rows"]
        if item["requirement_id"] == "GOST21101-2026-7.3.1-CHANGE-NUMBER"
    )

    assert row["activation_state"] == "ACTIVE"
    assert row["activation_reason_code"] == "PROJECT_TRIGGER_PROVEN"
    assert row["activation_trace"]
    assert row["activation_trace"][0]["document"] == "Раздел ПД №1_ПЗ.pdf"
    assert row["activation_trace"][0]["page"] == 2
    assert row["kind"] != "PROJECT_FINDING"


def test_existing_conditional_contract_still_fails_closed_when_applicability_not_proven():
    documents = [{"Файл": "Раздел ПД №4_КР1.pdf", "Тип документа": "КР"}]
    pages = [{
        "document": "Раздел ПД №4_КР1.pdf",
        "document_type": "КР",
        "page": 40,
        "text": "В гидравлическом расчёте приведены радиусы 50 м и 100 м.",
    }]

    result = _engine().run(documents, pages)
    row = next(
        item for item in result["rows"]
        if item["requirement_id"] == "FNP505-1215-CONVEYOR-CROSSING-SPACING"
    )

    assert row["kind"] == "REVIEW_QUESTION"
    assert row["reason_code"] == "NORMATIVE_APPLICABILITY_NOT_PROVEN"
