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


def test_abbreviation_is_merged_only_when_unambiguous():
    rows, audit = reconcile_register([
        finding("4.18", "Комплектная трансформаторная подстанция", "ПЗ"),
        finding("", "КТП", "ИОС1"),
    ])
    assert len(rows) == 1
    assert rows[0]["Способ идентификации"] in {"exact_position", "abbreviation"}
    assert any(row.get("identity_method") == "abbreviation" for row in audit)


def test_different_positions_never_merge_even_with_same_name():
    rows, _ = reconcile_register([
        finding("2.1.1", "Насосная станция", "ПЗ"),
        finding("2.1.2", "Насосная станция", "ПЗ"),
    ])
    assert len(rows) == 2


def test_quantity_conflict_uses_priority_and_is_visible():
    rows, _ = reconcile_register([
        finding("5.1", "Резервуары", "ПЗ", quantity=3, quantity_evidence="3 шт."),
        finding("5.1", "Резервуары", "ПЗУ2", quantity=2, quantity_evidence="2 шт.", general_plan_explication=True),
    ])
    row = rows[0]
    assert row["Количество"] == 3
    assert row["Статус количества"] == "Требует проверки"
    assert row["Источник количества"] == "ПЗ"
    assert "количество" in row["Конфликты"]


def test_default_quantity_is_marked_as_inferred():
    rows, _ = reconcile_register([finding("6.1", "Здание лаборатории", "ПЗ")])
    assert rows[0]["Количество"] == 1
    assert rows[0]["Статус количества"] == "Не указано — принято 1"
    assert rows[0]["Уверенность количества"] < 0.5
