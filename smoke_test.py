from pathlib import Path
from core.selfcheck import deployment_status
from core.catalogs import KnowledgeRegistry
from core.table_engine import TableEngine
from core.semantic_engine import object_similarity

ROOT = Path(__file__).resolve().parent
status = deployment_status(ROOT)
assert status["ok"], status
registry = KnowledgeRegistry(ROOT / "knowledge")
summary = registry.summary()
assert summary["objects"] > 0 and summary["parameters"] > 0 and summary["tables"] > 0, summary
engine = TableEngine(registry.load_json("core/table_catalog.json"))
assert engine.detect("Технико-экономические показатели\nНаименование показателя\nЕдиница измерения\nЗначение\nОбщая площадь м2 86,6")
score, reasons = object_similarity("4.14 Насосная ППВ", "Насосная станция ППВ", "4.14", "4.14")
assert score == 1.0 and reasons
print("ExpertCheck Core 2.0 Alpha 3: OK", summary)
