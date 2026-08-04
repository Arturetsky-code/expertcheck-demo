from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .catalogs import KnowledgeRegistry
from .confidence import calculate_confidence
from .rule_engine import RuleEngine
from .semantic_engine import object_similarity
from .table_engine import TableEngine
from .quality import build_quality_summary
from .dem import build_dem
from .validation import ValidationEngine
from .relations import RelationEngine
from .model_quality import calculate_model_quality
from .knowledge_base import KnowledgeBase
from .risk_engine import calculate_engineering_risk
from .object_register_engine import build_registry
from .passport_engine import build_object_passports, passport_summary


def _best_table_by_page(files, legacy, table_engine: TableEngine, document_types: dict[str, str]) -> dict[tuple[str, int], dict[str, Any]]:
    """Распознаёт тип инженерной таблицы для каждой страницы документа.

    Возвращает только лучший кандидат на страницу, чтобы не перегружать находки
    конкурирующими классификациями.
    """
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for uploaded in files:
        try:
            pages = legacy.read_pdf(uploaded.getvalue(), uploaded.name)
        except Exception:
            continue
        for page_no, text in pages:
            candidates = table_engine.detect(text, document_types.get(uploaded.name, ""))
            if not candidates:
                continue
            best = candidates[0]
            result[(uploaded.name, page_no)] = {
                "table_type": best.table_type,
                "table_score": best.score,
                "table_evidence": "; ".join(best.evidence),
                "table_structured_rows": [row.to_dict() for row in best.structured_rows],
            }
    return result


def _semantic_anchors(findings: list[dict]) -> list[dict]:
    anchors: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in findings:
        if item.get("parameter_code") not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            continue
        name = str(item.get("object_hint") or item.get("value_text") or "").strip()
        position = str(item.get("genplan_position") or "").strip()
        if not name or name == "Не определён":
            continue
        key = (position, name.lower())
        if key in seen:
            continue
        seen.add(key)
        anchors.append({"name": name, "position": position})
    return anchors


def _enrich_semantics(findings: list[dict]) -> None:
    anchors = _semantic_anchors(findings)
    if not anchors:
        return
    for item in findings:
        if item.get("parameter_code") in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            continue
        source_name = str(item.get("object_hint") or "").strip()
        source_position = str(item.get("genplan_position") or "").strip()
        if not source_name or source_name == "Не определён":
            item["semantic_match_score"] = 0.0
            item["semantic_match_reasons"] = ["объект характеристики не определён"]
            continue
        best_score = -1.0
        best_anchor: dict[str, str] | None = None
        best_reasons: list[str] = []
        for anchor in anchors:
            score, reasons = object_similarity(
                source_name,
                anchor["name"],
                source_position,
                anchor["position"],
            )
            if score > best_score:
                best_score = score
                best_anchor = anchor
                best_reasons = reasons
        item["semantic_match_score"] = round(max(0.0, best_score), 3)
        item["semantic_match_reasons"] = best_reasons
        if best_anchor:
            item["semantic_anchor_name"] = best_anchor["name"]
            item["semantic_anchor_position"] = best_anchor["position"]


def _enrich_rules(comparisons: list[dict], registry: KnowledgeRegistry) -> None:
    rules = registry.load_rules()
    engine = RuleEngine(rules)
    by_parameter = {
        rule.get("parameter_code"): rule
        for rule in engine.rules
        if rule.get("rule_kind") == "comparison" and rule.get("parameter_code")
    }
    for item in comparisons:
        rule = by_parameter.get(item.get("parameter_code"))
        if not rule:
            item["rule_source"] = "legacy"
            continue
        item["rule_source"] = rule.get("pack", "core")
        item["knowledge_rule_code"] = rule.get("code", "")
        item["knowledge_rule_name"] = rule.get("name", "")
        if not item.get("check_code"):
            item["check_code"] = rule.get("code", "")
        if not item.get("explanation"):
            item["explanation"] = engine.explain(rule, {"values": item.get("document_values", "")})


