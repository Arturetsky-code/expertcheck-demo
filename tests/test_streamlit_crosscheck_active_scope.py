from types import SimpleNamespace

import pandas as pd

from core.project_assembly import filter_comparisons_by_keys, object_key, selected_keys
from studio.pages.checks import _active_comparisons


def _row(position, name, include):
    row = {
        "Позиция по ГП": position,
        "Наименование объекта": name,
        "Включить": include,
    }
    row["Ключ"] = object_key(row)
    return row


def test_cross_section_page_uses_confirmed_assembly_not_raw_candidates():
    # Two complex/group rows were manually excluded; their children remain active.
    decisions = [
        _row("4", "Площадка дробильно-сортировочного комплекса", False),
        _row("4.2", "Технологический комплекс", False),
        _row("4.2.1", "Оборудование дробильного комплекса", True),
        _row("4.5", "Компрессорная", True),
    ]
    all_checks = pd.DataFrame([
        {"object": r["Наименование объекта"], "genplan_position": r["Позиция по ГП"], "status": "СОВПАДАЕТ"}
        for r in decisions
    ])
    active_checks = pd.DataFrame(filter_comparisons_by_keys(
        all_checks.to_dict("records"), decisions, selected_keys(decisions)
    ))
    ctx = SimpleNamespace(data=(None, None, all_checks, None, None, active_checks, None))
    displayed = _active_comparisons(ctx)
    assert displayed is active_checks
    assert set(displayed["genplan_position"]) == {"4.2.1", "4.5"}
    assert len(all_checks) == 4
    # The retained compressor mismatch must not be lost by filtering.
    assert "Компрессорная" in set(displayed["object"])


def test_cross_section_page_remains_empty_when_every_object_is_excluded():
    complete = pd.DataFrame([{"object": "Исключённый объект", "status": "СОВПАДАЕТ"}])
    active = complete.iloc[0:0].copy()
    ctx = SimpleNamespace(data=(None, None, complete, None, None, active, None))
    assert _active_comparisons(ctx).empty
    assert len(complete) == 1
