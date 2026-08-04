from pathlib import Path
from core.catalogs import KnowledgeRegistry
from core.table_engine import TableEngine
from core.semantic_engine import object_similarity
from core.quality import build_quality_summary

root = Path(__file__).resolve().parent
registry = KnowledgeRegistry(root / "knowledge")
engine = TableEngine(
    registry.load_json("core/table_catalog.json", []),
    registry.load_json("core/parameter_catalog.json", []),
)
text = """
Технико-экономические показатели
Наименование показателя
Единица измерения
Значение
Общая площадь
м²
86,6
Площадь застройки м² 71,2
"""
candidates = engine.detect(text, "ПЗ")
assert candidates, "Таблица ТЭП не распознана"
assert candidates[0].structured_rows, "Строки ТЭП не восстановлены"
score, reasons = object_similarity(
    "4.14 Насосная станция производственно-противопожарного водоснабжения",
    "Насосная ППВ",
    "4.14",
    "4.14",
)
assert score == 1.0 and reasons
quality = build_quality_summary([
    {"core2_confidence": 0.9, "table_type": "TAB-TEP-PZ", "semantic_match_score": 1.0, "object_hint": "Насосная", "match_method": "table"}
])
assert quality["Высокая уверенность"] == 1
print("ExpertCheck Core 2.0 Alpha 4 smoke test: OK")
print("Structured rows:", [row.to_dict() for row in candidates[0].structured_rows])
