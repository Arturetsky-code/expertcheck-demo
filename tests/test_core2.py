from pathlib import Path
from core.catalogs import KnowledgeRegistry
from core.semantic_engine import object_similarity
from core.table_engine import TableEngine

ROOT = Path(__file__).resolve().parents[1]

def test_catalogs_load():
    r = KnowledgeRegistry(ROOT / 'knowledge')
    s = r.summary()
    assert s['objects'] > 0
    assert s['parameters'] > 0
    assert s['tables'] > 0

def test_position_has_priority():
    score, _ = object_similarity('Насосная ППВ', 'Насосная станция', '4.14', '4.14')
    assert score == 1.0

def test_table_detection():
    r = KnowledgeRegistry(ROOT / 'knowledge')
    engine = TableEngine(r.load_json('core/table_catalog.json'))
    found = engine.detect('Технико-экономические показатели\nНаименование показателя\nЕдиница измерения\nЗначение\nОбщая площадь м2 86,6')
    assert found
