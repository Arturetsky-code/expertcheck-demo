from core.ai_gateway import AIResult
from core.ai_pipeline import run_ai_pipeline


class FakeProvider:
    name = 'Fake'
    def generate(self, prompt, system=''):
        if 'object_registry_review' in prompt:
            return AIResult(True, 'Fake', text='{"items":[{"key":"|раздел пд № 5.pdf","entity_type":"document_service","design_status":"unknown","independent_object":false,"confidence":0.99,"recommended_action":"exclude","reason":"имя файла","evidence_refs":["ПЗ/1"]}]}')
        return AIResult(True, 'Fake', text='{"items":[{"key":"cmp-0","binding":"suspicious","confidence":0.91,"reason":"нет доказательства общей строки","recommended_status":"requires_review"}]}')


def test_ai_pipeline_blocks_service_candidate_and_downgrades_ambiguous_comparison():
    findings=[{
        'parameter_code':'OBJECT_CANDIDATE','value_text':'Раздел ПД № 5.pdf',
        'object_intelligence_decision':'review','object_intelligence_confidence':20,
        'document':'ПЗ','page':1,
    }]
    comparisons=[{'status':'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ','object':'Здание','parameter':'Площадь'}]
    audit=run_ai_pipeline(findings,comparisons,provider=FakeProvider(),level='extended')
    assert findings[0]['object_intelligence_decision']=='blocked'
    assert comparisons[0]['status']=='НЕДОСТАТОЧНО ДАННЫХ'
    assert audit['object_reviews_received']==1
    assert audit['property_reviews_received']==1


def test_ai_pipeline_off_does_not_change_data():
    findings=[{'parameter_code':'OBJECT_CANDIDATE','value_text':'Насосная'}]
    comparisons=[]
    audit=run_ai_pipeline(findings,comparisons,provider=FakeProvider(),level='off')
    assert audit['enabled'] is False
    assert 'ai_object_review' not in findings[0]
