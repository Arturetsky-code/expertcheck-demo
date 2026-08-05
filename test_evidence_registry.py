from core.evidence_registry import build_evidence_index, evidence_for_row, is_forbidden_evidence
from core.project_assembly import build_assembly_rows


def test_file_name_is_forbidden_source():
    item={'value_text':'Раздел ПД № 3_АР2.pdf','structural_zone':'Состав проектной документации'}
    blocked,reason=is_forbidden_evidence(item)
    assert blocked
    assert reason


def test_object_has_page_and_section_evidence():
    findings=[{
        'parameter_code':'OBJECT_ENTRY','value_text':'Здание проборазделки','genplan_position':'4.13',
        'document_type':'ПЗ','document':'Раздел ПД №1_ПЗ.pdf','page':45,
        'trusted_zone':'OBJECT_REGISTER','structural_zone':'Состав сложного объекта',
        'object_trust_score':100,'object_lifecycle_status':'Проектируемый'
    }]
    index=build_evidence_index(findings)
    records=evidence_for_row({'Позиция по ГП':'4.13','Наименование объекта':'Здание проборазделки'},index)
    assert records[0]['page']==45
    assert records[0]['section']=='Состав сложного объекта'
    assert not records[0]['forbidden']


def test_assembly_blocks_candidate_with_only_forbidden_evidence():
    findings=[{
        'parameter_code':'OBJECT_CANDIDATE','value_text':'Раздел ПД № 3_АР2.pdf',
        'document_type':'ПЗ','document':'ПЗ.pdf','page':6,
        'trusted_zone':'DOCUMENT_SERVICE','structural_zone':'Состав проектной документации',
        'object_trust_score':-100,'object_lifecycle_status':'Не определён'
    }]
    index=build_evidence_index(findings)
    rows=build_assembly_rows([], [{'Наименование объекта':'Раздел ПД № 3_АР2.pdf'}], index)
    assert rows[0]['Включить'] is False
    assert rows[0]['Блокировка']
