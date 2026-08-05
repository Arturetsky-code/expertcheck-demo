from pathlib import Path
from core.checklist_engine import ChecklistEngine


def test_checklists_are_separate_workspace():
    root=Path(__file__).resolve().parents[1]
    text=(root/'studio'/'pages'/'__init__.py').read_text(encoding='utf-8')
    assert "'Межраздельная сверка'" in text
    assert "'Чек-листы'" in text
    assert "'Проверки'" not in text


def test_checklist_catalog_supports_independent_selection():
    root=Path(__file__).resolve().parents[1]
    engine=ChecklistEngine(root/'knowledge'/'checklist_catalog.json')
    assert engine.items
    assert engine.checklist_files()
    assert engine.sections()
