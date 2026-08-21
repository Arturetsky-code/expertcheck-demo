from core.project_evidence_database import build_project_evidence_database
from core.evidence_retrieval_cascade import retrieve_evidence
from core.adversarial_review import adversarial_gate
from core.deep_evidence_intelligence import run_deep_evidence_review

def test_db_does_not_invent_owner():
    db=build_project_evidence_database(facts=[{'metric':'AREA_BUILD','value':43414,'owner':''}])
    assert db['records'][0]['owner']==''

def test_cascade_prefers_entity_metric():
    db=build_project_evidence_database(facts=[
        {'owner':'ДСК','metric':'Производительность','value':500,'unit':'т/ч'},
        {'owner':'Дробилка','metric':'Производительность','value':250,'unit':'т/ч'}])
    got=retrieve_evidence({'entity':'ДСК','metric':'Производительность','title':'500 т/ч'},db)
    assert got[0]['owner']=='ДСК'

def test_adversarial_blocks_weak_positive():
    r=adversarial_gate({'verification_kind':'VERIFIED_OK'},[{'kind':'DOCUMENT_TEXT','retrieval_score':90}])
    assert r['verification_kind']=='REVIEW_QUESTION' and r['adversarial_state']=='BLOCKED'

def test_adversarial_accepts_strong_structured_positive():
    r=adversarial_gate({'verification_kind':'VERIFIED_OK'},[{'kind':'STRUCTURED_FACT','retrieval_score':90}])
    assert r['adversarial_state']=='PASSED'

def test_three_pass_review():
    out=run_deep_evidence_review([{'plan_id':'A1','title':'Производительность ДСК','entity':'ДСК','metric':'Производительность','verification_kind':'VERIFIED_OK'}],facts=[{'owner':'ДСК','metric':'Производительность','value':500,'unit':'т/ч'}])
    assert len(out['passes'])==3 and out['metrics']['with_candidates']==1

def test_historical_benchmark_metrics():
    from core.historical_expert_benchmark import evaluate_findings
    x=evaluate_findings([{'benchmark_id':'a'},{'benchmark_id':'b'}],[{'benchmark_id':'a'},{'benchmark_id':'c'}])
    assert x['expert_recall_pct']==50.0 and x['finding_precision_pct']==50.0
