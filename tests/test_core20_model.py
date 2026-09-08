from __future__ import annotations

from core20.baseline import evaluate_baseline
from core20.model import CanonicalProject, Evidence, Finding, ProjectObject, PropertyValue, stable_id


def test_stable_id_is_deterministic_and_normalized():
    assert stable_id('OBJ','Компрессорная','4.5') == stable_id('OBJ','  компрессорная  ','4.5')


def test_canonical_project_detects_broken_references():
    project=CanonicalProject(project_id='PRJ-1',name='Тест')
    project.add_property(PropertyValue(
        property_id='PROP-1',object_id='OBJ-MISSING',parameter_code='AREA_BUILD',
        parameter_name='Площадь застройки',value=54.3,unit='м2',
    ))
    issues=project.validate()
    assert any(item.code=="PROPERTY_OBJECT_MISSING" for item in issues)


def test_baseline_gate_accepts_equal_or_better_metrics():
    observed={
        'objects_confirmed':36,'passport_characteristics':140,'cross_section_comparisons':99,
        'cross_section_l5':50,'project_findings':1,'specialist_questions':300,
        'review_packages':20,'verified_checks':60,'system_limitations':250,
    }
    result=evaluate_baseline(observed)
    assert result['passed'] is True


def test_baseline_gate_rejects_lost_project_finding():
    observed={
        'objects_confirmed':36,'passport_characteristics':137,'cross_section_comparisons':99,
        'cross_section_l5':45,'project_findings':0,'specialist_questions':346,
        'review_packages':26,'verified_checks':49,'system_limitations':319,
    }
    result=evaluate_baseline(observed)
    assert result['passed'] is False
    assert 'project_findings' in result['failed']
