
from legacy_analyzer import Finding, compare_findings, load_json
from pathlib import Path
from core.object_semantics import is_parameter_entity_name
from core.ai_gateway import _needs_russian_translation

ROOT=Path(__file__).parent

def F(doc,code,pname,val,obj,pos):
    return Finding(document=doc,document_type=doc,page=1,parameter_code=code,parameter_name=pname,
                   value=val,value_text=f"{val} м²",unit="м²",context="",confidence=.95,
                   object_hint=obj,genplan_position=pos)

def test_property_label_never_object():
    assert is_parameter_entity_name("Площадь застройки")
    assert is_parameter_entity_name("Мощность 1250 кВА")
    assert not is_parameter_entity_name("КПП")
    assert not is_parameter_entity_name("Насосная станция производственно-противопожарного водоснабжения")

def test_bad_object_hint_repaired_by_position():
    params=load_json(ROOT/"parameters.json")
    findings=[
      Finding("ПЗ","ПЗ",1,"OBJECT_ENTRY","Объект",1,"КПП","шт.","",.99,"КПП",genplan_position="4.19"),
      F("ПЗ","AREA_BUILD","Площадь застройки",42.5,"Площадь застройки","4.19"),
      F("ПЗУ1","AREA_BUILD","Площадь застройки",42.5,"КПП","4.19"),
    ]
    rows=compare_findings(findings,params,[])
    area=[x for x in rows if x.get("parameter_code")=="AREA_BUILD"]
    assert area
    assert area[0]["object"]=="КПП"
    assert area[0]["status"]=="СОВПАДАЕТ"

def test_bad_object_hint_without_object_evidence_is_not_compared():
    params=load_json(ROOT/"parameters.json")
    findings=[
      F("ПЗ","AREA_BUILD","Площадь застройки",26.9,"Площадь застройки",""),
      F("ПЗУ1","AREA_BUILD","Площадь застройки",42.5,"Площадь застройки",""),
    ]
    rows=compare_findings(findings,params,[])
    assert not [x for x in rows if x.get("parameter_code")=="AREA_BUILD"]

def test_english_ai_payload_detected_for_translation():
    assert _needs_russian_translation({"result":"partial","reason":"The section contains only partial evidence","covered":["Area is shown"],"missing":[]})
    assert not _needs_russian_translation({"result":"partial","reason":"Раздел содержит только часть необходимых сведений","covered":["Площадь указана"],"missing":[]})
