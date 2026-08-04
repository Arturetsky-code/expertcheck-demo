from legacy_analyzer import _extract_pz_object_registry


def test_inline_position_and_name_are_extracted():
    text = """Позиция по генплану
Наименование объекта
2.1 Карта кучного выщелачивания
РФ, Забайкальский край
08.04.003.099 Объекты обогащения
Производительность 1,6 млн. т/год
2.1.1 Насосная станция золотосодержащих растворов
РФ, Забайкальский край
08.04.099.099 Прочие объекты
Площадь застройки 167,7 м2
"""
    rows = _extract_pz_object_registry(1, text, "ПЗ.pdf", [])
    assert [row.genplan_position for row in rows] == ["2.1", "2.1.1"]
    assert rows[0].value_text == "Карта кучного выщелачивания"
    assert rows[1].value_text == "Насосная станция золотосодержащих растворов"


def test_explicit_quantity_is_extracted_but_tep_numbers_are_not():
    text = """Позиция по генплану
Наименование объекта
2.1.5 Противопожарные резервуары
Количество 3 шт. Объем каждого 70 м3
Нормальный
2.1.6 Пункт обогрева
Площадь застройки 18,5 м2
"""
    rows = _extract_pz_object_registry(1, text, "ПЗ.pdf", [])
    assert len(rows) == 2
    assert rows[0].value == 3.0
    assert rows[1].value == 1.0
