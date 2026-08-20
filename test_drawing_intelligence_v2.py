from pathlib import Path
import json
import pytest

from core.drawing_intelligence_v2 import (
    parse_title_block, parse_room_explication, DrawingIntelligenceV2, drawing_graph_findings
)
from core.fact_admission import assess_fact_admission


def test_room_schedule_is_not_building_area():
    text='''
Экспликация помещений
Номер
поме-\nщения
Наименование
Площадь,\nм²
Кат. поме-\nщения
1
Коридор
7,9
2
Венткамера
32,6
В4
Итого:
40.5
RAM-0207.4-ЗД-ПД-4.13-АР2
Здание проборазделки
Потапенко
'''
    title=parse_title_block(text)
    sched=parse_room_explication(text)
    assert title['resolved'] is True
    assert title['position']=='4.13'
    assert title['object_name']=='Здание проборазделки'
    assert sched['resolved'] is True
    assert sched['reported_total']==40.5
    assert sched['calculated_total']==40.5
    assert sched['total_matches_rows'] is True


def test_fact_admission_withholds_room_area_from_project_tep():
    item={
        'document':'АР2.pdf','page':22,'document_type':'АР','object_hint':'Венткамера',
        'parameter_code':'AREA_ROOM','parameter_name':'Площадь помещения','value':32.6,'unit':'м²',
        'drawing_evidence':True,'scope_entity_type':'ROOM','metric_semantic_scope':'room_area',
        'comparison_excluded':True,'comparison_exclusion_reason':'площадь помещения не является ТЭП здания',
        'binding_status':'ROW_LOCKED','confidence':0.99,
    }
    decision=assess_fact_admission(item)
    assert decision['fact_admission_decision']=='HOLD'
    assert 'не является ТЭП здания' in decision['fact_admission_reasons'][0]


def test_drawing_graph_findings_are_explicitly_comparison_excluded():
    graph={'room_schedules':[{
        'document':'АР2.pdf','page':22,'position':'4.13','parent_object':'Здание проборазделки','bbox':[1,2,3,4],
        'rows':[{'room_no':'5','room_name':'Венткамера','area':32.6,'category':'В4'}],
        'reported_total':72.0,'total_matches_rows':True,
    }]}
    rows=drawing_graph_findings(graph)
    assert len(rows)==2
    assert all(x['comparison_excluded'] for x in rows)
    assert {x['parameter_code'] for x in rows}=={'AREA_ROOM','AREA_ROOM_SUM'}


def test_real_ar2_golden_if_available():
    source=Path('/mnt/data/Раздел ПД №3_АР2.pdf')
    if not source.exists():
        pytest.skip('real AR2 fixture is external to release archive')
    import legacy_analyzer as legacy
    class U:
        name='Раздел ПД №3_АР2.pdf'
        def getvalue(self): return source.read_bytes()
    graph=DrawingIntelligenceV2().extract_uploaded([U()],{U.name:'АР'},legacy.read_pdf)
    by_pos={x['position']:x for x in graph['room_schedules']}
    assert by_pos['4.12']['reported_total']==12.7
    assert by_pos['4.13']['reported_total']==72.0
    assert by_pos['4.16']['reported_total']==87.1
    assert by_pos['4.5']['reported_total']==25.4
    assert by_pos['4.13']['total_matches_rows'] is True
    vent=[r for r in by_pos['4.13']['rows'] if r['room_name']=='Венткамера'][0]
    assert vent['area']==32.6
