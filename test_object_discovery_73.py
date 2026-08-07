from core.object_gate import hard_rejection_reason
from core.object_discovery_orchestrator import ensure_general_plan_registry_visibility
from core.project_assembly import build_assembly_rows


def test_property_label_is_not_object():
    item={"parameter_code":"OBJECT_CANDIDATE","value_text":"Площадь застройки, всего, в т.ч.:"}
    assert "показател" in hard_rejection_reason(item).lower()


def test_calendar_date_position_is_not_genplan_position():
    item={"parameter_code":"OBJECT_CANDIDATE","value_text":"Склад", "genplan_position":"21.05.26"}
    assert "дат" in hard_rejection_reason(item).lower()


def test_general_plan_explication_remains_visible_as_candidate():
    gp=[{
        "general_plan_explication":True,"genplan_position":"4.13","value_text":"Здание проборазделки",
        "object_lifecycle_status":"Не определён","confidence":0.96,"page":5,"document":"ПЗУ2.pdf"
    }]
    trusted,candidates,audit=ensure_general_plan_registry_visibility([],[],gp)
    assert not trusted
    assert len(candidates)==1
    assert candidates[0]["Позиция по ГП"]=="4.13"
    assert audit["general_plan_seed_candidates"]==1


def test_review_does_not_disable_following_trusted_rows():
    trusted=[
        {"Позиция по ГП":"4.13","Наименование объекта":"Здание проборазделки"},
        {"Позиция по ГП":"4.15","Наименование объекта":"Комплектная трансформаторная подстанция"},
    ]
    decisions={
        "4.13|здание проборазделки":{"decision":"review","confidence":82},
        "4.15|комплектная трансформаторная подстанция":{"decision":"trusted","confidence":96},
    }
    rows=build_assembly_rows(trusted,[],{},decisions)
    assert [r["Включить"] for r in rows] == [True, True]
