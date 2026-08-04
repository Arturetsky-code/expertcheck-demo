from legacy_analyzer import _extract_pz_object_registry


def test_hierarchical_positions_are_separate_and_classifier_is_ignored():
    text = """Позиция по генплану\nНаименование объекта\n1\n2.1\nКарта кучного выщелачивания\n08.04.003.099\nПрочие объекты\n2\n2.1.1\nНасосная станция золотосодержащих растворов\n08.04.099.099\nПрочие объекты\n3\n2.1.2\nНасосная станция выщелачивающих растворов\n08.04.099.099\nПрочие объекты\n"""
    findings = _extract_pz_object_registry(1, text, "ПЗ.pdf", [])
    positions = [item.genplan_position for item in findings]
    assert positions == ["2.1", "2.1.1", "2.1.2"]
    assert "08.04.099.099" not in positions


def test_quantity_is_extracted_from_registry_row():
    text = """Позиция по генплану\nНаименование объекта\n2.1.5\nПротивопожарные резервуары\nКоличество 3 шт. Объем каждого 70 м3\nНормальный\n2.1.6\nПункт обогрева\nПлощадь 18,7 м2\n"""
    findings = _extract_pz_object_registry(1, text, "ПЗ.pdf", [])
    row = next(item for item in findings if item.genplan_position == "2.1.5")
    assert row.value == 3.0
