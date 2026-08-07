from core.property_intelligence import normalize_engineering_value, infer_value_scope
from core.cross_section_consistency import build_cross_section_checks
from core.expert_review_engine import build_expert_risks


def _f(section, code, value, unit, context='', obj='КТП', pos='4.15'):
    return {'section':section,'document':section+'.pdf','parameter_code':code,'value_num':value,'unit':unit,
            'object_hint':obj,'semantic_anchor_name':obj,'genplan_position':pos,'confidence':0.95,
            'binding_status':'ROW_LOCKED','context':context,'page':1}


def test_power_unit_normalization_kva_mva():
    a=normalize_engineering_value(_f('ПЗ','POWER_KTP',1250,'кВА'))
    b=normalize_engineering_value(_f('ИОС1','POWER_KTP',1.25,'МВА'))
    assert a.value == b.value == 1250


def test_reservoir_per_unit_not_compared_to_total():
    one=_f('ПЗ','RES_VOLUME',70,'м³','объем каждого резервуара',obj='Противопожарные резервуары',pos='12')
    total=_f('ТХ','RES_VOLUME',210,'м³','суммарный объем трех резервуаров',obj='Противопожарные резервуары',pos='12')
    rows=build_cross_section_checks([one,total])
    assert len(rows)==2
    assert {r['comparison_scope'] for r in rows} == {'per_unit','total'}
    assert all(r['status']=='НЕДОСТАТОЧНО ДАННЫХ' for r in rows)


def test_width_is_compared():
    rows=build_cross_section_checks([_f('ПЗУ','WIDTH',6,'м',obj='Автомобильная дорога',pos='7'),_f('ПЗ','WIDTH',6,'м',obj='Автомобильная дорога',pos='7')])
    assert rows and rows[0]['parameter_code']=='WIDTH'
    assert rows[0]['status']=='СОВПАДАЕТ'


def test_risk_matches_exact_pressure_scenario():
    risks=build_expert_risks([{'check_code':'x','status':'ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ','object':'Трубопровод','parameter_code':'PRESSURE','parameter_name':'Давление','priority':'Высокий','sources':'ПЗ / ТХ'}])
    assert risks
    assert risks[0]['scenario_id']=='GGE-TEP-007'
