from core.object_register_engine import build_registry
from core.object_semantics import classify_object, parameter_applicability
from core.cross_section_consistency import build_cross_section_checks


def f(name, code='OBJECT_CANDIDATE', doc='ПЗ', position='', **extra):
    row = {
        'document':'test.pdf','document_type':doc,'page':1,'parameter_code':code,
        'parameter_name':'Кандидат','value_text':name,'object_hint':name,
        'genplan_position':position,'confidence':0.9,'context':'','structural_zone':'','match_method':'',
    }
    row.update(extra)
    return row


def test_document_register_rows_never_become_objects():
    findings = [
        f('Архитектурные решения', context='Состав проектной документации'),
        f('Система электроснабжения', context='Перечень разделов проектной документации'),
        f('Проект организации строительства', context='Ведомость документов'),
    ]
    records, audit = build_registry(findings)
    assert records == []
    assert all(x['decision'] == 'отклонено' for x in audit)


def test_unpositioned_single_weak_candidate_not_in_register():
    records, audit = build_registry([f('Неизвестное наименование')])
    assert records == []
    assert audit[0]['decision'] == 'отклонено'


def test_unpositioned_candidate_confirmed_by_two_sections_is_in_register():
    findings = [
        f('Насосная станция ППВ', doc='АР1'),
        f('Насосная станция ППВ', doc='ТХ1'),
    ]
    records, _ = build_registry(findings)
    assert len(records) == 1
    assert records[0]['Наименование объекта'] == 'Насосная станция ППВ'


def test_official_pz_position_is_in_register():
    records, _ = build_registry([f('Насосная станция ППВ', code='OBJECT_ENTRY', position='4.18')])
    assert len(records) == 1
    assert records[0]['Позиция по ГП'] == '4.18'


def test_characteristics_beyond_area_are_compared():
    findings = []
    for code, value, unit, doc in [
        ('CAPACITY', 120, 'м³/ч', 'ПЗ'), ('CAPACITY', 120, 'м³/ч', 'ТХ1'),
        ('POWER_INST', 45, 'кВт', 'ТХ1'), ('POWER_INST', 47, 'кВт', 'ИОС1'),
        ('HEIGHT_BUILD', 6.2, 'м', 'ПЗ'), ('HEIGHT_BUILD', 6.2, 'м', 'АР1'),
        ('FLOORS', 1, 'эт.', 'ПЗ'), ('FLOORS', 1, 'эт.', 'АР1'),
    ]:
        findings.append({
            'document':f'{doc}.pdf','document_type':doc,'page':1,'parameter_code':code,
            'parameter_name':code,'value':value,'unit':unit,'object_hint':'Насосная станция ППВ',
            'semantic_anchor_name':'Насосная станция ППВ','genplan_position':'4.18','confidence':0.95,
        })
    checks = build_cross_section_checks(findings)
    by_code = {x['parameter_code']:x for x in checks}
    assert by_code['CAPACITY']['status'] == 'СОВПАДАЕТ'
    assert by_code['POWER_INSTALLED']['status'] == 'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ'
    assert by_code['HEIGHT_BUILD']['status'] == 'СОВПАДАЕТ'
    assert by_code['FLOORS']['status'] == 'СОВПАДАЕТ'


def test_floor_not_applicable_to_reservoir():
    assert classify_object('Противопожарный резервуар').code == 'RESERVOIR'
    assert parameter_applicability('RESERVOIR', 'FLOORS') == 'not_applicable'
