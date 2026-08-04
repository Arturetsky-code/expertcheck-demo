from core.register_reconciliation import reconcile_register


def finding(position, name, doc_type, **extra):
    row = {
        "parameter_code": "OBJECT_ENTRY" if doc_type == "ПЗ" else "OBJECT_CANDIDATE",
        "genplan_position": position,
        "value_text": name,
        "object_hint": name,
        "document_type": doc_type,
        "document": f"{doc_type}.pdf",
        "confidence": 0.95,
    }
    row.update(extra)
    return row


def test_reconciliation_is_domain_agnostic():
    rows, _ = reconcile_register([
        finding("1.1", "Резервуарный парк", "ПЗ"),
        finding("1.1", "Резервуарный парк", "ПЗУ2", general_plan_explication=True),
        finding("1.1", "Резервуарный парк", "ТХ1"),
    ])
    assert len(rows) == 1
    assert rows[0]["Статус консолидации"] == "Подтверждено тремя и более источниками"


def test_general_plan_missing_in_pz_is_flagged():
    rows, _ = reconcile_register([
        finding("7.4", "Трансформаторная подстанция", "ПЗУ2", general_plan_explication=True),
        finding("7.4", "КТП", "ИОС1"),
    ])
    assert rows[0]["В ПЗ"] is False
    assert rows[0]["В генплане"] is True
    assert rows[0]["Статус консолидации"] == "Есть на генплане — отсутствует в ПЗ"


def test_parent_and_child_are_not_merged():
    rows, _ = reconcile_register([
        finding("2.1", "Производственный комплекс", "ПЗ"),
        finding("2.1.1", "Насосная станция", "ПЗ"),
        finding("2.1.1", "Насосная станция", "ПЗУ2", general_plan_explication=True),
    ])
    assert {row["Позиция по ГП"] for row in rows} == {"2.1", "2.1.1"}
