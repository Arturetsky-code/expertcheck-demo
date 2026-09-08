from __future__ import annotations

from core.project_assembly import object_key, selected_keys, filter_registry_by_keys
from core.report_engine import build_structured_report
from core.learning_engine import object_learning_examples, apply_learning_examples


def _registry_rows():
    rows=[]
    for i in range(1,40):
        rows.append({
            "Позиция по ГП": str(i),
            "Наименование объекта": f"Объект {i}",
            "Источники": "ПЗУ",
        })
    return rows


def test_confirmed_scope_uses_36_of_39_candidates():
    registry=_registry_rows()
    assembly=[]
    excluded={4,12,27}
    for idx,row in enumerate(registry,1):
        assembly.append({
            "Ключ": object_key(row),
            "Включить": idx not in excluded,
            "Позиция по ГП": row["Позиция по ГП"],
            "Наименование объекта": row["Наименование объекта"],
            "Решение пользователя": ("Составная часть / не отдельный объект" if idx in excluded else "Подтверждённый объект"),
        })
    allowed=selected_keys(assembly)
    filtered=filter_registry_by_keys(registry,allowed)
    assert len(registry)==39
    assert len(filtered)==36


def test_management_report_counts_ui_confirmed_objects_not_all_candidates():
    registry=_registry_rows()[:4]
    docs=[{
        "consolidated_registry": registry,
        "project_understanding": {"objects": []},
    }]
    assembly=[]
    for idx,row in enumerate(registry,1):
        assembly.append({
            "Ключ": object_key(row),
            "Включить": idx != 2,
            "Позиция по ГП": row["Позиция по ГП"],
            "Наименование объекта": row["Наименование объекта"],
            "Решение Object Intelligence": "trusted",
        })
    report=build_structured_report('Тест',docs,[],assembly_rows=assembly)
    assert report["summary"]["objects_confirmed"] == 3
    assert len(report["excluded_objects"]) == 1


def test_non_standalone_decision_becomes_learning_example_and_needs_repetition():
    rows=[{
        "Наименование объекта": "Технологический комплекс",
        "Позиция по ГП": "4.2",
        "Включить": False,
        "Решение пользователя": "Составная часть / не отдельный объект",
    }]
    examples=object_learning_examples(rows)
    assert examples[0]["included"] is False
    assert "Составная часть" in examples[0]["reason"]
    findings=[{
        "parameter_code": "OBJECT_ENTRY",
        "value_text": "Технологический комплекс",
    }]
    assert apply_learning_examples(findings,examples)==0
    assert apply_learning_examples(findings,examples+examples)==1
    assert findings[0]["learning_rule_blocked"] is True
