from pathlib import Path
import legacy_analyzer as la


def test_continued_pz_table_binds_tep_to_same_position_block():
    params = la.load_json(Path(__file__).parent / 'parameters.json')
    objects = la.load_json(Path(__file__).parent / 'objects.json')
    text = '''
4.12
Модуль обеспыливания
Площадь застройки 23,5 м2
Общая площадь 12,7 м2
Строительный объем 52,0 м3
4.13
Здание проборазделки
Площадь застройки 89,9 м2
Общая площадь 74,7 м2
Строительный объем 433,0 м3
'''
    rows = la._extract_pz_complex_table(45, text, 'ПЗ.pdf', params, objects)
    values = {(r.object_hint, r.parameter_code): r.value for r in rows}
    assert values[('Модуль обеспыливания', 'AREA_BUILD')] == 23.5
    assert values[('Здание проборазделки', 'AREA_BUILD')] == 89.9
    assert ('Здание проборазделки', 'AREA_BUILD') in values
    assert values[('Здание проборазделки', 'AREA_BUILD')] != 23.5
