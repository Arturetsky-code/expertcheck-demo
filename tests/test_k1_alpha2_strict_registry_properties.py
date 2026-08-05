from core.register_reconciliation import reconcile_register
from core.universal_object_discovery import discover_object_candidates
from core.universal_registry_extractor import UniversalRegistryExtractor
from core.cross_section_consistency import build_cross_section_checks


def test_reconciliation_rejects_filename_even_if_object_candidate():
    findings=[{
        'parameter_code':'OBJECT_CANDIDATE','value_text':'Раздел ПД № 5_ТХ1.pdf',
        'object_hint':'Раздел ПД № 5_ТХ1.pdf','document':'Раздел ПД № 5_ТХ1.pdf',
        'document_type':'ТХ1','confidence':0.99,
    }]
    rows,audit=reconcile_register(findings)
    assert rows == []
    assert any(x.get('decision')=='rejected' for x in audit)


def test_unknown_oil_object_can_be_discovered_from_two_sections():
    findings=[
        {'parameter_code':'PRESSURE','object_hint':'Блок входных манифольдов БВМ-1','document_type':'ПЗ','document':'pz.pdf','page':3,'value':5.2,'confidence':0.9},
        {'parameter_code':'FLOW_RATE','object_hint':'Блок входных манифольдов БВМ-1','document_type':'ТХ1','document':'tx.pdf','page':7,'value':1000,'confidence':0.9},
    ]
    added,_=discover_object_candidates(findings)
    assert len(added)==1
    assert added[0]['object_hint']=='Блок входных манифольдов БВМ-1'


def test_pressure_is_compared_between_sections():
    findings=[
        {'parameter_code':'PRESSURE','parameter_name':'Давление','object_hint':'Газопровод Г-1','document_type':'ПЗ','document':'pz.pdf','page':1,'value':5.2,'unit':'МПа','confidence':0.9,'core2_confidence':0.9},
        {'parameter_code':'PRESSURE','parameter_name':'Давление','object_hint':'Газопровод Г-1','document_type':'ТХ1','document':'tx.pdf','page':2,'value':5.5,'unit':'МПа','confidence':0.9,'core2_confidence':0.9},
    ]
    rows=build_cross_section_checks(findings)
    assert rows and rows[0]['status']=='ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ'


def test_universal_registry_skips_document_register_page():
    assert UniversalRegistryExtractor._finding('x.pdf','ПЗ',1,'1.1','Установка подготовки нефти',0.9)['record_kind']=='project_object'
