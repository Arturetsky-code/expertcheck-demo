
from pathlib import Path
from core.normative_validity import NormativeValidityChecker
from core.automatic_review import AutomaticProjectReview, canonical_section

ROOT=Path(__file__).parent/"knowledge"

def test_pp87_is_curated_current():
    e=NormativeValidityChecker(ROOT)
    x=e.check("Постановление Правительства РФ № 87",document="ПЗ.pdf",page=5,context="в соответствии с ПП РФ №87")
    assert x["status"]=="Действует"
    assert x["official_source_kind"]=="PRAVO"

def test_unknown_sp_is_not_declared_invalid_or_current():
    e=NormativeValidityChecker(ROOT)
    x=e.check("СП 999.99999.2020",document="ПЗ.pdf",page=7,context="Расчет выполнен по СП 999.99999.2020")
    assert x["status"]=="Требует верификации"
    assert x["impact_risk"]=="Высокий"

def test_snip_gets_edition_risk_not_false_repeal():
    e=NormativeValidityChecker(ROOT)
    x=e.check("СНиП 2.01.01-82")
    assert x["status"]=="Возможна устаревшая редакция"
    assert x["status"]!="Утратил силу"

def test_extract_multiple_references():
    e=NormativeValidityChecker(ROOT)
    refs=e.extract_from_text("Решения приняты по СП 20.13330.2016 и ГОСТ Р 21.101-2020, а состав по Постановлению Правительства РФ № 87.")
    assert any("СП 20.13330.2016" in x for x in refs)
    assert any("ГОСТ Р 21.101-2020" in x for x in refs)
    assert any("87" in x and "Постанов" in x for x in refs)

def test_document_type_canonicalization():
    assert canonical_section("Раздел 2. Схема планировочной организации земельного участка")=="ПЗУ"
    assert canonical_section("Система электроснабжения ИОС1")=="ИОС1"

def test_automatic_programme_selects_present_checklists():
    e=AutomaticProjectReview(ROOT)
    docs=[
      {"Файл":"ПЗУ.pdf","Раздел":"Раздел 2. Схема планировочной организации земельного участка"},
      {"Файл":"ЭС.pdf","Раздел":"Система электроснабжения"},
    ]
    p=e.programme(docs,{"project_type":"производственный"})
    names={x["checklist"] for x in p}
    assert any("Ген.план" in x for x in names)
    assert any("Электрика" in x for x in names)


class FakeUpload:
    name="ПЗ.pdf"
    def getvalue(self): return b"x"

def test_page_text_normative_scan():
    e=NormativeValidityChecker(ROOT)
    def reader(data,name):
        return [(1,"Расчет выполнен по СП 999.99999.2020."),(2,"Состав проектной документации принят по Постановлению Правительства РФ № 87.")]
    rows=e.audit_uploaded_pdfs([FakeUpload()],reader)
    assert len(rows)>=2
    assert any(x["page"]==2 and x["status"]=="Действует" for x in rows)

def test_automatic_execute_without_manual_selection():
    e=AutomaticProjectReview(ROOT)
    docs=[{"Файл":"ЭС.pdf","Раздел":"Система электроснабжения"}]
    findings=[{"document":"ЭС.pdf","document_type":"ИОС1","parameter_code":"POWER_INSTALLED","parameter_name":"Мощность","value_text":"1250 кВА","context":"Установленная мощность 1250 кВА"}]
    result=e.execute(docs,[],findings,{"project_type":"производственный"})
    assert result["summary"]["automatic"] is True
    assert result["summary"]["checklists_run"]>=1
    assert result["summary"]["checks"]>=1
