from core.checklist_compiler import compile_item
from core.deep_evidence_intelligence import apply_deep_evidence_decisions, run_deep_evidence_review
from core.general_plan_engine import _is_plausible_name
from core.project_evidence_database import build_project_evidence_database
from core.project_review_planner import build_review_plan
from core.project_understanding import build_project_object_model
from core.report_quality_gate import validate_review_plan
from core.typed_check_engine import execute_typed_check
from core.verification_core import classify_verification, domain_summary
from core.verification_recipe_critic import critique_recipe
from core.verification_regression_gate import regression_gate


def test_ai_provisional_is_never_confirmed():
    row={
        'status':'Предварительно подтверждено AI',
        'evidence':'Найден смысловой кандидат',
        'evidence_quality_state':'CANDIDATE_EVIDENCE',
    }
    result=classify_verification(row,'assignment')
    assert result['verification_kind']=='REVIEW_QUESTION'
    assert domain_summary([row],'assignment')['automatic_coverage_pct']==0.0


def test_assignment_positive_requires_verified_evidence():
    weak=classify_verification({
        'status':'Соответствует заданию','evidence':'Похожий текст',
        'evidence_quality_state':'CANDIDATE_EVIDENCE',
    },'assignment')
    strong=classify_verification({
        'status':'Соответствует заданию','evidence':['ПЗ, стр. 4: 1600 тыс. т/год'],
        'evidence_quality_state':'VERIFIED_EVIDENCE',
    },'assignment')
    assert weak['verification_kind']=='SYSTEM_LIMITATION'
    assert strong['verification_kind']=='VERIFIED_OK'


def test_deep_evidence_verdict_is_merged_back_into_domain_rows():
    rows=[{
        'requirement_id':'REQ-1','requirement_text':'Производительность 1600 тыс. т/год',
        'status':'Соответствует заданию','evidence':['ПЗ, стр. 4'],
        'evidence_quality_state':'VERIFIED_EVIDENCE','object_name':'ДСК',
        'parameter_code':'CAPACITY','required_value':1600,'unit':'тыс. т/год',
    }]
    plan=build_review_plan(assignment_rows=rows,normative_rows=[],checklist_review={'results':[]})
    review=run_deep_evidence_review(plan['items'],facts=[])
    merged=apply_deep_evidence_decisions(review,assignment_rows=rows,checklist_review={'results':[]})
    assert merged['blocked']==1
    assert rows[0]['status']=='Требует проверки'
    assert rows[0]['final_verification_kind']=='REVIEW_QUESTION'
    final_plan=build_review_plan(assignment_rows=rows,normative_rows=[],checklist_review={'results':[]})
    assert final_plan['domains']['assignment']['confirmed']==0


def test_strong_pipeline_fact_survives_deep_evidence_gate():
    rows=[{
        'requirement_id':'REQ-2','requirement_text':'Производительность 1600 тыс. т/год',
        'status':'Соответствует заданию','evidence':['ПЗ, стр. 44'],
        'evidence_quality_state':'VERIFIED_EVIDENCE','object_name':'ДСК',
        'parameter_code':'CAPACITY','required_value':1600,'unit':'тыс. т/год',
    }]
    plan=build_review_plan(assignment_rows=rows,normative_rows=[],checklist_review={'results':[]})
    review=run_deep_evidence_review(plan['items'],facts=[{
        'object_hint':'ДСК','parameter_code':'CAPACITY','value':1600,'unit':'тыс. т/год',
        'document':'ПЗ.pdf','page':44,'binding_status':'ROW_LOCKED',
    }])
    assert review['results'][0]['adversarial_state']=='PASSED'
    apply_deep_evidence_decisions(review,assignment_rows=rows,checklist_review={'results':[]})
    assert rows[0]['final_verification_kind']=='VERIFIED_OK'


def test_pipeline_fact_fields_feed_strong_evidence_database():
    db=build_project_evidence_database(facts=[{
        'object_hint':'ДСК','parameter_code':'CAPACITY','value':1600,'unit':'тыс. т/год',
        'document':'ПЗ.pdf','page':44,'binding_status':'ROW_LOCKED',
    },{
        'object_hint':'Компрессорная','parameter_code':'AREA_BUILD','value':24.7,
        'document':'ПЗ.pdf','page':45,'fact_admission_decision':'HOLD',
    }])
    assert db['record_count']==1
    assert db['records'][0]['owner']=='ДСК'
    assert db['records'][0]['metric']=='CAPACITY'
    assert db['records'][0]['kind']=='STRUCTURED_FACT'


def test_correctness_question_cannot_compile_as_presence():
    rule=compile_item({'question':'Правильность заполнения общих указаний (согласно шаблона на общие указания)'})
    assert rule.rule_type=='semantic_review'
    assert rule.verification_level=='L5_ENGINEERING_COMPLIANCE'


def test_plain_keyword_hit_is_only_candidate():
    rule=compile_item({'question':'Наличие отмостки, лестницы и площадки обслуживания'})
    result=execute_typed_check(rule.to_dict(),[{
        'document':'ПЗУ.pdf','page':10,
        'context':'На площадке предусмотрены лестницы и отдельные сооружения.',
    }],[])
    assert result['status']!='Да'
    assert result['proof_kind'] in {'CANDIDATE_EVIDENCE','UNSUPPORTED'}


def test_recipe_gate_rejects_correctness_as_presence():
    recipe={
        'domain':'checklist','title':'Правильность заполнения общих указаний',
        'verification_level':'L1_PRESENCE','check_method':'DOCUMENT_CONTENT_PRESENCE',
        'required_evidence':['TEXT_OR_TABLE','PAGE_REFERENCE'],'expected_sections':['SELECTED_SECTION'],
        'confidence':0.86,'abstain_policy':'ABSTAIN',
    }
    reviewed={**recipe,**critique_recipe(recipe)}
    gated=regression_gate(reviewed)
    assert reviewed['critic_pass'] is False
    assert gated['recipe_status']=='EXPERIMENTAL'
    assert gated['regression_violations']


def test_single_surname_fragment_is_not_general_plan_object():
    assert _is_plausible_name('Бурда') is False
    assert _is_plausible_name('КТП') is True
    assert _is_plausible_name('Компрессорная') is True


def test_object_source_lineage_keeps_document_and_page():
    model=build_project_object_model([{
        'Позиция по ГП':'4.5','Наименование объекта':'Компрессорная',
        'source_records':[{'kind':'GENERAL_PLAN_EXPLICATION','document':'ПЗУ2.pdf','page':18}],
    }],[])
    obj=model['objects'][0]
    assert obj['source_lineage_status']=='VERIFIED_SOURCE'
    assert 'ПЗУ2.pdf, стр. 18' in obj['sources']


def test_report_quality_gate_accepts_consistent_plan():
    plan=build_review_plan(
        assignment_rows=[{'status':'Не проверено системой','evidence_quality_state':'NO_EVIDENCE'}],
        normative_rows=[],checklist_review={'results':[]},
    )
    result=validate_review_plan(plan)
    assert result['status']=='PASSED',result['issues']
