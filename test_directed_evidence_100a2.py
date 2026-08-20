from core.directed_evidence import build_page_corpus, attach_directed_evidence
from core.requirement_contracts import build_contract
from core.assignment_compliance import compare_requirements, TYPE_VALUE
from core.table_semantic_scope import assess_table_semantic_scope

class F:
    def __init__(self,name,text): self.name=name; self.text=text
    def getvalue(self): return self.text.encode('utf-8')

def reader(data,name):
    return [(1,data.decode('utf-8'))]

def test_project_global_shift_duration_directed_evidence():
    req={'requirement_id':'R1','requirement_text':'Продолжительность смены 12 часов','source_row_title':'Режим работы',
         'object_name':'','parameter_code':'SHIFT_DURATION','required_value':12.0,'unit':'часов','requirement_type':TYPE_VALUE}
    req['evidence_contract_v2']=build_contract(req); req['requirement_scope']=req['evidence_contract_v2']['scope']
    files=[F('Раздел ПД №6_ТХ1.pdf','Режим работы предприятия. Продолжительность смены составляет 12 часов.')]
    corpus=build_page_corpus(files,reader); attach_directed_evidence([req],corpus)
    row=compare_requirements([req],[],[])[0]
    assert row['status']=='Соответствует заданию'
    assert row['evidence_quality_state']=='VERIFIED_EVIDENCE'

def test_object_specific_capacity_needs_owner():
    req={'requirement_id':'R2','requirement_text':'Производительность ДСК 500 т/ч','source_row_title':'Технологические решения',
         'object_name':'ДСК','parameter_code':'CAPACITY','required_value':500.0,'unit':'т/ч','requirement_type':TYPE_VALUE}
    req['evidence_contract_v2']=build_contract(req); req['requirement_scope']=req['evidence_contract_v2']['scope']
    files=[F('Раздел ПД №6_ТХ1.pdf','Производительность дробильно-сортировочного комплекса (ДСК) составляет 500 т/ч.')]
    corpus=build_page_corpus(files,reader); attach_directed_evidence([req],corpus)
    row=compare_requirements([req],[],[])[0]
    assert row['status']=='Соответствует заданию'

def test_same_number_without_metric_label_is_not_evidence():
    req={'requirement_id':'R3','requirement_text':'Продолжительность смены 12 часов','source_row_title':'Режим работы',
         'object_name':'','parameter_code':'SHIFT_DURATION','required_value':12.0,'unit':'часов','requirement_type':TYPE_VALUE}
    req['evidence_contract_v2']=build_contract(req); req['requirement_scope']=req['evidence_contract_v2']['scope']
    files=[F('Раздел ПД №6_ТХ1.pdf','На площадке предусмотрено 12 шкафов управления.')]
    corpus=build_page_corpus(files,reader); attach_directed_evidence([req],corpus)
    row=compare_requirements([req],[],[])[0]
    assert row['status']=='Не проверено системой'

def test_site_area_cannot_leak_to_equipment():
    finding={'parameter_code':'AREA_BUILD','object_hint':'Оборудование дробильного комплекса','value':43414,'unit':'м2',
             'context':'Технико-экономические показатели площадки. Площадь территории 43414 м2', 'binding_status':'SEMANTIC'}
    r=assess_table_semantic_scope(finding)
    assert r['table_semantic_scope_decision']=='HOLD'
