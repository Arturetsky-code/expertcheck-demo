
from pathlib import Path
import pandas as pd
from core.entity_property_binding import validate_entity_property, stable_object_id
from core.cross_section_consistency import build_cross_section_checks

def test_property_cannot_be_object():
    bad=validate_entity_property("Площадь застройки","Площадь застройки","AREA_BUILD","")
    assert not bad["valid"]
    good=validate_entity_property("КПП","Площадь застройки","AREA_BUILD","4.19")
    assert good["valid"]
    assert good["object_id"].startswith("OBJ-POS-")

def test_object_id_stable_by_position():
    assert stable_object_id("КПП","4.19")==stable_object_id("Контрольно-пропускной пункт","4.19")

def test_cross_section_sources_keep_object_and_property_separate():
    findings=[
      {"document":"ПЗ.pdf","document_type":"ПЗ","page":46,"parameter_code":"AREA_BUILD",
       "parameter_name":"Площадь застройки","value":26.9,"value_text":"Площадь застройки 26,9 м2",
       "unit":"м²","object_hint":"КПП","semantic_anchor_name":"КПП","genplan_position":"4.19",
       "confidence":.96,"core2_confidence":.96,"binding_status":"POSITION_LOCKED"},
      {"document":"ПЗУ1.pdf","document_type":"ПЗУ1","page":18,"parameter_code":"AREA_BUILD",
       "parameter_name":"Площадь застройки","value":42.5,"value_text":"КПП 42,5 м2",
       "unit":"м²","object_hint":"КПП","semantic_anchor_name":"КПП","genplan_position":"4.19",
       "confidence":.96,"core2_confidence":.96,"binding_status":"POSITION_LOCKED"},
    ]
    rows=build_cross_section_checks(findings)
    assert rows
    row=rows[0]
    assert row["object"]=="КПП"
    assert row["parameter_name"]=="Площадь застройки"
    assert row["object_id"].startswith("OBJ-POS-")
    assert "КПП · Площадь застройки" in row["sources"]
    assert row["status"]=="ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ"

def test_property_as_object_excluded_from_crosscheck():
    findings=[
      {"document":"ПЗ.pdf","document_type":"ПЗ","page":46,"parameter_code":"AREA_BUILD",
       "parameter_name":"Площадь застройки","value":26.9,"unit":"м²",
       "object_hint":"Площадь застройки","semantic_anchor_name":"Площадь застройки",
       "confidence":.99,"core2_confidence":.99},
      {"document":"ПЗУ.pdf","document_type":"ПЗУ","page":18,"parameter_code":"AREA_BUILD",
       "parameter_name":"Площадь застройки","value":42.5,"unit":"м²",
       "object_hint":"Площадь застройки","semantic_anchor_name":"Площадь застройки",
       "confidence":.99,"core2_confidence":.99},
    ]
    assert build_cross_section_checks(findings)==[]
