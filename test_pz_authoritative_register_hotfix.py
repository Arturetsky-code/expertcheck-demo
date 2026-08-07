from core.pz_complex_object_register import extract_pz_complex_object_register_from_pages


def test_complex_object_register_multiline_and_properties():
    pages=[{
        'document':'ПЗ.pdf','document_type':'ПЗ','page':44,
        'text':'''Сведения о сложном объекте, применительно к которому разработана проектная документация, а также\nсведения о зданиях (сооружениях), входящих в состав сложного объект\n4.1\nПодпорная стена\nРФ, Забайкальский край\n08.04.002.099 Объекты\nДлина 68,5 м Высотность 6,6 м\n4.13\nЗдание проборазделки\nРФ, Забайкальский край\n08.04.002.099 Объекты\nПлощадь застройки 89,9 м2 Общая площадь 74,7 м2 Строительный объем 433,0 м3\nЗаверение проектной организации'''
    }]
    findings,audit=extract_pz_complex_object_register_from_pages(pages)
    objs=[x for x in findings if x.get('parameter_code')=='OBJECT_ENTRY']
    assert [(x['genplan_position'],x['value_text']) for x in objs]==[('4.1','Подпорная стена'),('4.13','Здание проборазделки')]
    props=[x for x in findings if x.get('object_hint')=='Здание проборазделки' and x.get('parameter_code')!='OBJECT_ENTRY']
    assert {x['parameter_code'] for x in props} >= {'AREA_BUILD','AREA_TOTAL','VOLUME_BUILD'}


def test_complex_object_register_joins_name_across_page_boundary():
    pages=[
      {'document':'ПЗ.pdf','document_type':'ПЗ','page':45,'text':'Сведения о сложном объекте, применительно к которому разработана проектная документация, а также сведения о зданиях (сооружениях), входящих в состав сложного объект\n4.15\nКомплектная\nтрансформаторная\n25.06.2026, 12:30\nПояснительная записка\n45/47'},
      {'document':'ПЗ.pdf','document_type':'ПЗ','page':46,'text':'подстанция\nРФ, Забайкальский край\nНапряжение 6/0,4 кВ\n4.16\nЭлектрощитовая\nРФ, Забайкальский край\nЗаверение проектной организации'},
    ]
    findings,_=extract_pz_complex_object_register_from_pages(pages)
    objs=[x for x in findings if x.get('parameter_code')=='OBJECT_ENTRY']
    assert objs[0]['value_text']=='Комплектная трансформаторная подстанция'
    assert objs[1]['value_text']=='Электрощитовая'


def test_authoritative_pz_register_overrides_generic_service_and_lifecycle_heuristics():
    from core.object_gate import apply_hard_object_gate
    from core.trusted_project_model import annotate_findings, filter_registry
    from core.object_register_engine import build_registry
    rows=[
      {'document':'ПЗ.pdf','document_type':'ПЗ','page':45,'parameter_code':'OBJECT_ENTRY','value_text':'Здание с кабинетом начальника','object_hint':'Здание с кабинетом начальника','genplan_position':'4.6','source_kind':'pz_complex_object_register','pz_complex_object_register':True,'structural_zone':'ПЗ / Сведения о сложном объекте / официальный состав','confidence':.995},
      {'document':'ПЗ.pdf','document_type':'ПЗ','page':46,'parameter_code':'OBJECT_ENTRY','value_text':'Насосная станция производственно-противопожарного водоснабжения с резервуарами','object_hint':'Насосная станция производственно-противопожарного водоснабжения с резервуарами','genplan_position':'4.18','source_kind':'pz_complex_object_register','pz_complex_object_register':True,'structural_zone':'ПЗ / Сведения о сложном объекте / официальный состав','confidence':.995},
      {'document':'ПЗ.pdf','document_type':'ПЗ','page':46,'parameter_code':'OBJECT_ENTRY','value_text':'Пункт обогрева','object_hint':'Пункт обогрева','genplan_position':'4.20','source_kind':'pz_complex_object_register','pz_complex_object_register':True,'structural_zone':'ПЗ / Сведения о сложном объекте / официальный состав','confidence':.995},
    ]
    audit=apply_hard_object_gate(rows)
    assert audit['blocked']==0
    annotate_findings(rows)
    assert all(x['object_lifecycle_status']=='Проектируемый' for x in rows)
    raw,_=build_registry(rows)
    trusted,candidates=filter_registry(raw,rows)
    assert len(trusted)==3 and not candidates


def test_authoritative_pz_baseline_suppresses_identification_only_rows_but_keeps_gp_discrepancy():
    from core.pz_complex_object_register import enforce_authoritative_pz_registry
    pz=[
      {'parameter_code':'OBJECT_ENTRY','value_text':'Подпорная стена','object_hint':'Подпорная стена','genplan_position':'4.1','pz_complex_object_register':True},
      {'parameter_code':'OBJECT_ENTRY','value_text':'Операторская','object_hint':'Операторская','genplan_position':'4.4','pz_complex_object_register':True},
    ]
    trusted=[
      {'Позиция по ГП':'4.1','Наименование объекта':'Подпорная стена'},
      {'Позиция по ГП':'4.2','Наименование объекта':'Технологический комплекс'},
      {'Позиция по ГП':'4.24','Наименование объекта':'Дизельная электростанция'},
    ]
    candidates=[{'Позиция по ГП':'4.30','Наименование объекта':'Новый объект с генплана'}]
    findings=pz+[
      {'parameter_code':'OBJECT_ENTRY','genplan_position':'4.30','value_text':'Новый объект с генплана','general_plan_explication':True},
    ]
    t,c,a=enforce_authoritative_pz_registry(trusted,candidates,pz,findings)
    assert [x['Позиция по ГП'] for x in t][:2]==['4.1','4.4']
    assert any(x['Позиция по ГП']=='4.30' for x in t)
    assert not any(x['Позиция по ГП']=='4.30' for x in c)
    assert a['suppressed_non_authoritative']==0
