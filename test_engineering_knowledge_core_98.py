from core.fact_admission import assess_fact_admission
from core.applicability_matrix import expected_sections, section_expectations
from core.typed_check_engine import execute_typed_check
from core.assignment_compliance import _atomic_fragments
from core.finding_qualification import qualify_checklist


def test_fact_admission_does_not_let_confidence_replace_owner_binding():
    f={
        'object_hint':'Здание проборазделки','parameter_code':'AREA_BUILD','parameter_name':'Площадь застройки',
        'value':89.9,'unit':'м2','document':'ПЗ','page':45,'confidence':.99,
        # no row/position/source passport
    }
    r=assess_fact_admission(f)
    assert r['fact_admission_decision']=='HOLD'
    assert r['fact_who_score'] < 40


def test_fact_admission_accepts_traceable_row_fact():
    f={
        'object_hint':'Здание проборазделки','parameter_code':'AREA_BUILD','parameter_name':'Площадь застройки',
        'value':89.9,'unit':'м2','document':'ПЗ','page':45,'confidence':.91,
        'binding_status':'ROW_LOCKED','row_integrity_status':'CONFIRMED_ROW','evidence_id':'EV-1',
        'scope_binding_decision':'ALLOW'
    }
    r=assess_fact_admission(f)
    assert r['fact_admission_decision']=='ADMIT'


def test_applicability_does_not_require_every_possible_section():
    matrix=section_expectations('BUILDING','AREA_TOTAL')
    assert matrix['АР'] in {'required','expected'}
    assert 'КР' not in expected_sections('BUILDING','AREA_TOTAL')


def test_typed_presence_absence_is_not_negative_finding():
    compiled={'typed_check':'DRAWING_PRESENCE_CHECK','evidence_terms':['план','экспликация']}
    r=execute_typed_check(compiled,[],[])
    assert r['status']=='Не проверено системой'
    q=qualify_checklist({'status':r['status'],'evidence':r['evidence']})
    assert q['risk_eligible'] is False


def test_assignment_parser_splits_numbered_rows_into_atoms():
    text='15. Режим работы. Продолжительность смены 12 часов\n16. Предусмотреть резервуар объемом 70 м3; обеспечить подъезд.'
    atoms=_atomic_fragments(text)
    assert any(x['row_no']=='15' for x in atoms)
    assert any(x['row_no']=='16' and 'резервуар' in x['text'].lower() for x in atoms)
    assert all(len(x['text']) < 180 for x in atoms)

from core.quality_benchmark import benchmark_summary

def test_quality_benchmark_metrics_are_explicit():
    s=benchmark_summary([
        {'quality_label':'TP'},{'quality_label':'TP'},{'quality_label':'FP'},
        {'quality_label':'FN'},{'quality_label':'ABSTAIN_OK'}
    ])
    assert s['precision_pct']==66.7
    assert s['recall_pct']==66.7
    assert s['correct_abstention']==1
