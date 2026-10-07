from core20.normative_execution import NormativeExecutionEngine20
from core20.normative_foundation import default_foundation


TRIGGERED_IDS = {
    "FZ123-30-1-FIRE-RESISTANCE-TAXONOMY",
    "FZ123-31-1-CONSTRUCTIVE-FIRE-HAZARD-TAXONOMY",
    "FZ123-32-1-FUNCTIONAL-FIRE-HAZARD-TAXONOMY",
}


def _pb_document():
    return [{
        "Файл":"Раздел ПД №9_ПБ.pdf",
        "Тип документа":"ПБ",
        "project_understanding":{
            "objects":[{
                "object_id":"OBJ-FIRE",
                "properties":{
                    "fire_classification":[
                        {"document":"Раздел ПД №9_ПБ.pdf","page":18}
                    ]
                },
            }]
        },
    }]


def test_fz123_classification_atoms_are_dormant_without_project_triggers():
    engine=NormativeExecutionEngine20(default_foundation())
    pages=[{
        "document":"Раздел ПД №9_ПБ.pdf",
        "document_type":"ПБ",
        "page":18,
        "text":"Общие сведения по обеспечению пожарной безопасности объекта.",
    }]

    result=engine.run(_pb_document(),pages)

    active_ids={row["requirement_id"] for row in result["rows"]}
    inactive_ids={
        row["requirement_id"]
        for row in result["inactive_triggered_contract_rows"]
    }

    assert TRIGGERED_IDS.isdisjoint(active_ids)
    assert TRIGGERED_IDS <= inactive_ids


def test_fz123_classification_atoms_activate_only_for_present_characteristics():
    engine=NormativeExecutionEngine20(default_foundation())
    pages=[{
        "document":"Раздел ПД №9_ПБ.pdf",
        "document_type":"ПБ",
        "page":18,
        "text":(
            "Степень огнестойкости здания: II. "
            "Класс конструктивной пожарной опасности: С0. "
            "Класс функциональной пожарной опасности: Ф5.1. "
            "Назначение объекта: производственное здание."
        ),
    }]

    result=engine.run(_pb_document(),pages)
    rows={
        row["requirement_id"]:row
        for row in result["rows"]
        if row["requirement_id"] in TRIGGERED_IDS
    }

    assert set(rows)==TRIGGERED_IDS
    assert all(row.get("activation_state")=="ACTIVE" for row in rows.values())
    assert all(
        row.get("activation_reason_code")=="PROJECT_TRIGGER_PROVEN"
        for row in rows.values()
    )
    assert all(row["kind"]=="REVIEW_QUESTION" for row in rows.values())
    assert all(
        row["proof_state"]=="SEMANTIC_PROOF_REQUIRED"
        for row in rows.values()
    )
    assert all(
        row["reason_code"]=="NORMATIVE_SEMANTIC_PROOF_REQUIRED"
        for row in rows.values()
    )

    queue_ids={
        packet["requirement_id"]
        for packet in result["semantic_queue"]
    }
    assert TRIGGERED_IDS <= queue_ids
    assert result["project_findings"]==0


def test_fz123_functional_class_atom_does_not_activate_from_unrelated_fire_text():
    engine=NormativeExecutionEngine20(default_foundation())
    pages=[{
        "document":"Раздел ПД №9_ПБ.pdf",
        "document_type":"ПБ",
        "page":18,
        "text":(
            "Производственное здание оборудовано системой пожарной сигнализации. "
            "Категория помещения по взрывопожарной и пожарной опасности: В1."
        ),
    }]

    result=engine.run(_pb_document(),pages)

    active_ids={row["requirement_id"] for row in result["rows"]}
    assert "FZ123-32-1-FUNCTIONAL-FIRE-HAZARD-TAXONOMY" not in active_ids
