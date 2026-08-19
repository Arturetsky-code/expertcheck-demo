
from core.project_understanding import build_project_object_model,understanding_quality

def registry():
    return [
      {"Наименование объекта":"КПП","Позиция по ГП":"4.19","Тип объекта":"Здание"},
      {"Наименование объекта":"Насосная станция","Позиция по ГП":"4.20","Тип объекта":"Сооружение"},
    ]

def test_parameter_cannot_become_object():
    findings=[{"parameter_code":"AREA_BUILD","parameter_name":"Площадь застройки","value":26.9,"unit":"м²",
               "object_hint":"Площадь застройки","document_type":"ПЗ","document":"ПЗ.pdf","page":46}]
    model=build_project_object_model(registry(),findings)
    assert model["stats"]["properties_bound"]==0
    assert model["stats"]["properties_rejected"]==1

def test_same_object_property_binding():
    findings=[{"parameter_code":"AREA_BUILD","parameter_name":"Площадь застройки","value":42.5,"unit":"м²",
               "object_hint":"КПП","semantic_anchor_name":"КПП","genplan_position":"4.19",
               "document_type":"ПЗУ1","document":"ПЗУ.pdf","page":18,"confidence":.9}]
    model=build_project_object_model(registry(),findings)
    obj=[x for x in model["objects"] if x["name"]=="КПП"][0]
    assert "AREA_BUILD" in obj["properties"]
    assert obj["properties"]["AREA_BUILD"][0]["section"]=="ПЗУ"

def test_different_object_is_not_bound():
    findings=[{"parameter_code":"AREA_BUILD","parameter_name":"Площадь застройки","value":42.5,"unit":"м²",
               "object_hint":"Компрессорная","semantic_anchor_name":"Компрессорная",
               "document_type":"ПЗ","document":"ПЗ.pdf","page":10,"confidence":.95}]
    model=build_project_object_model(registry(),findings)
    assert model["stats"]["properties_bound"]==0
    assert model["stats"]["properties_unresolved"]==1

def test_position_is_strong_binding():
    findings=[{"parameter_code":"POWER_INSTALLED","parameter_name":"Мощность","value":75,"unit":"кВт",
               "object_hint":"Насосная","semantic_anchor_name":"Насосная","genplan_position":"4.20",
               "document_type":"ИОС1","document":"ИОС1.pdf","page":12,"confidence":.8}]
    model=build_project_object_model(registry(),findings)
    obj=[x for x in model["objects"] if x["name"]=="Насосная станция"][0]
    assert obj["properties"]["POWER_INSTALLED"][0]["value"]==75

def test_quality_reports_unresolved():
    model=build_project_object_model(registry(),[
      {"parameter_code":"AREA_BUILD","parameter_name":"Площадь застройки","value":1,"object_hint":"Неизвестный цех","document_type":"ПЗ","confidence":.9}
    ])
    q=understanding_quality(model)
    assert q["unresolved_properties"]==1
    assert "не используется" in q["guardrail"].lower()
