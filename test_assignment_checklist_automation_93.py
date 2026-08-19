
from pathlib import Path
from core.assignment_compliance import extract_requirements, compare_requirements, summary
from core.checklist_routing import ChecklistRoutingEngine, canonical_section
from core.checklist_engine import ChecklistEngine
from core.project_upload import guess_document_type

ROOT=Path(__file__).parent

class FakeUpload:
    name="Задание на проектирование.pdf"
    declared_document_type="Задание на проектирование"
    def getvalue(self): return b"x"

def test_assignment_is_classified():
    assert guess_document_type("01_Задание на проектирование.pdf")=="Задание на проектирование"

def test_assignment_extracts_numeric_requirement():
    def reader(data,name):
        return [(1,"Задание на проектирование. Предусмотреть КТП мощностью 1250 кВА. Предусмотреть строительство КПП.")]
    rows=extract_requirements([FakeUpload()],reader)
    assert any(x["parameter_code"]=="POWER_INSTALLED" and x["required_value"]==1250 for x in rows)
    assert any("Кпп" in x["object_name"] or "КПП" in x["object_name"] for x in rows)

def test_assignment_numeric_comparison():
    req=[{"requirement_id":"A","source_document":"Задание.pdf","page":1,"requirement_text":"Предусмотреть КТП мощностью 1250 кВА",
          "object_name":"КТП","object_id":"OBJ-X","parameter_code":"POWER_INSTALLED","required_value":1250.0,"unit":"кВА",
          "requirement_type":"NUMERIC","confidence":.9}]
    findings=[{"document":"ИОС1.pdf","page":12,"parameter_code":"POWER_INSTALLED","parameter_name":"Мощность",
               "value":1250.0,"unit":"кВА","object_hint":"КТП","semantic_anchor_name":"КТП"}]
    rows=compare_requirements(req,findings,[])
    assert rows[0]["status"]=="Соответствует заданию"
    assert summary(rows)["compliant"]==1

def test_checklist_router_normalizes_parts():
    engine=ChecklistEngine(ROOT/"knowledge"/"checklist_catalog.json")
    router=ChecklistRoutingEngine(engine)
    docs=[
      {"Файл":"ЭС.pdf","Тип документа":"ИОС1.1"},
      {"Файл":"ПЗУ2.pdf","Тип документа":"ПЗУ2"},
      {"Файл":"АР1.pdf","Тип документа":"АР1"},
    ]
    result=router.route(docs)
    assert "ИОС1" in result["covered_sections"]
    assert "ПЗУ" in result["covered_sections"]
    assert "АР" in result["uncovered_sections"]  # recognized, but no corporate AR checklist exists yet

def test_canonical_section_synonyms():
    assert canonical_section("Система электроснабжения ИОС1.1")=="ИОС1"
    assert canonical_section("Графическая часть ПЗУ2")=="ПЗУ"
    assert canonical_section("МООС / ОВОС")=="ООС"
