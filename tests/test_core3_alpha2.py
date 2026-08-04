from core.normalization import canonical_parameter, normalize_measure
from core.cross_source_consistency import build_pdf_xml_checks


def test_parameter_normalization():
    item = canonical_parameter("площадь застройки")
    assert item.code == "AREA_BUILD"
    assert item.unit == "м²"
    assert normalize_measure("055")[0] == "м²"


def test_pdf_xml_mismatch_check():
    findings = [
        {
            "source_kind": "xml", "parameter_code": "AREA_BUILD", "parameter_name": "Площадь застройки",
            "value_num": 100.0, "unit": "м²", "object_hint": "Административный корпус",
            "document": "pz.xml", "section": "ПЗ XML", "value_text": "100", "page": 0,
        },
        {
            "source_kind": "pdf", "parameter_code": "AREA_BUILD", "parameter_name": "Площадь застройки",
            "value": 101.0, "unit": "м²", "object_hint": "Административный корпус",
            "document": "AR.pdf", "section": "АР1", "document_type": "АР1", "value_text": "101 м²", "page": 5,
            "context": "Административный корпус, площадь застройки 101 м²",
        },
    ]
    rows = build_pdf_xml_checks(findings)
    assert len(rows) == 1
    assert rows[0]["status"] == "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ"
    assert rows[0]["category"] == "Согласованность PDF ↔ XML"
