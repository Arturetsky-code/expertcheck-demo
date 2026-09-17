from core25.contracts import Evidence25
from core25.evidence import is_canonical_evidence, qualify_evidence
from core25.routing import VerificationRoute
from core25.contracts import Scope


def test_table_of_contents_entry_is_rejected_even_when_addressable():
    ev = Evidence25(
        evidence_id="TOC",
        document="ПЗ.pdf",
        page=2,
        fragment="5 Технологические решения ........ 45",
        addressable=True,
        source_kind="TABLE_OF_CONTENTS",
    )
    assert is_canonical_evidence(ev) is False


def test_real_page_fragment_is_canonical():
    ev = Evidence25(
        evidence_id="E1",
        document="ТХ.pdf",
        section="ТХ",
        page=18,
        fragment="Производительность дробилки составляет 500 т/ч.",
        addressable=True,
        source_kind="PAGE_TEXT",
    )
    assert is_canonical_evidence(ev) is True


def test_unaddressable_semantic_hit_is_rejected():
    ev = Evidence25(
        evidence_id="SEM",
        document="ТХ.pdf",
        page=None,
        fragment="500 т/ч",
        addressable=False,
        source_kind="SEMANTIC_SEARCH",
    )
    assert is_canonical_evidence(ev) is False


def test_heading_only_metadata_is_rejected():
    ev = Evidence25(
        evidence_id="H1",
        document="ПЗУ.pdf",
        page=10,
        fragment="3. Планировочная организация земельного участка",
        addressable=True,
        source_kind="PAGE_TEXT",
        metadata={"heading_only": True},
    )
    assert is_canonical_evidence(ev) is False


def test_qualify_evidence_filters_section_and_orders_structured_first():
    route = VerificationRoute(
        kind="TYPED_VALUE",
        scope=Scope.PROJECT_GLOBAL,
        expected_sections=("ТХ",),
        parameter_code="CAPACITY",
        requires_owner=False,
        requires_addressable_evidence=True,
        prefer_structured_source=True,
    )
    candidates = [
        Evidence25(evidence_id="P", document="ТХ.pdf", section="ТХ", page=8, fragment="Мощность 500 т/ч", addressable=True, source_kind="PAGE_TEXT"),
        Evidence25(evidence_id="T", document="ТХ.pdf", section="ТХ", page=9, table_id="1", row_id="3", cell_id="2", fragment="500 т/ч", addressable=True, source_kind="TABLE_CELL"),
        Evidence25(evidence_id="A", document="АР.pdf", section="АР", page=5, fragment="500 т/ч", addressable=True, source_kind="PAGE_TEXT"),
    ]
    qualified = qualify_evidence(candidates, route)
    assert [item.evidence_id for item in qualified] == ["T", "P"]
