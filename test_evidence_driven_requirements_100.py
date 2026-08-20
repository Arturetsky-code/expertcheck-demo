from core.requirement_contracts import build_contract, SCOPE_PROJECT, SCOPE_EQUIPMENT
from core.assignment_compliance import compare_requirements, TYPE_VALUE
from core.nonfinding_policy import can_create_negative_finding
from core.normative_kb_v4 import classify_rule, KIND_ENGINEERING, KIND_LAW


def test_project_global_value_can_match_without_object_owner():
    req={"requirement_id":"A1","requirement_text":"Продолжительность смены – 12 часов","source_row_title":"Режим работы","requirement_type":TYPE_VALUE,"parameter_code":"SHIFT_DURATION","required_value":12.0,"unit":"часов","object_name":""}
    req['evidence_contract_v2']=build_contract(req); req['requirement_scope']=req['evidence_contract_v2']['scope']
    assert req['requirement_scope']==SCOPE_PROJECT
    findings=[{"parameter_code":"SHIFT_DURATION","value":12.0,"parameter_name":"Продолжительность смены","document":"ТХ.pdf","page":7,"document_type":"ТХ","fact_admission_decision":"ADMIT"}]
    row=compare_requirements([req],findings,[])[0]
    assert row['status']=='Соответствует заданию'


def test_equipment_value_still_requires_same_owner():
    req={"requirement_id":"A2","requirement_text":"Автосамосвал SinoTrack объемом кузова 32 м3","source_row_title":"Технологические решения","requirement_type":TYPE_VALUE,"parameter_code":"BODY_VOLUME","required_value":32.0,"unit":"м3","object_name":"Автосамосвал SinoTrack"}
    req['evidence_contract_v2']=build_contract(req); req['requirement_scope']=req['evidence_contract_v2']['scope']
    assert req['requirement_scope']==SCOPE_EQUIPMENT
    findings=[{"parameter_code":"BODY_VOLUME","value":6.0,"semantic_anchor_name":"Выгреб","parameter_name":"Объем","document":"ПЗ.pdf","page":5,"document_type":"ПЗ","fact_admission_decision":"ADMIT"}]
    row=compare_requirements([req],findings,[])[0]
    assert row['status']!='Выявлено отклонение'


def test_not_found_never_creates_negative_finding():
    assert not can_create_negative_finding(status='Не найдено',basis='Автоматический анализ не подтвердил наличие документа',evidence='')
    assert can_create_negative_finding(status='Выявлено отклонение',basis='Значения противоречат',evidence='ПЗ стр. 5 / ПЗУ стр. 7',explicit_contradiction=True)


def test_normative_rule_kinds_are_separated():
    assert classify_rule({'source':'Инженерное правило ExpertCheck','document_id':''})==KIND_ENGINEERING
    assert classify_rule({'source':'Постановление Правительства РФ № 87','document_id':'PP87'})==KIND_LAW
