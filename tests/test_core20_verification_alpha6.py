from __future__ import annotations

from core20.model import CanonicalProject, Evidence, Requirement
from core20.verification import VerificationEngine20


def _normative_requirement(
    project: CanonicalProject,
    *,
    rid: str,
    text: str,
    source: str,
    paragraph: str,
    route: list[str],
    check_kind: str = "STRUCTURE",
    verified: bool = True,
    applicable=None,
    evidence_ids=None,
    parameter_code: str = "",
    required_value=None,
    unit: str = "",
    categorical: bool = False,
):
    project.add_requirement(Requirement(
        requirement_id=rid,
        domain="normative",
        text=text,
        applicable=applicable,
        expected_parameter_code=parameter_code,
        expected_evidence_route=route,
        evidence_ids=list(evidence_ids or []),
        evidence_level="L4",
        metadata={
            "verified_clause":verified,
            "source_reference":source,
            "paragraph":paragraph,
            "knowledge_kind":"LAW_REQUIREMENT",
            "normative_requirement_id":rid,
            "check_kind":check_kind,
            "required_value":required_value,
            "unit":unit,
            "categorical_conclusion_allowed":categorical,
        },
    ))


def _project(name: str, inventory: list[dict]) -> CanonicalProject:
    return CanonicalProject(
        project_id=f"PRJ-{name}",
        name=name,
        metadata={
            "document_inventory":inventory,
            "document_inventory_complete":True,
        },
    )


def test_pp87_pzu_complete_is_independently_verified():
    project=_project("industrial",[
        {"document":"Раздел ПД №2_ПЗУ1.pdf","section":"ПЗУ","page_count":40},
        {"document":"Раздел ПД №2_ПЗУ2.pdf","section":"ПЗУ","page_count":8},
    ])
    _normative_requirement(
        project,
        rid="PP87-CLAUSE-12-PZU",
        text="Раздел ПЗУ должен содержать текстовую и графическую части.",
        source="Постановление Правительства РФ от 16.02.2008 № 87",
        paragraph="п. 12",
        route=["ПЗУ"],
    )
    result=VerificationEngine20(project).run()
    row=result["decision_rows"][0]
    assert row["kind"]=="VERIFIED_OK"
    assert row["automatic_verdict_eligible"] is True
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_STRUCTURE_VERIFIED"
    assert row["metadata"]["observed_document_roles"]==["GRAPHIC_PART","TEXT_PART"]
    assert result["normative_auto"]==1
    assert result["normative_structure_auto"]==1


def test_pp87_ar_complete_is_project_name_independent():
    for name in ("tailings-storage","boiler-house","road-project"):
        project=_project(name,[
            {"document":"АР1 Текстовая часть.pdf","section":"АР","page_count":20},
            {"document":"АР2 Графическая часть.pdf","section":"АР","page_count":12},
        ])
        _normative_requirement(
            project,
            rid="PP87-CLAUSE-13-AR",
            text="Раздел АР должен содержать текстовую и графическую части.",
            source="Постановление Правительства РФ от 16.02.2008 № 87",
            paragraph="п. 13",
            route=["АР"],
        )
        row=VerificationEngine20(project).run()["decision_rows"][0]
        assert row["kind"]=="VERIFIED_OK", (name,row)
        assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_STRUCTURE_VERIFIED"


def test_missing_structural_part_is_review_not_false_finding():
    project=_project("industrial",[
        {"document":"Раздел ПД №2_ПЗУ1.pdf","section":"ПЗУ","page_count":40},
    ])
    _normative_requirement(
        project,
        rid="PP87-CLAUSE-12-PZU",
        text="Раздел ПЗУ должен содержать текстовую и графическую части.",
        source="Постановление Правительства РФ от 16.02.2008 № 87",
        paragraph="п. 12",
        route=["ПЗУ"],
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["automatic_verdict_eligible"] is False
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_STRUCTURE_PART_MISSING"
    assert row["metadata"]["missing_document_roles"]==["GRAPHIC_PART"]


def test_unverified_norm_is_always_fail_closed():
    project=_project("tailings",[
        {"document":"ГТ.pdf","section":"ГТ","page_count":120},
    ])
    _normative_requirement(
        project,
        rid="HYDRO-UNVERIFIED-1",
        text="Гребень дамбы должен иметь требуемую отметку.",
        source="СП требуется определить",
        paragraph="",
        route=["ГТ"],
        verified=False,
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="SYSTEM_LIMITATION"
    assert row["automatic_verdict_eligible"] is False
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_CLAUSE_NOT_VERIFIED"


def test_verified_clause_without_applicability_is_review():
    project=_project("unknown-project",[])
    _normative_requirement(
        project,
        rid="LAW-X-1",
        text="Проверяемое требование.",
        source="СП 1.00000",
        paragraph="п. 1.1",
        route=["ГТ"],
        verified=True,
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_APPLICABILITY_NOT_PROVEN"


def test_explicit_not_applicable_becomes_informational():
    project=_project("road",[
        {"document":"АД.pdf","section":"АД","page_count":30},
    ])
    _normative_requirement(
        project,
        rid="LAW-X-2",
        text="Требование к иному типу объекта.",
        source="СП 2.00000",
        paragraph="п. 2.1",
        route=["АД"],
        verified=True,
        applicable=False,
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="INFORMATIONAL"
    assert row["automatic_verdict_eligible"] is False
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_NOT_APPLICABLE"


def test_verified_numeric_norm_requires_categorical_permission():
    project=_project("boiler",[
        {"document":"ТХ.pdf","section":"ТХ","page_count":50},
    ])
    project.add_evidence(Evidence(
        evidence_id="E1",
        document_name="ТХ.pdf",
        section="ТХ",
        page=20,
        fragment="Компрессор принят с рабочим давлением 0,8 МПа.",
        addressable=True,
        trusted=True,
    ))
    _normative_requirement(
        project,
        rid="LAW-PRESSURE-1",
        text="Рабочее давление должно составлять 0,8 МПа.",
        source="СП 3.00000",
        paragraph="п. 3.1",
        route=["ТХ"],
        check_kind="VALUE",
        verified=True,
        evidence_ids=["E1"],
        parameter_code="PRESSURE",
        required_value=0.8,
        unit="МПа",
        categorical=False,
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="REVIEW_QUESTION"
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_CATEGORICAL_CONCLUSION_BLOCKED"


def test_verified_numeric_norm_can_close_when_contract_allows():
    project=_project("boiler",[
        {"document":"ТХ.pdf","section":"ТХ","page_count":50},
    ])
    project.add_evidence(Evidence(
        evidence_id="E1",
        document_name="ТХ.pdf",
        section="ТХ",
        page=20,
        fragment="Компрессор принят с рабочим давлением 0,8 МПа.",
        addressable=True,
        trusted=True,
    ))
    _normative_requirement(
        project,
        rid="LAW-PRESSURE-2",
        text="Рабочее давление должно составлять 0,8 МПа.",
        source="СП 3.00000",
        paragraph="п. 3.2",
        route=["ТХ"],
        check_kind="VALUE",
        verified=True,
        evidence_ids=["E1"],
        parameter_code="PRESSURE",
        required_value=0.8,
        unit="МПа",
        categorical=True,
    )
    row=VerificationEngine20(project).run()["decision_rows"][0]
    assert row["kind"]=="VERIFIED_OK"
    assert row["automatic_verdict_eligible"] is True
    assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_TYPED_VALUE_MATCH"
