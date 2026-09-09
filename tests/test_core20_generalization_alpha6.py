from __future__ import annotations

from pathlib import Path

from core20.model import CanonicalProject, Requirement
from core20.verification import VerificationEngine20


FORBIDDEN_PROJECT_LITERALS=(
    "тест 77",
    "золото дельмачик",
    "test 77",
)


def test_core20_contains_no_control_project_literals():
    root=Path(__file__).resolve().parents[1] / "core20"
    violations=[]
    for path in root.glob("*.py"):
        text=path.read_text(encoding="utf-8").casefold()
        for literal in FORBIDDEN_PROJECT_LITERALS:
            if literal in text:
                violations.append(f"{path.name}: {literal}")
    assert violations==[]


def _pp87_project(name: str) -> CanonicalProject:
    project=CanonicalProject(
        project_id=f"PRJ-{name}",
        name=name,
        metadata={
            "document_inventory":[
                {"document":"ПЗУ1.pdf","section":"ПЗУ","page_count":20},
                {"document":"ПЗУ2.pdf","section":"ПЗУ","page_count":7},
            ],
            "document_inventory_complete":True,
        },
    )
    project.add_requirement(Requirement(
        requirement_id="PP87-CLAUSE-12-PZU",
        domain="normative",
        text="Раздел ПЗУ должен содержать текстовую и графическую части.",
        expected_evidence_route=["ПЗУ"],
        evidence_level="L4",
        metadata={
            "verified_clause":True,
            "source_reference":"Постановление Правительства РФ от 16.02.2008 № 87",
            "paragraph":"п. 12",
            "knowledge_kind":"LAW_REQUIREMENT",
            "normative_requirement_id":"PP87-CLAUSE-12-PZU",
            "check_kind":"STRUCTURE",
        },
    ))
    return project


def test_normative_decision_is_invariant_to_project_name_and_industry_label():
    decisions=[]
    for name in ("Промышленный объект","Хвостохранилище","Котельная","Автомобильная дорога"):
        row=VerificationEngine20(_pp87_project(name)).run()["decision_rows"][0]
        decisions.append((row["kind"],row["metadata"]["canonical_reason_code"]))
    assert len(set(decisions))==1
    assert decisions[0]==("VERIFIED_OK","NORMATIVE_STRUCTURE_VERIFIED")


def test_unknown_industry_specific_norm_never_becomes_auto_from_project_name():
    for name in ("Хвостохранилище","Автомобильная дорога","Котельная"):
        project=CanonicalProject(
            project_id=f"PRJ-{name}",
            name=name,
            metadata={
                "document_inventory":[{"document":"Профильный раздел.pdf","section":"ПРОФИЛЬ","page_count":30}],
                "document_inventory_complete":True,
            },
        )
        project.add_requirement(Requirement(
            requirement_id="DOMAIN-NORM-UNKNOWN",
            domain="normative",
            text="Отраслевое требование, нормативный пункт которого ещё не верифицирован.",
            expected_evidence_route=["ПРОФИЛЬ"],
            evidence_level="L4",
            metadata={
                "verified_clause":False,
                "source_reference":"",
                "paragraph":"",
                "knowledge_kind":"LAW_REQUIREMENT",
                "check_kind":"SEMANTIC",
            },
        ))
        row=VerificationEngine20(project).run()["decision_rows"][0]
        assert row["kind"]=="SYSTEM_LIMITATION"
        assert row["automatic_verdict_eligible"] is False
        assert row["metadata"]["canonical_reason_code"]=="NORMATIVE_CLAUSE_NOT_VERIFIED"
