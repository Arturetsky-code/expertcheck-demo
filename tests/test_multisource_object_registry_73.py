from pathlib import Path
from core.general_plan_engine import GeneralPlanRegisterEngine
from core.position_rules import normalize_genplan_position
from core.pz_complex_object_register import enforce_authoritative_pz_registry

FIXTURES = {
    '/mnt/data/1(1).pdf': {'4.1':'Подпорная стена','4.18':'Насосная станция производственно-противопожарного водоснабжения с резервуарами','4.24':'Дизельная электростанция','4.26':'Мачты освещения'},
    '/mnt/data/2(1).pdf': {'2.1':'Карта кучного выщелачивания','2.1.1':'Насосная станция золотосодержащих растворов','2.4.1':'Водосбросной канал'},
    '/mnt/data/3(1).pdf': {'3.3.1':'Общежитие для ИТР','3.3.17':'КПП','3.3.20':'Склад продуктов (рефрижераторы)'},
    '/mnt/data/4(1).pdf': {'1':'Карьер "Малеевский"','4.2':'Площадка склада упорных руд','6.3':'Площадка пруда-накопителя','8':'Площадка стоянки техники'},
}

def test_hierarchical_position_that_looks_like_date_is_kept():
    assert normalize_genplan_position('3.3.20') == '3.3.20'
    assert normalize_genplan_position('27.05.26') == ''

def test_four_real_general_plans_extract_core_explication_rows():
    eng=GeneralPlanRegisterEngine()
    for filename, expected in FIXTURES.items():
        entries,_=eng.extract_pdf(Path(filename).read_bytes(),Path(filename).name)
        got={x.position:x.name for x in entries if x.in_explication}
        for pos,name in expected.items():
            assert got.get(pos)==name, (filename,pos,got.get(pos))

def test_existing_gp_row_is_not_auto_included():
    eng=GeneralPlanRegisterEngine(); entries,_=eng.extract_pdf(Path('/mnt/data/4(1).pdf').read_bytes(),'4(1).pdf')
    row=next(x for x in entries if x.position=='4.2' and x.in_explication)
    assert row.design_status=='Существующий'

def test_gp_explication_survives_when_pz_register_is_present():
    pz=[
      {'parameter_code':'OBJECT_ENTRY','value_text':'Подпорная стена','object_hint':'Подпорная стена','genplan_position':'4.1','pz_complex_object_register':True},
      {'parameter_code':'OBJECT_ENTRY','value_text':'Операторская','object_hint':'Операторская','genplan_position':'4.4','pz_complex_object_register':True},
    ]
    gp={'parameter_code':'OBJECT_ENTRY','genplan_position':'4.30','value_text':'Новый объект с генплана','object_hint':'Новый объект с генплана','general_plan_explication':True,'general_plan_design_status':'Проектируемый'}
    t,c,a=enforce_authoritative_pz_registry([],[],pz,pz+[gp])
    assert any(x['Позиция по ГП']=='4.30' and x['Включить'] for x in t)
