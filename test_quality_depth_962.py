from pathlib import Path
from core.evidence_provenance import annotate_evidence_provenance
from core.cross_section_consistency import build_cross_section_checks
from core.normative_intelligence import NormativeIntelligence

ROOT=Path(__file__).parent/'knowledge'

def _fact(doc, section, value, evidence_id, page=10, row=3):
    return {
        'document':doc,'document_type':section,'section':section,'page':page,
        'table_index':1,'row_index':row,'object_hint':'Здание проборазделки',
        'parameter_code':'AREA_BUILD','parameter_name':'Площадь застройки','value':value,'unit':'м²',
        'confidence':0.96,'core2_confidence':0.96,'binding_status':'ROW_LOCKED','row_integrity_status':'CONFIRMED_ROW',
        'match_method':'строка таблицы ТЭП','evidence_id':evidence_id,
    }

def test_provenance_contains_source_locator():
    rows=[_fact('ПЗ.pdf','ПЗ',89.9,'a')]
    annotate_evidence_provenance(rows)
    assert rows[0]['source_fingerprint'].startswith('SRC-')
    assert rows[0]['physical_trace_level']=='ROW_TRACE'

def test_duplicate_extractors_same_row_do_not_count_as_two_independent_sources():
    a=_fact('ПЗ.pdf','ПЗ',23.5,'a')
    b=_fact('ПЗ.pdf','ПЗ',23.5,'b') # same physical row, duplicate extraction
    c=_fact('ПЗУ.pdf','ПЗУ',89.9,'c',page=18,row=13)
    rows=[a,b,c]
    annotate_evidence_provenance(rows)
    checks=build_cross_section_checks(rows)
    row=next(x for x in checks if x['parameter_code']=='AREA_BUILD')
    assert row['independent_trusted_sources']==2
    assert set(row['trusted_section_families'])=={'ПЗ','ПЗУ'}

def test_normative_requirements_have_quality_contract():
    e=NormativeIntelligence(ROOT)
    rows=e.search(question='состав проектной документации',section='ПЗ',limit=20)
    assert rows
    pp=next(x for x in rows if x.get('document_id')=='PP87')
    assert 'normative_quality' in pp
    assert pp['categorical_conclusion_allowed'] is False
    assert pp['normative_quality']['verified_document'] is True
    assert pp['normative_quality']['verified_clause'] is False
