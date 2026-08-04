from core.object_register_engine import build_registry, parent_position


def f(position, name, doc="ПЗ", code="OBJECT_ENTRY", page=1, qty=1):
    return {
        "parameter_code": code,
        "genplan_position": position,
        "value_text": name,
        "object_hint": name,
        "document_type": doc,
        "document": f"{doc}.pdf",
        "page": page,
        "value": qty,
        "confidence": 0.99,
    }


def test_hierarchical_positions_are_separate():
    records, _ = build_registry([
        f("2.1", "Карта кучного выщелачивания"),
        f("2.1.1", "Насосная станция золотосодержащих растворов"),
        f("2.1.2", "Насосная станция выщелачивающих растворов"),
    ])
    assert [r["Позиция по ГП"] for r in records] == ["2.1", "2.1.1", "2.1.2"]
    assert records[1]["Родительская позиция"] == "2.1"


def test_unpositioned_alias_merges_into_position():
    records, audit = build_registry([
        f("2.1.1", "Насосная станция золотосодержащих растворов"),
        f("", "Насосная станция золотосодержащих растворов", doc="АР1", code="OBJECT_CANDIDATE"),
    ])
    assert len(records) == 1
    assert records[0]["Подтверждений"] == 2
    assert "Позиция +" in records[0]["Способ объединения"]
    assert any(row["matched_position"] == "2.1.1" for row in audit)


def test_different_pump_stations_do_not_merge():
    records, _ = build_registry([
        f("2.1.1", "Насосная станция золотосодержащих растворов"),
        f("2.1.2", "Насосная станция выщелачивающих растворов"),
    ])
    assert len(records) == 2


def test_quantity_preserved():
    records, _ = build_registry([f("2.1.5", "Противопожарные резервуары", qty=3)])
    assert records[0]["Количество"] == 3


def test_parent_position():
    assert parent_position("2.1.1") == "2.1"
    assert parent_position("2.1") == ""
