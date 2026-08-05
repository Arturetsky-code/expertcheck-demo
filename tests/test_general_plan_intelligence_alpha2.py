from core.general_plan_reconciliation import (
    anchor_findings_to_general_plan,
    build_general_plan_document_checks,
    build_general_plan_field_checks,
)


def gp(position='4.13', name='Здание проборазделки', field=True):
    return {
        'document': 'ПЗУ2.pdf', 'document_type': 'ПЗУ2', 'page': 2,
        'parameter_code': 'OBJECT_CANDIDATE', 'object_hint': name,
        'value_text': name, 'genplan_position': position,
        'general_plan_explication': True, 'general_plan_field': field,
        'confidence': 0.99,
    }


def test_exact_position_anchors_property_to_gp_object():
    rows = [{
        'document': 'ПЗ.pdf', 'document_type': 'ПЗ', 'page': 45,
        'parameter_code': 'BUILDING_AREA', 'object_hint': 'Здание проборазделки',
        'genplan_position': '4.13', 'value': 89.9,
    }]
    audit = anchor_findings_to_general_plan(rows, [gp()])
    assert rows[0]['semantic_anchor_position'] == '4.13'
    assert rows[0]['semantic_anchor_name'] == 'Здание проборазделки'
    assert audit[0]['decision'] == 'привязано'


def test_ambiguous_similar_names_are_not_forced_to_gp_object():
    gps = [gp('1', 'Насосная станция №1'), gp('2', 'Насосная станция №2')]
    rows = [{'parameter_code': 'POWER_INSTALLED', 'object_hint': 'Насосная станция', 'document_type': 'ТХ'}]
    anchor_findings_to_general_plan(rows, gps)
    assert not rows[0].get('semantic_anchor_position')


def test_gp_object_missing_in_pz_creates_review_check():
    checks, coverage = build_general_plan_document_checks([gp()], [gp()])
    assert coverage[0]['missing_in_pz'] is True
    assert checks[0]['parameter_code'] == 'OBJECT_PRESENCE_PZ'


def test_explication_field_check_status():
    checks = build_general_plan_field_checks([gp(field=False)], [])
    assert checks[0]['status'] == 'ТРЕБУЕТ ПРОВЕРКИ'
