from core.directed_evidence import normalize_engineering_unit, units_compatible
from core.evidence_semantics import promote_candidates
from core.entity_scope_graph import infer_entity_level, metric_scope_compatible
from core.finding_qualification import qualify_comparison, qualify_checklist
from core.display_localization import evidence_label, header_label

def test_capacity_unit_normalization():
    assert normalize_engineering_unit('тыс. тонн в год')=='тыс.т/год'
    assert units_compatible('тыс. т/год','тыс. тонн в год','CAPACITY')

def test_semantic_promotion_project_capacity():
    req={'parameter_code':'CAPACITY','unit':'тыс. т/год','requirement_scope':'PROJECT_GLOBAL','source_row_title':'Производственная мощность','requirement_text':'Производственная мощность 1 600 тыс. тонн в год'}
    cand={'parameter_code':'CAPACITY','unit':'тыс. тонн в год','context':'Мощность дробильно-сортировочного комплекса 1600 тыс. тонн в год','unit_compatible':True,'owner_match':True}
    out=promote_candidates(req,[cand])[0]
    assert out['evidence_state']=='verified_candidate'

def test_scope_graph():
    assert infer_entity_level('Оборудование дробильного комплекса')=='EQUIPMENT'
    assert not metric_scope_compatible('site_area','EQUIPMENT')
    assert metric_scope_compatible('room_area','ROOM')

def test_finding_types():
    q=qualify_comparison({'status':'НЕДОСТАТОЧНО ДАННЫХ'})
    assert q['finding_type']=='SYSTEM_LIMITATION' and not q['risk_eligible']
    q2=qualify_comparison({'status':'Потенциальное расхождение','independent_trusted_sources':2,'independent_section_count':2,'sources':'ПЗ; ПЗУ'})
    assert q2['finding_type']=='PROJECT_FINDING'

def test_localization():
    assert evidence_label('TABLE_CELL_LOCKED')=='Ячейка таблицы восстановлена'
    assert header_label('canonical_id')=='Канонический ID'