def analyze_uploaded_core(files, config_dir):
    """Переходный конвейер Core 2.1 Alpha 1.

    Legacy Analyzer пока выполняет проверенную предметную логику извлечения.
    Core 2.1 дополнительно строит цифровую инженерную модель (DEM),
    валидирует её полноту, строит доказуемые связи и рассчитывает индекс качества модели.
    """
    import legacy_analyzer as legacy

    # Важно: legacy возвращает документы, находки, сравнения именно в таком порядке.
    documents, findings, comparisons = legacy.analyze_uploaded(files, config_dir)

    root = Path(config_dir)
    registry = KnowledgeRegistry(root / "knowledge")
    table_engine = TableEngine(
        registry.load_json("core/table_catalog.json", []),
        registry.load_json("core/parameter_catalog.json", []),
    )
    document_types = {str(doc.get("Файл", "")): str(doc.get("Раздел", doc.get("Тип документа", ""))) for doc in documents}
    page_tables = _best_table_by_page(files, legacy, table_engine, document_types)

    for item in findings:
        table_info = page_tables.get((item.get("document"), int(item.get("page") or 0)), {})
        item.update(table_info)
        score, factors = calculate_confidence(
            genplan_match=bool(item.get("genplan_position")),
            exact_name=item.get("object_hint") not in {None, "", "Не определён"},
            table_recognized=bool(table_info) or "таблиц" in str(item.get("match_method", "")).lower()
            or "тэп" in str(item.get("structural_zone", "")).lower(),
            unit_match=bool(item.get("unit")),
            legacy_score=item.get("confidence"),
        )
        item["core2_confidence"] = score
        item["confidence_factors"] = factors
        item["core_version"] = "2.3-sprint1-alpha2"

    _enrich_semantics(findings)
    _enrich_rules(comparisons, registry)
    knowledge_base = KnowledgeBase(root / "knowledge")
    for item in comparisons:
        knowledge_base.enrich_comparison(item)
        risk = calculate_engineering_risk(item)
        item["engineering_risk_score"] = risk["score"]
        item["engineering_risk_level"] = risk["level"]
        item["engineering_risk_reasons"] = risk["reasons"]

    # Реестр объектов строится отдельным движком и сопровождается журналом решений.
    object_registry, object_register_audit = build_registry(findings)
    object_passports = build_object_passports(object_registry, findings, comparisons)
    object_passport_summary = passport_summary(object_passports)

    # Цифровая инженерная модель строится только из извлечённых доказательств.
    dem = build_dem(findings, project_name="Новый проект")
    validation_issues = ValidationEngine().validate(dem)
    relations = RelationEngine().build(dem)
    model_quality = calculate_model_quality(dem, validation_issues)
    quality_summary = build_quality_summary(findings)

    summary = registry.summary()
    table_pages_by_doc: dict[str, int] = defaultdict(int)
    for filename, _page in page_tables:
        table_pages_by_doc[filename] += 1

    for item in comparisons:
        item["core_version"] = "2.3-sprint1-alpha2"
        item["dem_model_quality"] = model_quality.get("model_quality_index", 0.0)
    for item in findings:
        item["dem_object_count"] = dem.metadata.get("object_count", 0)
        item["dem_unassigned_values"] = dem.metadata.get("unassigned_value_count", 0)
    for doc in documents:
        doc["core_version"] = "2.3-sprint1-alpha2"
        doc["knowledge_summary"] = summary
        doc["evidence_base_summary"] = knowledge_base.summary()
        doc["quality_summary"] = quality_summary
        doc["dem_summary"] = dem.metadata
        doc["dem_model_quality"] = model_quality
        doc["dem_validation_issues"] = [issue.to_dict() for issue in validation_issues]
        doc["dem_relations"] = [relation.to_dict() for relation in relations]
        doc["object_registry_summary"] = {
            "registry_positions": len(object_registry),
            "physical_objects": sum(int(row.get("Количество", 1) or 1) for row in object_registry),
            "confirmed_by_multiple_sources": sum(1 for row in object_registry if int(row.get("Подтверждений", 0) or 0) >= 2),
            "requires_review": sum(1 for row in object_registry if "Требует" in str(row.get("Статус", ""))),
            "audit_candidates": len(object_register_audit),
        }
        doc["object_register_audit"] = object_register_audit
        doc["object_passports"] = [passport.to_dict() for passport in object_passports]
        doc["object_passport_summary"] = object_passport_summary
        doc["Распознано страниц с таблицами"] = table_pages_by_doc.get(doc.get("Файл", ""), 0)

    return documents, findings, comparisons
