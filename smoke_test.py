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

# Core 2.1 DEM smoke test
from core.dem import build_dem
from core.validation import ValidationEngine
from core.relations import RelationEngine
from core.model_quality import calculate_model_quality

_demo_findings = [
    {"parameter_code":"OBJECT_ENTRY","value_text":"Насосная станция ППВ","object_hint":"Насосная станция ППВ","genplan_position":"4.14","document_type":"ПЗ","value":1},
    {"parameter_code":"TOTAL_AREA","parameter_name":"Общая площадь","value":86.6,"value_text":"86,6","unit":"м²","object_hint":"Насосная ППВ","semantic_anchor_name":"Насосная станция ППВ","semantic_anchor_position":"4.14","document_type":"АР","document":"АР1.pdf","page":18,"core2_confidence":0.92},
]
_demo_dem = build_dem(_demo_findings, "Smoke project")
_demo_issues = ValidationEngine().validate(_demo_dem)
_demo_relations = RelationEngine().build(_demo_dem)
_demo_quality = calculate_model_quality(_demo_dem, _demo_issues)
assert len(_demo_dem.objects) == 1
assert _demo_dem.metadata["value_count"] == 1
assert 0 <= _demo_quality["model_quality_index"] <= 1
print("Core 2.1 DEM smoke test: OK")
