from core.object_intelligence import build_object_decisions
from core.project_assembly import build_assembly_rows
from core.evidence_registry import build_evidence_index


def test_file_only_candidate_is_blocked():
    findings=[{
        'parameter_code':'OBJECT_CANDIDATE','value_text':'Раздел ПД № 5_ТХ.pdf',
        'document':'Состав ПД.pdf','document_type':'ПЗ','page':2,
        'trusted_zone':'DOCUMENT_SERVICE','object_lifecycle_status':'Проектируемый',
        'object_trust_score':-100,
    }]
    decisions=build_object_decisions(findings)
    decision=next(iter(decisions.values()))
    assert decision['decision']=='blocked'


def test_official_object_register_is_trusted():
    findings=[{
        'parameter_code':'OBJECT_ENTRY','value_text':'Здание проборазделки','genplan_position':'4.13',
        'document':'ПЗ.pdf','document_type':'ПЗ','page':45,
        'trusted_zone':'OBJECT_REGISTER','structural_zone':'Состав сложного объекта',
        'object_lifecycle_status':'Проектируемый','object_trust_score':100,
    }]
    decisions=build_object_decisions(findings)
    decision=next(iter(decisions.values()))
    assert decision['decision']=='trusted'
    assert decision['official_sources']==1
    assert decision['canonical_source']['page']==45


def test_narrative_only_requires_review():
    findings=[{
        'parameter_code':'OBJECT_CANDIDATE','value_text':'Насосная станция',
        'document':'ТХ.pdf','document_type':'ТХ','page':17,
        'trusted_zone':'NARRATIVE','object_lifecycle_status':'Проектируемый',
        'object_trust_score':10,
    }]
    decisions=build_object_decisions(findings)
    assert next(iter(decisions.values()))['decision']=='review'


def test_assembly_uses_intelligence_decision():
    findings=[{
        'parameter_code':'OBJECT_CANDIDATE','value_text':'Насосная станция',
        'document':'ТХ.pdf','document_type':'ТХ','page':17,
        'trusted_zone':'NARRATIVE','object_lifecycle_status':'Проектируемый',
        'object_trust_score':10,
    }]
    decisions=build_object_decisions(findings)
    rows=build_assembly_rows([], [{'Наименование объекта':'Насосная станция'}], build_evidence_index(findings), decisions)
    assert rows[0]['Включить'] is False
    assert rows[0]['Решение Object Intelligence']=='review'
