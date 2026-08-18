
from pathlib import Path
from core.normative_intelligence import NormativeIntelligence
from core.engineering_verification_v2 import EngineeringVerification2
from core.checklist_compiler import compile_item

ROOT=Path(__file__).parent/"knowledge"

def test_object_profiles_distinguish_object_and_expected_properties():
    e=EngineeringVerification2(ROOT)
    x=e.classify_object("КТП-1250 кВА")
    assert x["object_type"]=="SUBSTATION"
    b=e.validate_binding("КТП-1250 кВА","POWER_INSTALLED","ИОС1")
    assert b["parameter_expected_for_object"]
    bad=e.validate_binding("Автомобильная дорога","TRANSFORMER_COUNT","ПЗУ")
    assert not bad["parameter_expected_for_object"]

def test_evidence_confidence_is_evidence_based():
    e=EngineeringVerification2(ROOT)
    weak=e.evidence_confidence([{"section":"ПЗ"}],False)
    strong=e.evidence_confidence([
        {"section":"ПЗ","page":10,"value":42.5,"structured":True},
        {"section":"ПЗУ","page":15,"value":42.5,"structured":True},
    ],True)
    assert strong["evidence_confidence"]>weak["evidence_confidence"]
    assert strong["verification_status"] in {"Подтверждено автоматически","Предварительно соответствует"}

def test_normative_unverified_does_not_become_categorical():
    n=NormativeIntelligence(ROOT)
    assert n.requirements
    for req in n.requirements:
        if not req.get("paragraph"):
            assert n.legal_confidence(req)=="Требует верификации НТД"

def test_checklist_compiles_mandatory_documents_and_pp87_structure():
    a=compile_item({"question":"Проверить наличие справки об объектах культурного наследия"})
    assert a.rule_type=="mandatory_document"
    b=compile_item({"question":"Проверить обязательное содержание раздела по Постановлению №87"})
    assert b.rule_type=="section_structure"
