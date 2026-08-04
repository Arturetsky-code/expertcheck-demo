from __future__ import annotations
from pathlib import Path
from .catalogs import KnowledgeRegistry
from .confidence import calculate_confidence


def analyze_uploaded_core(files, config_dir):
    """Compatibility pipeline: legacy extraction + Core 2.0 enrichment.

    This keeps the existing UI operational while catalogs and engines migrate in stages.
    """
    from legacy_analyzer import analyze_uploaded as legacy_analyze
    findings, comparisons, documents = legacy_analyze(files, config_dir)
    root = Path(config_dir)
    knowledge = KnowledgeRegistry(root / "knowledge")
    for item in findings:
        score, factors = calculate_confidence(
            genplan_match=bool(item.get("genplan_position")),
            exact_name=item.get("object_hint") not in {None, "", "Не определён"},
            table_recognized="таблиц" in str(item.get("match_method", "")).lower() or "ТЭП" in str(item.get("structural_zone", "")),
            unit_match=bool(item.get("unit")),
            legacy_score=item.get("confidence"),
        )
        item["core2_confidence"] = score
        item["confidence_factors"] = factors
        item["core_version"] = "2.0-alpha"
    for item in comparisons:
        item["core_version"] = "2.0-alpha"
    for doc in documents:
        doc["core_version"] = "2.0-alpha"
        doc["knowledge_summary"] = knowledge.summary()
    return findings, comparisons, documents
