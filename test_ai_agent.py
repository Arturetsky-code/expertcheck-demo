from core.ai_agent import build_grounded_snapshot,run_local_agents,answer_locally

def test_agent_detects_file_in_registry():
    s=build_grounded_snapshot([], [{'Наименование объекта':'Раздел ПД № 3_АР2.pdf','Количество источников':2}], [], [], [], registry_confirmed=True)
    assert any('служебная сущность' in x.title.lower() for x in run_local_agents(s).observations)

def test_agent_blocks_unconfirmed_registry():
    s=build_grounded_snapshot([], [], [], [], [], registry_confirmed=False);r=run_local_agents(s)
    assert r.readiness<100 and any('не подтверждён' in x.title.lower() for x in r.observations)

def test_local_question_uses_evidence_ids():
    s=build_grounded_snapshot([], [{'Наименование объекта':'Насосная станция','Позиция по ГП':'4.1'}], [], [], [], registry_confirmed=True)
    assert 'OBJ-0001' in answer_locally(s,'покажи реестр объектов')
