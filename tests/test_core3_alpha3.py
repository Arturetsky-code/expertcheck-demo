from core.cross_section_consistency import build_cross_section_checks, section_family


def f(section, value, *, obj="Насосная станция ППВ", code="AREA_BUILD", pos="4.18", doc=None, confidence=0.95):
    return {
        "source_kind": "pdf",
        "parameter_code": code,
        "parameter_name": "Площадь застройки",
        "value": value,
        "unit": "м²",
        "object_hint": obj,
        "genplan_position": pos,
        "document_type": section,
        "section": section,
        "document": doc or f"{section}.pdf",
        "page": 3,
        "confidence": confidence,
        "core2_confidence": confidence,
    }


def test_section_family_parts_are_merged():
    assert section_family(f("АР1", 100)) == "АР"
    assert section_family(f("АР2", 100)) == "АР"
    assert section_family(f("ИОС1.1", 100)) == "ИОС1"


def test_cross_section_match():
    rows = build_cross_section_checks([f("ПЗ", 100), f("ПЗУ1", 100.05), f("АР2", 100.0)])
    assert len(rows) == 1
    assert rows[0]["status"] == "СОВПАДАЕТ"
    assert rows[0]["independent_section_count"] == 3


def test_cross_section_mismatch():
    rows = build_cross_section_checks([f("ПЗ", 100), f("АР1", 101)])
    assert rows[0]["status"] == "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ"
    assert rows[0]["difference"] == 1


def test_internal_section_conflict():
    rows = build_cross_section_checks([
        f("АР1", 100, doc="AR1.pdf"),
        f("АР2", 102, doc="AR2.pdf"),
        f("ПЗ", 100),
    ])
    assert rows[0]["status"] == "КОНФЛИКТ ВНУТРИ РАЗДЕЛА"
    assert "АР" in rows[0]["internal_conflict_sections"]


def test_same_names_different_positions_not_merged():
    rows = build_cross_section_checks([
        f("ПЗ", 100, obj="Резервуар", pos="1.1"),
        f("АР", 100, obj="Резервуар", pos="1.1"),
        f("ПЗ", 200, obj="Резервуар", pos="1.2"),
        f("АР", 200, obj="Резервуар", pos="1.2"),
    ])
    assert len(rows) == 2
    assert {r["genplan_position"] for r in rows} == {"1.1", "1.2"}


def test_unconfirmed_value_is_diagnostic_not_mismatch():
    rows = build_cross_section_checks([f("ТХ", 1600, code="CAPACITY")])
    assert rows[0]["status"] == "НЕДОСТАТОЧНО ДАННЫХ"
    assert "ПЗ" in rows[0]["missing_expected_documents"]
