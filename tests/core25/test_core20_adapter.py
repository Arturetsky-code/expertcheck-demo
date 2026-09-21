from core20.model import Evidence, Requirement
from core25.adapters.core20 import adapt_evidence, adapt_requirement
from core25.contracts import Domain, Scope
from core25.requirement_engine import normalize_assignment_requirement


def test_core20_assignment_requirement_preserves_route_and_scope():
    old = Requirement(
        requirement_id="A-12",
        domain="assignment",
        text="Продолжительность смены – 12 часов",
        expected_parameter_code="SHIFT_DURATION",
        expected_evidence_route=["ТХ"],
        verification_kind="VALUE",
        metadata={"required_value": 12.0, "unit": "час", "scope": "PROJECT_GLOBAL"},
    )
    new = adapt_requirement(old)
    assert new.requirement_id == "A-12"
    assert new.domain is Domain.ASSIGNMENT
    assert new.scope is Scope.PROJECT_GLOBAL
    assert new.parameter_code == "SHIFT_DURATION"
    assert new.expected_sections == ("ТХ",)
    assert new.required_value == 12.0
    assert new.unit == "час"


def test_core20_evidence_keeps_canonical_address():
    old = Evidence(
        evidence_id="E1",
        document_name="ТХ.pdf",
        section="ТХ",
        page=7,
        fragment="Продолжительность смены 12 часов",
        addressable=True,
        trusted=True,
    )
    new = adapt_evidence(old)
    assert new.document == "ТХ.pdf"
    assert new.page == 7
    assert new.fragment.startswith("Продолжительность")
    assert new.addressable is True
    assert new.trusted is True


def test_raw_assignment_requirement_normalizes_to_same_contract():
    raw = {
        "requirement_id": "A-22",
        "requirement_text": "Производственная мощность 1 600 тыс. тонн в год",
        "requirement_type": "VALUE",
        "parameter_code": "ANNUAL_CAPACITY",
        "required_value": 1600.0,
        "unit": "тыс. т/год",
        "requirement_scope": "PROJECT_GLOBAL",
        "expected_sections": ["ТХ", "ПЗ"],
        "document": "Задание.pdf",
        "page": 5,
    }
    req = normalize_assignment_requirement(raw)
    assert req.requirement_id == "A-22"
    assert req.domain is Domain.ASSIGNMENT
    assert req.scope is Scope.PROJECT_GLOBAL
    assert req.parameter_code == "ANNUAL_CAPACITY"
    assert req.expected_sections == ("ТХ", "ПЗ")
    assert req.source_document == "Задание.pdf"
    assert req.source_page == 5


def test_core20_topic_alignment_keeps_stable_baseline_contract():
    from core20.evidence_quality_1012 import topic_alignment

    result = topic_alignment(
        {"topic": "ограждение", "keywords": ["производительность"]},
        "Проектом предусмотрено ограждение площадки.",
    )

    assert result["eligible"] is False
    assert len(result["required_anchors"]) == 2
