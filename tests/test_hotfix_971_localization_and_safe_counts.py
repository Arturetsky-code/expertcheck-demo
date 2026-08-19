from core.finding_qualification import qualify_comparison
from core.display_localization import parameter_label, status_label, localize_parameter_list


def test_decimal_string_counts_do_not_crash_and_confirm_issue():
    row = {
        'status': 'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ',
        'independent_trusted_sources': '2.0',
        'independent_section_count': '2,0',
        'sources': 'ПЗ, стр. 45 | ПЗУ, стр. 18',
    }
    result = qualify_comparison(row)
    assert result['finding_class'] == 'CONFIRMED_ISSUE'


def test_bad_counts_degrade_safely_to_review():
    row = {
        'status': 'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ',
        'independent_trusted_sources': 'not-a-number',
        'independent_section_count': None,
        'sources': 'ПЗ, стр. 45',
    }
    result = qualify_comparison(row)
    assert result['finding_class'] == 'REVIEW'


def test_parameter_codes_are_localized():
    assert parameter_label('AREA_BUILD') == 'Площадь застройки'
    assert parameter_label('QUANTITY') == 'Количество'
    assert localize_parameter_list(['AREA_BUILD', 'QUANTITY']) == ['Площадь застройки', 'Количество']


def test_internal_statuses_are_localized():
    assert status_label('CONFIRMED_ISSUE') == 'Выявлено несоответствие'
    assert status_label('HOLD') == 'Требует проверки'
