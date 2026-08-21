from core.verification_core import classify_verification
from core.fact_admission import assess_fact_admission
from core.report_engine import build_structured_report

def test_l5_presence_cannot_close_engineering_check():
 r={'status':'Да','proof_kind':'PRESENCE','verification_level':'L5_ENGINEERING_COMPLIANCE','evidence':'найден фрагмент'}
 assert classify_verification(r,'checklist')['verification_kind']=='SYSTEM_LIMITATION'

def test_building_area_rejected_for_equipment_scope():
 r={'parameter_code':'AREA_BUILD','object_hint':'Оборудование дробильного комплекса','value':43414,'document':'ПЗ','page':27,'binding_status':'ROW_LOCKED'}
 assert assess_fact_admission(r)['fact_admission_decision']!='ADMIT'

def test_project_understanding_conflict_survives_to_report():
 pu={'objects':[{'name':'Компрессорная','property_summary':[{'parameter_name':'Площадь застройки','value_conflict':True,'sections':['ПЗ','ПЗУ'],'values':[48.7,54.3]}]}]}
 rep=build_structured_report('P',[{'project_understanding':pu}],[])
 assert rep['summary']['project_findings']==1
 assert any(x['object']=='Компрессорная' for x in rep['problems'])
