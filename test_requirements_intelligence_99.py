from core.assignment_compliance import compare_requirements, TYPE_VALUE, TYPE_SET, _split_requirement_atoms
from core.normative_validity import NormativeValidityChecker
from core.normative_requirement_analyzer import NormativeRequirementAnalyzer, _extract_cited_clause


def test_assignment_numeric_without_owner_cannot_create_deviation():
    req=[{"requirement_id":"A","requirement_type":TYPE_VALUE,"requirement_text":"Объем кузова 32 м3","parameter_code":"BODY_VOLUME","required_value":32.0,"unit":"м3","object_name":""}]
    findings=[{"document":"ПЗ.pdf","page":1,"parameter_code":"BODY_VOLUME","value":20.0,"object_hint":"Автосамосвал другой"}]
    row=compare_requirements(req,findings,[])[0]
    assert row["status"]=="Требует проверки"
    assert "владелец" in row["decision_basis"].lower()


def test_assignment_set_comparison_uses_expected_appendix_objects():
    req=[{"requirement_id":"A","requirement_type":TYPE_SET,"requirement_text":"Состав объектов по приложению 1","expected_objects":[{"position":"4.1","name":"Подпорная стена"},{"position":"4.4","name":"Операторская"}]}]
    registry=[{"Позиция по ГП":"4.1","Наименование объекта":"Подпорная стена"},{"Позиция по ГП":"4.4","Наименование объекта":"Операторская"}]
    row=compare_requirements(req,[],registry)[0]
    assert row["status"]=="Соответствует заданию"


def test_subclause_split_does_not_break_m3_sentence():
    text="1. Подвоз автосамосвалами, объемом кузова 32 м3. Выгрузка производится на площадку. 2. Подача погрузчиками."
    parts=_split_requirement_atoms(text)
    assert any("32 м3. Выгрузка" in p for p in parts)
    assert len(parts)==2


def test_normative_parser_rejects_partial_snip_noise(tmp_path):
    checker=NormativeValidityChecker(tmp_path)
    refs=checker.extract_from_text("Общие требования СНиП от 23. Текст. СНиП 2.03.11-85 применяется.")
    assert "СНиП от" not in refs
    assert any("2.03.11-85" in x for x in refs)


def test_clause_is_bound_only_when_explicitly_attached():
    assert _extract_cited_clause("согласно п. 4.3 СП 14.13330.2018 применить карту", "СП 14.13330.2018")=="4.3"
    assert _extract_cited_clause("СП 1.13130.2020 приведён в перечне. Далее п. 2 другой нормы", "СП 1.13130.2020")==""


def test_bibliography_reference_is_not_requirement(tmp_path):
    analyzer=NormativeRequirementAnalyzer(tmp_path)
    rows=analyzer.analyze_page("ПЗ.pdf",1,"Перечень НТД: СП 1.13130.2020. СП 2.13130.2020.")
    assert rows==[]
