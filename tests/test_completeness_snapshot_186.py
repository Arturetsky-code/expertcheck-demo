from __future__ import annotations

import pandas as pd

from core.project_completeness import PROFILE_CAPITAL, build_matrix
from studio.pages.completeness import _document_types


def test_restored_snapshot_russian_document_type_column_is_detected():
    docs = pd.DataFrame([
        {"Файл": "ПЗ.pdf", "Тип документа": "ПЗ"},
        {"Файл": "ПЗУ.pdf", "Тип документа": "ПЗУ1"},
        {"Файл": "АР.pdf", "Тип документа": "АР1"},
        {"Файл": "КР.pdf", "Тип документа": "КР"},
        {"Файл": "ТХ.pdf", "Тип документа": "ТХ1"},
        {"Файл": "ПОС.pdf", "Тип документа": "ПОС"},
        {"Файл": "ООС.pdf", "Тип документа": "ООС"},
        {"Файл": "ПБ.pdf", "Тип документа": "ПБ"},
    ])
    types = _document_types(docs)
    assert "ПЗ" in types
    assert "ПЗУ1" in types
    matrix = build_matrix(types, PROFILE_CAPITAL)
    by_code = {row["Код"]: row for row in matrix}
    assert by_code["ПЗ"]["Обнаружен"] == "Да"
    assert by_code["ПЗУ"]["Обнаружен"] == "Да"
    assert by_code["АР"]["Обнаружен"] == "Да"
    assert by_code["КР"]["Обнаружен"] == "Да"
    assert by_code["ТХ"]["Обнаружен"] == "Да"
    assert by_code["ПОС"]["Обнаружен"] == "Да"
    assert by_code["ООС"]["Обнаружен"] == "Да"
    assert by_code["ПБ"]["Обнаружен"] == "Да"
