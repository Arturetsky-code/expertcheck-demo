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
from .general_plan_engine import GeneralPlanRegisterEngine
from .general_plan_reconciliation import (
    anchor_findings_to_general_plan, build_general_plan_document_checks,
    build_general_plan_field_checks,
)
from .register_reconciliation import reconcile_register
from .project_profiles import ProjectProfileRegistry
from .xml_engine import XmlEngine
from .cross_source_consistency import build_pdf_xml_checks
from .cross_section_consistency import build_cross_section_checks
from .cross_section_verification import qualify_cross_section_verdicts, technology_proof_summary
from .object_semantics import enrich_findings_with_object_semantics, is_service_object_candidate, object_candidate_evidence
from .universal_object_discovery import discover_object_candidates
from .knowledge_engine import default_knowledge_engine
from .trusted_project_model import annotate_findings, filter_registry
from .cognitive_document_intelligence import CognitiveDocumentIntelligence
from .ai_pipeline import run_ai_pipeline, review_object_candidates, apply_object_reviews, discover_objects_from_scope_evidence
from .engineering_intelligence import apply_structure_guards, audit_mandatory_documents, scan_normative_references
from .object_gate import apply_hard_object_gate
from .project_object_recovery import recover_project_objects_from_uploaded
from .project_profile_87 import detect_pp87_profile
from .visual_document_intelligence import recover_text_from_scanned_pages
from .project_object_recovery import recover_project_objects_from_pages
from .evidence_graph import build_evidence_graph
from .normative_knowledge import NormativeKnowledgeLayer
from .normative_validity import NormativeValidityChecker
from .normative_requirement_analyzer import NormativeRequirementAnalyzer
from .normative_compliance_engine import NormativeComplianceEngine
from .automatic_review import AutomaticProjectReview
from .project_review_planner import build_review_plan
from .verification_core import domain_summary
from .report_quality_gate import validate_review_plan
from .fact_admission import assess_fact_admission
from .remark_learning import RemarkLearningEngine
from .learning_engine import apply_learning_examples
from .object_discovery_orchestrator import ensure_general_plan_registry_visibility, needs_object_recovery
from .composition_registry import build_composition_baseline, merge_baseline_with_registry
from .pz_complex_object_register import extract_pz_complex_object_register_from_uploaded, enforce_authoritative_pz_registry
from .engineering_review_engine import CrossSectionDependencyEngine
from .expert_practice_intelligence import ExpertPracticeIntelligence
from .entity_property_binding import annotate_findings as annotate_entity_property_bindings
from .assignment_compliance import extract_requirements as extract_assignment_requirements, compare_requirements as compare_assignment_requirements, summary as assignment_summary
from .project_understanding import build_project_object_model, understanding_quality
from .table_row_integrity import apply_table_row_integrity_guard
from .engineering_plausibility import apply_engineering_plausibility_guard, plausibility_review_questions
from .evidence_provenance import annotate_evidence_provenance
from .drawing_intelligence import annotate_drawing_evidence
from .drawing_intelligence_v2 import DrawingIntelligenceV2, drawing_graph_findings
from .finding_qualification import coverage_summary
from .directed_evidence import build_page_corpus, attach_directed_evidence, directed_evidence_facts
from .table_semantic_scope import annotate_table_semantic_scope
from .page_evidence_store import is_assignment_source
from .atomic_requirement_graph import build_atomic_requirement_graph
from .universal_project_fact_graph import build_universal_project_fact_graph
from .atomic_verification_engine import (
    aggregate_atomic_results, atomic_evidence_facts, atomic_summary, parent_assignment_summary,
    verify_atomic_requirements, verify_checklist_rows,
)
from .categorical_consistency import build_categorical_consistency_checks
from .coverage_matrix import build_coverage_matrix
from .coverage_acceleration import coverage_budget
from .project_snapshot import build_analysis_snapshot, corpus_fingerprint
from .evidence_reconstruction import reconstruct_high_value_evidence, sanitize_high_value_facts
from .semantic_evidence_engine import build_semantic_project_graph
try:
    from .universal_registry_extractor import UniversalRegistryExtractor
except ModuleNotFoundError:
    UniversalRegistryExtractor = None


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
        service, _ = is_service_object_candidate(item)
        strength, _ = object_candidate_evidence(item)
        if service or strength <= 0:
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


def analyze_uploaded_core(files, config_dir, progress_callback=None, ai_options=None):
    """Переходный конвейер Core 2.1 Alpha 1.

    Legacy Analyzer пока выполняет проверенную предметную логику извлечения.
    Core 2.1 дополнительно строит цифровую инженерную модель (DEM),
    валидирует её полноту, строит доказуемые связи и рассчитывает индекс качества модели.
    """
    import legacy_analyzer as legacy

    def progress(value: int, stage: str, detail: str = "") -> None:
        if progress_callback:
            try:
                progress_callback(max(0, min(100, int(value))), stage, detail)
            except Exception:
                pass

    ai_options = ai_options or {}
    semantic_level = str(ai_options.get("level") or "off").lower()
    semantic_judge_provider = ai_options.get("judge_provider") or ai_options.get("provider")
    semantic_critic_provider = ai_options.get("critic_provider") or ai_options.get("reviewer_provider")
    semantic_checkpoint = ai_options.get("semantic_checkpoint")
    if not isinstance(semantic_checkpoint, dict):
        semantic_checkpoint = {}
    review_mode = str(ai_options.get("review_mode") or "extended").lower()
    acceleration_budget = coverage_budget(review_mode, semantic_level)
    assignment_semantic_limit = acceleration_budget.assignment_semantic_limit
    initial_checklist_semantic_limit = acceleration_budget.initial_checklist_semantic_limit
    progress(3, "Подготовка комплекта", "Проверяем форматы и распределяем документы по обработчикам")

    # PDF обрабатываются legacy-движком, XML — отдельным версионным движком Core 3.0.
    pdf_files = [f for f in files if str(getattr(f, "name", "")).lower().endswith(".pdf")]
    xml_files = [f for f in files if str(getattr(f, "name", "")).lower().endswith(".xml")]
    if pdf_files:
        progress(10, "Извлечение данных", f"Обрабатываем PDF: {len(pdf_files)}")
        documents, findings, comparisons = legacy.analyze_uploaded(pdf_files, config_dir)
    else:
        documents, findings, comparisons = [], [], []
    progress(38, "Чтение XML", f"Структурированных файлов: {len(xml_files)}")
    xml_documents, xml_findings, xml_warnings = XmlEngine().parse_uploaded(xml_files)
    documents.extend(xml_documents)
    findings.extend(xml_findings)
    structure_guard_audit = apply_structure_guards(findings)
    object_gate_audit = apply_hard_object_gate(findings)
    enrich_findings_with_object_semantics(findings)
    trusted_object_audit = annotate_findings(findings)
    pdf_xml_checks = build_pdf_xml_checks(findings)
    cross_section_checks = build_cross_section_checks(findings)
    # Core 3.0 Alpha 3 формирует собственную сводную межраздельную сверку.
    # Legacy-проверки сохраняются, но дубли Core удаляются по коду/объекту/параметру.
    comparisons.extend(pdf_xml_checks)
    comparisons.extend(cross_section_checks)

    progress(48, "Нормализация", "Приводим объекты, характеристики и единицы к единой модели")
    root = Path(config_dir)
    registry = KnowledgeRegistry(root / "knowledge")
    table_engine = TableEngine(
        registry.load_json("core/table_catalog.json", []),
        registry.load_json("core/parameter_catalog.json", []),
    )
    document_types = {str(doc.get("Файл", "")): str(doc.get("Раздел", doc.get("Тип документа", ""))) for doc in documents}
    progress(52, "Реестр объектов", "Читаем экспликации генерального плана")
    pipeline_errors: list[dict[str, str]] = []
    try:
        gp_findings, general_plan_audit = GeneralPlanRegisterEngine().extract_uploaded(pdf_files, document_types)
    except Exception as exc:
        gp_findings, general_plan_audit = [], [{"decision": "error", "reason": str(exc)}]
        pipeline_errors.append({"stage": "general_plan", "error": str(exc)})
    findings.extend(gp_findings)
    general_plan_anchor_audit = anchor_findings_to_general_plan(findings, gp_findings)

    progress(57, "Реестр объектов", "Извлекаем официальные объектные таблицы")
    if UniversalRegistryExtractor is not None:
        try:
            universal_registry_findings, universal_registry_audit = UniversalRegistryExtractor().extract_uploaded(
                pdf_files, document_types, legacy.read_pdf
            )
            findings.extend(universal_registry_findings)
        except Exception as exc:
            universal_registry_findings, universal_registry_audit = [], [{"decision": "error", "reason": str(exc)}]
            pipeline_errors.append({"stage": "universal_registry", "error": str(exc)})
    else:
        universal_registry_findings, universal_registry_audit = [], [{
            "decision": "пропущено",
            "reason": "Модуль universal_registry_extractor.py отсутствует в репозитории"
        }]

    progress(62, "Структурный анализ", "Связываем объекты и ТЭП внутри строк таблиц")
    try:
        cognitive_findings, cognitive_page_structures, cognitive_audit = CognitiveDocumentIntelligence().extract_uploaded(
            pdf_files, document_types
        )
    except Exception as exc:
        cognitive_findings, cognitive_page_structures, cognitive_audit = [], [], [{"decision": "error", "reason": str(exc)}]
        pipeline_errors.append({"stage": "cognitive_document_intelligence", "error": str(exc)})
    findings.extend(cognitive_findings)

    progress(66, "Структурный анализ", "Определяем наиболее надёжные таблицы и источники")
    try:
        page_tables = _best_table_by_page(pdf_files, legacy, table_engine, document_types)
    except Exception as exc:
        page_tables = {}
        pipeline_errors.append({"stage": "table_ranking", "error": str(exc)})

    progress(67, "Состав проекта", "Читаем официальный перечень зданий и сооружений в составе сложного объекта ПЗ")
    try:
        pz_complex_objects, pz_complex_object_audit = extract_pz_complex_object_register_from_uploaded(pdf_files, document_types)
        findings.extend(pz_complex_objects)
    except Exception as exc:
        pz_complex_objects, pz_complex_object_audit = [], [{"decision":"error","reason":str(exc)}]
        pipeline_errors.append({"stage": "pz_complex_object_register", "error": str(exc)})

    progress(68, "Состав проекта", "Дополняем состав по идентификационным признакам и формулировкам проектных решений")
    try:
        recovered_objects, object_recovery_audit = recover_project_objects_from_uploaded(pdf_files, document_types)
        findings.extend(recovered_objects)
    except Exception as exc:
        recovered_objects, object_recovery_audit = [], [{"decision":"error","reason":str(exc)}]
        pipeline_errors.append({"stage": "project_object_recovery", "error": str(exc)})

    # AI participates in the *discovery* stage, not only in secondary filtering.
    # It receives only strong scope/identification excerpts and every returned
    # name is checked against the source excerpt before becoming a candidate.
    ai_scope_result = None
    ai_scope_sent = 0
    ai_scope_objects = []
    if str(ai_options.get("level") or "off").lower() != "off" and ai_options.get("provider") is not None:
        progress(68, "AI-анализ состава", "ИИ проверяет сильные источники состава проекта и восстанавливает пропущенные объекты")
        try:
            ai_scope_result, ai_scope_objects, ai_scope_sent = discover_objects_from_scope_evidence(
                ai_options.get("provider"), object_recovery_audit, limit_pages=6
            )
            findings.extend(ai_scope_objects)
        except Exception as exc:
            pipeline_errors.append({"stage":"ai_scope_discovery","error":str(exc)})

    progress(69, "Сканы и чертежи", "Определяем текстово-разреженные страницы и выполняем безопасный OCR, если он доступен")
    try:
        ocr_pages, scan_audit = recover_text_from_scanned_pages(pdf_files, document_types, max_pages_per_file=4)
        ocr_objects, ocr_object_audit = recover_project_objects_from_pages(ocr_pages)
        findings.extend(ocr_objects)
    except Exception as exc:
        ocr_pages, scan_audit, ocr_object_audit = [], [{"decision":"error","reason":str(exc)}], []
        pipeline_errors.append({"stage": "scan_ocr", "error": str(exc)})

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
        item["core_version"] = "17.1-proof-th-cross-section"

    # Универсальный поиск выполняется после распознавания контекста таблиц.
    discovered_objects, universal_discovery_audit = discover_object_candidates(findings)
    findings.extend(discovered_objects)
    structure_guard_audit_2 = apply_structure_guards(findings)
    structure_guard_audit = {k: int(structure_guard_audit.get(k,0))+int(structure_guard_audit_2.get(k,0)) for k in set(structure_guard_audit)|set(structure_guard_audit_2)}
    object_gate_audit_2 = apply_hard_object_gate(findings)
    object_gate_audit = {k: int(object_gate_audit.get(k,0))+int(object_gate_audit_2.get(k,0)) for k in set(object_gate_audit)|set(object_gate_audit_2)}

    progress(69, "Инженерная правдоподобность", "Удерживаем размерно противоречивые значения до проверки исходного документа")
    engineering_plausibility_audit = apply_engineering_plausibility_guard(findings)
    plausibility_questions = plausibility_review_questions(engineering_plausibility_audit)
    comparisons.extend(plausibility_questions)

    progress(69, "Контроль строк таблиц", "Проверяем, что показатель не был сдвинут на соседний объект при чтении PDF")
    table_row_integrity_audit = apply_table_row_integrity_guard(findings)

    progress(69, "Drawing Intelligence", "Строим граф листов, экспликаций и ревизий АР без догадок по ближайшему тексту")
    try:
        drawing_graph = DrawingIntelligenceV2().extract_uploaded(pdf_files, document_types, legacy.read_pdf)
        drawing_v2_findings = drawing_graph_findings(drawing_graph)
        findings.extend(drawing_v2_findings)
    except Exception as exc:
        drawing_graph = {"version":"2.0-alpha1","summary":{"error":str(exc)},"objects":[],"sheets":[],"room_schedules":[],"revisions":[],"withheld":[]}
        drawing_v2_findings = []
        pipeline_errors.append({"stage":"drawing_intelligence_v2","error":str(exc)})

    _enrich_semantics(findings)
    enrich_findings_with_object_semantics(findings)
    entity_property_binding_audit = annotate_entity_property_bindings(findings)
    trusted_object_audit.extend(annotate_findings(findings))
    # Генплан является опорным реестром: повторно и консервативно привязываем ТЭП
    # после универсального поиска объектов, затем строим проверки состава.
    general_plan_anchor_audit.extend(anchor_findings_to_general_plan(findings, gp_findings))
    table_semantic_scope_audit = annotate_table_semantic_scope(findings)
    evidence_provenance_audit = annotate_evidence_provenance(findings)
    drawing_intelligence_summary = annotate_drawing_evidence(findings)
    general_plan_field_checks = build_general_plan_field_checks(gp_findings, general_plan_audit)
    general_plan_document_checks, general_plan_coverage = build_general_plan_document_checks(findings, gp_findings)
    # Пересобираем сводную сверку после добавления генплана и семантических якорей.
    comparisons = [row for row in comparisons if str(row.get("category")) != "Межраздельная сверка"]
    cross_section_checks = build_cross_section_checks(findings)
    comparisons.extend(cross_section_checks)
    comparisons.extend(general_plan_field_checks)
    comparisons.extend(general_plan_document_checks)
    _enrich_rules(comparisons, registry)
    knowledge_base = KnowledgeBase(root / "knowledge")
    remark_learning = RemarkLearningEngine(root / "knowledge")
    for item in comparisons:
        knowledge_base.enrich_comparison(item)
        risk = calculate_engineering_risk(item)
        item["engineering_risk_score"] = risk["score"]
        item["engineering_risk_level"] = risk["level"]
        item["engineering_risk_reasons"] = risk["reasons"]
    remark_learning_count = remark_learning.enrich_comparisons(comparisons)
    engineering_review = CrossSectionDependencyEngine(root / "knowledge")
    engineering_review_count = engineering_review.enrich_comparisons(comparisons)
    expert_practice = ExpertPracticeIntelligence(root / "knowledge")
    expert_practice_count = expert_practice.enrich_comparisons(comparisons)

    # Final Object Gate runs before any registry is built. AI is the second filter
    # for ambiguous candidates, so the user sees an already cleaned project composition.
    progress(70, "Object Gate", "Отсекаем оглавления, пункты разделов, даты и служебные строки")
    final_gate = apply_hard_object_gate(findings)
    object_gate_audit = {k: int(object_gate_audit.get(k,0))+int(final_gate.get(k,0)) for k in set(object_gate_audit)|set(final_gate)}
    learning_examples = list(ai_options.get("learning_examples") or [])
    learning_applied = apply_learning_examples(findings, learning_examples)
    pre_ai_result, pre_ai_reviews, pre_ai_sent = review_object_candidates(
        ai_options.get("provider"), findings, limit=24, learning_examples=learning_examples
    ) if str(ai_options.get("level") or "off").lower() != "off" else (None, {}, 0)
    pre_ai_applied = apply_object_reviews(findings, pre_ai_reviews) if pre_ai_reviews else 0

    # Реестр объектов строится только после Object Gate + AI secondary filter.
    progress(72, "Консолидация реестра", "Сопоставляем ПЗ, генплан, XML и профильные разделы")
    raw_object_registry, object_register_audit = build_registry(findings)
    raw_consolidated_registry, reconciliation_audit = reconcile_register(findings)
    object_registry, object_candidates = filter_registry(raw_object_registry, findings)
    consolidated_registry, consolidated_candidates = filter_registry(raw_consolidated_registry, findings)

    # General Plan First safety net. The explication is an independent object
    # register and must remain visible even if downstream lifecycle inference or
    # PZ/XML matching is incomplete. Explicit project rows are restored to the
    # trusted registry; unknown-status rows remain visible as candidates.
    object_registry, object_candidates, gp_seed_audit = ensure_general_plan_registry_visibility(
        object_registry, object_candidates, gp_findings
    )
    consolidated_registry, consolidated_candidates, gp_seed_audit_consolidated = ensure_general_plan_registry_visibility(
        consolidated_registry, consolidated_candidates, gp_findings
    )

    # If PZ contains the explicit final complex-object table, it is the primary
    # project-composition baseline. Identification-sign rows not present in this
    # final table are suppressed; GP-only rows remain visible as discrepancies.
    object_registry, object_candidates, pz_authoritative_audit = enforce_authoritative_pz_registry(
        object_registry, object_candidates, pz_complex_objects, findings
    )
    consolidated_registry, consolidated_candidates, pz_authoritative_audit_consolidated = enforce_authoritative_pz_registry(
        consolidated_registry, consolidated_candidates, pz_complex_objects, findings
    )

    # Composition Fail-Safe: the engineer-facing object list is built from explicit
    # structured composition registers (PZ complex-object table + GP explication).
    # Downstream generic filters may enrich these rows, but cannot delete them.
    composition_baseline, composition_baseline_audit = build_composition_baseline(pz_complex_objects, gp_findings)
    if composition_baseline:
        consolidated_registry = merge_baseline_with_registry(composition_baseline, consolidated_registry)
        object_registry = merge_baseline_with_registry(composition_baseline, object_registry)
        # Generic narrative candidates are intentionally kept out of the primary
        # composition list when a structured baseline exists. They remain in findings
        # and developer diagnostics, but no longer displace real project objects.
        baseline_positions = {str(r.get('Позиция по ГП') or '') for r in composition_baseline}
        consolidated_candidates = [r for r in consolidated_candidates if str(r.get('Позиция по ГП') or '') not in baseline_positions and bool(r.get('general_plan_seed'))]
        object_candidates = [r for r in object_candidates if str(r.get('Позиция по ГП') or '') not in baseline_positions and bool(r.get('general_plan_seed'))]

    recovery_mode_triggered = needs_object_recovery(object_registry, object_candidates, gp_findings)
    if recovery_mode_triggered:
        progress(74, "Recovery Mode", "Повторно используем экспликацию генплана и сильные источники ПЗ; результат не считается пустым автоматически")

    ai_pipeline_audit = run_ai_pipeline(
        findings,
        comparisons,
        provider=ai_options.get("provider"),
        level=str(ai_options.get("level") or "off"),
        progress_callback=progress,
        skip_object_review=True,
    )
    ai_pipeline_audit["object_candidates_sent"] = pre_ai_sent
    ai_pipeline_audit["object_reviews_received"] = pre_ai_applied
    if pre_ai_result is not None and not pre_ai_result.ok:
        ai_pipeline_audit.setdefault("errors", []).append("Object AI: " + str(pre_ai_result.error))
    progress(80, 'Паспорта объектов', 'Формируем итоговый реестр и цифровые паспорта')
    object_passports = build_object_passports(object_registry, findings, comparisons)
    object_passport_summary = passport_summary(object_passports)

    # Project Understanding Engine 4.0: a property can only attach to a confirmed
    # project object. Ambiguous properties remain unresolved instead of creating
    # a false cross-section mismatch.
    progress(80, "Понимание проекта", "Связываем объекты, показатели, значения и источники в единую модель проекта")
    project_understanding = build_project_object_model(object_registry, findings)
    project_understanding_quality = understanding_quality(project_understanding)
    # Every extracted engineering fact receives a visible admission decision,
    # including facts that never reached Project Understanding.  This keeps the
    # technical appendix auditable and prevents raw HOLD/REJECT records from
    # looking equivalent to admitted evidence.
    for finding in findings:
        if str(finding.get('parameter_code') or '') in {'OBJECT_ENTRY','OBJECT_CANDIDATE'}:
            continue
        if not finding.get('fact_admission_decision'):
            finding.update(assess_fact_admission(finding))

    high_value_sanitization_audit = sanitize_high_value_facts(findings)

    # Final high-trust cross-section pass. Earlier extraction comparisons remain
    # useful diagnostics, but the final engineering comparisons are rebuilt only
    # from properties attached to confirmed objects.
    comparisons = [
        row for row in comparisons
        if str(row.get("category") or "") != "Межраздельная сверка"
        and str(row.get("check_type") or "") not in {"Межраздельная сверка","Сводная межраздельная проверка"}
    ]
    cross_section_checks = build_cross_section_checks(findings)
    comparisons.extend(cross_section_checks)
    _enrich_rules(comparisons, registry)

    project_profile_summary = ProjectProfileRegistry(root / "knowledge").summary()

    progress(81, "Задание на проектирование", "Готовим адресный корпус страниц без повторной обработки комплекта")
    try:
        assignment_page_corpus = build_page_corpus(pdf_files, legacy.read_pdf, document_types)
    except Exception as exc:
        assignment_page_corpus = []
        pipeline_errors.append({"stage":"assignment_page_corpus","error":str(exc)})
    project_page_corpus = [page for page in assignment_page_corpus if not is_assignment_source(page)]
    semantic_project_fingerprint = corpus_fingerprint(assignment_page_corpus)
    if semantic_checkpoint.get("_project_fingerprint") != semantic_project_fingerprint:
        semantic_checkpoint.clear()
        semantic_checkpoint["_project_fingerprint"] = semantic_project_fingerprint
    assignment_semantic_checkpoint = semantic_checkpoint.setdefault("assignment", {})
    checklist_semantic_checkpoint = semantic_checkpoint.setdefault("checklist", {})
    try:
        evidence_reconstruction = reconstruct_high_value_evidence(project_page_corpus)
        findings.extend(evidence_reconstruction.get("facts") or [])
        reconstructed_comparisons = list(evidence_reconstruction.get("comparisons") or [])
        comparisons.extend(reconstructed_comparisons)
        cross_section_checks.extend(reconstructed_comparisons)
        _enrich_rules(reconstructed_comparisons, registry)
    except Exception as exc:
        evidence_reconstruction = {"version":"1.0","facts":[],"comparisons":[],"summary":{"error":str(exc)}}
        pipeline_errors.append({"stage":"evidence_reconstruction","error":str(exc)})
    categorical_checks=[]
    try:
        categorical_checks=build_categorical_consistency_checks(project_page_corpus,object_registry)
        comparisons.extend(categorical_checks)
        cross_section_checks.extend(categorical_checks)
        _enrich_rules(categorical_checks,registry)
    except Exception as exc:
        pipeline_errors.append({'stage':'categorical_consistency','error':str(exc)})
    # The final high-trust pass used to discard the dependency enrichment that
    # had been calculated for an earlier diagnostic pass. Reapply the owner →
    # control matrix to the exact rows consumed by reports and public metrics.
    engineering_review.enrich_comparisons(cross_section_checks)
    cross_section_gate_summary=qualify_cross_section_verdicts(cross_section_checks)
    technology_proof=technology_proof_summary(cross_section_checks)
    atomic_requirement_graph = {"version":"1.0","atoms":[],"summary":{"source_requirements":0,"atomic_requirements":0}}
    universal_project_fact_graph = {"version":"1.0","facts":[],"passages":[],"summary":{"facts":0}}
    assignment_atomic_rows = []
    assignment_parent_baseline = []
    try:
        progress(82, "Задание на проектирование", "Извлекаем строки и атомарные требования Задания")
        assignment_requirements = extract_assignment_requirements(
            pdf_files, legacy.read_pdf, page_corpus=assignment_page_corpus,
        )
        assignment_directed_evidence_summary = attach_directed_evidence(assignment_requirements, project_page_corpus)
        assignment_parent_baseline = compare_assignment_requirements(assignment_requirements, findings, object_registry, project_page_corpus)
        atomic_requirement_graph = build_atomic_requirement_graph(assignment_requirements, domain="assignment")
        progress(83, "Задание на проектирование", f"Построено атомарных условий: {len(atomic_requirement_graph.get('atoms') or [])}")
        universal_project_fact_graph = build_universal_project_fact_graph(
            object_registry, findings, project_page_corpus
        )
        progress(84, "Задание на проектирование", "Отбираем лучшие адресные пакеты для ограниченной AI-проверки")

        def assignment_semantic_progress(role, completed, total):
            role_label = "Judge" if role == "JUDGE" else "Critic"
            progress(
                84 if role == "JUDGE" else 85,
                "Задание на проектирование",
                f"Консультативная AI-проверка {role_label}: обработано {completed} из {total} пакетов",
            )

        assignment_atomic_rows = verify_atomic_requirements(
            atomic_requirement_graph.get("atoms") or [],
            knowledge_root=str(root / "knowledge"),
            fact_graph=universal_project_fact_graph,
            page_corpus=project_page_corpus,
            judge_provider=semantic_judge_provider,
            critic_provider=semantic_critic_provider,
            semantic_level=semantic_level,
            semantic_limit=assignment_semantic_limit,
            semantic_progress_callback=assignment_semantic_progress,
            semantic_checkpoint=assignment_semantic_checkpoint,
        )
        progress(86, "Задание на проектирование", "Агрегируем результаты без категоричных выводов по недостаточным данным")
        assignment_compliance = aggregate_atomic_results(assignment_parent_baseline, assignment_atomic_rows)
        assignment_semantic_audit = dict((assignment_atomic_rows[0] if assignment_atomic_rows else {}).get("semantic_engine_audit") or {})
        assignment_ai_summary={
            "reviewed":assignment_semantic_audit.get("judge_responses",0),
            "confirmed":assignment_semantic_audit.get("promoted_verified",0),
            "contradicted":assignment_semantic_audit.get("project_findings",0),
            "semantic_evidence_engine":assignment_semantic_audit,
        }
        assignment_compliance_summary = parent_assignment_summary(
            assignment_compliance, assignment_atomic_rows, atomic_requirement_graph.get("summary") or {}
        )
        assignment_compliance_summary["ai_evidence_review"]=assignment_ai_summary
        assignment_compliance_summary["directed_evidence"]=assignment_directed_evidence_summary
        assignment_directed_facts = directed_evidence_facts(assignment_atomic_rows) + atomic_evidence_facts(assignment_atomic_rows)
        assignment_compliance_summary["directed_evidence"]["admitted_for_deep_review"] = len(assignment_directed_facts)
    except Exception as exc:
        assignment_requirements, assignment_compliance, assignment_directed_facts = [], [], []
        assignment_atomic_rows, assignment_parent_baseline = [], []
        assignment_compliance_summary = {"total":0,"compliant":0,"deviation":0,"unconfirmed":0,"semantic":0,"not_checked":0,"ai_evidence_review":{"reviewed":0,"confirmed":0,"contradicted":0},"error":str(exc)}
        pipeline_errors.append({"stage":"assignment_compliance","error":str(exc)})

    # Цифровая инженерная модель строится только из извлечённых доказательств.
    progress(87, "Межраздельная сверка", "Сравниваем инженерные характеристики и формируем объяснения")
    dem = build_dem(findings, project_name="Новый проект")
    validation_issues = ValidationEngine().validate(dem)
    relations = RelationEngine().build(dem)
    model_quality = calculate_model_quality(dem, validation_issues)
    quality_summary = build_quality_summary(findings)

    summary = registry.summary()
    table_pages_by_doc: dict[str, int] = defaultdict(int)
    for filename, _page in page_tables:
        table_pages_by_doc[filename] += 1

    progress(88, "Инженерная полнота", "Проверяем исходные документы и нормативные ссылки")
    mandatory_document_audit = audit_mandatory_documents(documents, findings)
    normative_reference_audit = scan_normative_references(findings)
    normative_layer = NormativeKnowledgeLayer(root / "knowledge")
    normative_reference_audit = normative_layer.enrich(normative_reference_audit)
    normative_validity_checker = NormativeValidityChecker(root / "knowledge")
    normative_validity_audit = normative_validity_checker.audit_uploaded_pdfs(pdf_files, legacy.read_pdf)
    if not normative_validity_audit:
        normative_validity_audit = normative_validity_checker.audit_findings(findings)
    normative_validity_summary = normative_validity_checker.summary(normative_validity_audit)
    normative_reference_summary = normative_validity_checker.aggregate_reference_audit(normative_validity_audit)
    try:
        normative_requirement_audit = NormativeRequirementAnalyzer(root / "knowledge").audit_uploaded_pdfs(pdf_files, legacy.read_pdf)
    except Exception as exc:
        normative_requirement_audit = []
        pipeline_errors.append({"stage":"normative_requirement_analysis","error":str(exc)})
    pp87_project_profile = detect_pp87_profile(findings, documents)
    try:
        normative_engine = NormativeComplianceEngine(root / "knowledge")
        normative_compliance_audit = normative_engine.review(
            findings,
            project_type=str(pp87_project_profile.get("project_type") or "") if isinstance(pp87_project_profile,dict) else "",
            page_corpus=project_page_corpus,
        )
        normative_compliance_summary = NormativeComplianceEngine.summary(normative_compliance_audit)
        normative_compliance_summary["knowledge_coverage"] = normative_engine.coverage()
    except Exception as exc:
        normative_compliance_audit = []
        normative_compliance_summary = {"requirements":0,"verified_clause":0,"ai_review_ready":0,"requires_kb_verification":0,"project_review":0,"error":str(exc)}
        pipeline_errors.append({"stage":"normative_compliance","error":str(exc)})
    evidence_graph = build_evidence_graph(findings, comparisons)
    progress(91, "Формирование результата", "Рассчитываем риски, статусы и цифровые паспорта")
    for item in comparisons:
        item["core_version"] = "17.1-proof-th-cross-section"
        item["dem_model_quality"] = model_quality.get("model_quality_index", 0.0)
    for item in findings:
        item["dem_object_count"] = dem.metadata.get("object_count", 0)
        item["dem_unassigned_values"] = dem.metadata.get("unassigned_value_count", 0)
    progress(93, "Автоматические чек-листы", "Определяем разделы и запускаем подходящие корпоративные чек-листы")
    project_context = {
        "project_type": str(pp87_project_profile.get("project_type") or pp87_project_profile.get("profile") or "") if isinstance(pp87_project_profile, dict) else str(pp87_project_profile or ""),
        "name": " ".join(str(x.get("Файл") or "") for x in documents[:5]),
        "description": " ".join(str(x.get("Раздел") or x.get("Тип документа") or "") for x in documents),
    }
    checklist_atomic_review = {"version":"1.0","atoms":[],"summary":{"atomic_conditions":0}}
    automatic_review = {"programme":[],"runs":[],"results":[],"summary":{"automatic":True}}
    try:
        automatic_review = AutomaticProjectReview(root / "knowledge").execute(
            documents, comparisons, findings, project_context=project_context
        )
    except Exception as exc:
        automatic_review["summary"]["error"] = str(exc)
        pipeline_errors.append({"stage":"automatic_checklist_programme","error":str(exc)})
    progress(
        94, "Автоматические чек-листы",
        f"Детерминированная программа сформирована: {len(automatic_review.get('results') or [])} строк",
    )
    try:
        # The initial request must finish and persist the project before a
        # project-sized external AI queue starts.  Every L4 checklist packet is
        # still prepared here; Judge/Critic work is resumed safely from the UI.
        initial_checklist_level = semantic_level if initial_checklist_semantic_limit > 0 else "off"
        progress(
            95, "Доказательная проверка чек-листов",
            "Проверяем детерминированные условия и формируем возобновляемую AI-очередь",
        )
        checklist_atomic_review = verify_checklist_rows(
            list(automatic_review.get("results") or []),
            knowledge_root=str(root / "knowledge"),
            fact_graph=universal_project_fact_graph,
            page_corpus=project_page_corpus,
            judge_provider=semantic_judge_provider,
            critic_provider=semantic_critic_provider,
            semantic_level=initial_checklist_level,
            semantic_limit=initial_checklist_semantic_limit,
            semantic_checkpoint=checklist_semantic_checkpoint,
            semantic_candidate_cap=acceleration_budget.checklist_semantic_limit,
        )
        if initial_checklist_level == "off" and semantic_level in {"extended", "maximum"}:
            deferred_audit = dict(checklist_atomic_review.get("semantic_engine_audit") or {})
            deferred_audit.update({
                "enabled": True,
                "deferred": True,
                "execution_mode": "DEFERRED_TO_RESUMABLE_QUEUE",
                "activation_reasons": [
                    "Внешняя AI-проверка отложена до сохранения первичного результата."
                ],
            })
            checklist_atomic_review["semantic_engine_audit"] = deferred_audit
            if checklist_atomic_review.get("atoms"):
                checklist_atomic_review["atoms"][0]["semantic_engine_audit"] = deferred_audit
        automatic_review["atomic_verification"] = checklist_atomic_review
    except Exception as exc:
        automatic_review["atomic_verification"] = checklist_atomic_review
        automatic_review.setdefault("summary", {})["atomic_verification_error"] = str(exc)
        pipeline_errors.append({"stage":"automatic_checklist_evidence","error":str(exc)})
    progress(
        96, "Автоматические чек-листы",
        "Детерминированная проверка завершена; внешняя AI-очередь не блокирует сохранение проекта",
    )
    decision_coverage = coverage_summary(cross_section_checks, (automatic_review.get("results") or []) if isinstance(automatic_review,dict) else [])
    evidence_review_plan = build_review_plan(
        assignment_rows=assignment_atomic_rows,
        normative_rows=normative_compliance_audit,
        checklist_review=automatic_review if isinstance(automatic_review,dict) else {},
        # Межраздельный Proof-контур детерминирован и уже имеет адресные
        # структурированные доказательства; не расходуем на него AI-очередь.
        comparisons=[],
    )
    review_plan = build_review_plan(
        assignment_rows=assignment_compliance,
        normative_rows=normative_compliance_audit,
        checklist_review=automatic_review if isinstance(automatic_review,dict) else {},
        comparisons=cross_section_checks,
    )
    progress(97, "Контроль доказательств", "Проверяем адресность и согласованность сформированных выводов")
    verified_core_gate_summary={"version":"17.0-final-verdict-gate-v1","checked":0,"passed":0,"blocked":0}
    # Deep Evidence Intelligence: reconstruct evidence once, then target every planned check.
    # This layer is conservative: it may downgrade weak positives, never invent evidence.
    try:
        from .deep_evidence_intelligence import (
            apply_deep_evidence_decisions, compact_deep_evidence_review,
            run_deep_evidence_review,
        )
        deep_evidence_review = run_deep_evidence_review(
            evidence_review_plan.get("items") or [], documents=documents,
            facts=findings + assignment_directed_facts + atomic_evidence_facts(checklist_atomic_review.get("atoms") or []),
            comparisons=cross_section_checks,
            page_corpus=project_page_corpus,
        )
        merge_summary=apply_deep_evidence_decisions(
            deep_evidence_review,
            assignment_rows=assignment_atomic_rows,
            normative_rows=normative_compliance_audit,
            checklist_review=automatic_review if isinstance(automatic_review,dict) else {},
        )
        deep_evidence_review['merge_summary']=merge_summary

        # One final gate runs after every retrieval/adversarial merge and before
        # public metrics are rebuilt.  No earlier status or cached L5 can bypass
        # the same contract consumed by the XLSX reports.
        from .verified_verdict_gate import enforce_project_verdicts, enforce_verified_verdicts
        verified_core_gate_summary=enforce_project_verdicts(
            assignment_rows=assignment_atomic_rows,
            normative_rows=normative_compliance_audit,
            checklist_review=automatic_review if isinstance(automatic_review,dict) else {},
            comparisons=cross_section_checks,
        )
        deep_evidence_review['verified_core_gate']=verified_core_gate_summary

        # Recalculate every public metric from the adjudicated rows.  This is the
        # critical feedback loop missing in 10.2 Alpha 2.
        assignment_meta={
            key:assignment_compliance_summary.get(key)
            for key in ('ai_evidence_review','directed_evidence')
            if key in assignment_compliance_summary
        }
        assignment_compliance=aggregate_atomic_results(assignment_parent_baseline,assignment_atomic_rows)
        assignment_parent_gate=enforce_verified_verdicts(
            assignment_compliance, domain="assignment",
        )
        verified_core_gate_summary['domains']['assignment_parent']=assignment_parent_gate
        for metric in ('checked','passed','blocked'):
            verified_core_gate_summary[metric]+=assignment_parent_gate[metric]
        deep_evidence_review['verified_core_gate']=verified_core_gate_summary
        assignment_compliance_summary=parent_assignment_summary(
            assignment_compliance, assignment_atomic_rows, atomic_requirement_graph.get("summary") or {}
        )
        assignment_compliance_summary.update(assignment_meta)
        if isinstance(automatic_review,dict):
            checklist_rows=list(automatic_review.get('results') or [])
            checklist_domain=domain_summary(checklist_rows,'checklist')
            actionable=[x for x in checklist_rows if not x.get('is_heading')]
            checklist_summary=dict(automatic_review.get('summary') or {})
            checklist_summary.update({
                'yes':sum(str(x.get('status') or '')=='Да' for x in actionable),
                'no':sum(str(x.get('status') or '')=='Нет' for x in actionable),
                'review':sum(str(x.get('status') or '')=='Требует проверки' for x in actionable),
                'unsupported':sum(str(x.get('status') or '')=='Не проверено системой' for x in actionable),
                'verified_completed':checklist_domain['completed'],
                'system_limitations':checklist_domain['system_limitations'],
                'review_questions':checklist_domain['review_questions'],
                'automatic_coverage_pct':checklist_domain['automatic_coverage_pct'],
            })
            automatic_review['summary']=checklist_summary
        review_plan=build_review_plan(
            assignment_rows=assignment_compliance,
            normative_rows=normative_compliance_audit,
            checklist_review=automatic_review if isinstance(automatic_review,dict) else {},
            comparisons=cross_section_checks,
        )
        deep_evidence_review['final_plan_metrics']={
            'completed':review_plan.get('completed',0),
            'project_findings':review_plan.get('project_findings',0),
            'review_questions':review_plan.get('review_questions',0),
            'system_limitations':review_plan.get('system_limitations',0),
        }
        deep_evidence_review=compact_deep_evidence_review(deep_evidence_review)
        decision_coverage = coverage_summary(cross_section_checks, (automatic_review.get("results") or []) if isinstance(automatic_review,dict) else [])
    except Exception as exc:
        deep_evidence_review = {"version":"1.0","results":[],"metrics":{"error":str(exc)}}
        pipeline_errors.append({"stage":"deep_evidence_intelligence","error":str(exc)})
    progress(98, "Контроль качества", "Формируем итоговые метрики, очередь продолжения и Quality Gate")
    coverage_matrix=build_coverage_matrix(review_plan.get('items') or [])
    semantic_packets = [
        dict(row.get("semantic_evidence_packet") or {})
        for row in assignment_atomic_rows + list(checklist_atomic_review.get("atoms") or [])
        if row.get("semantic_evidence_packet")
    ]
    semantic_project_graph = build_semantic_project_graph(universal_project_fact_graph, semantic_packets)
    semantic_engine_summary = {
        "version":"1.0",
        "assignment":dict((assignment_atomic_rows[0] if assignment_atomic_rows else {}).get("semantic_engine_audit") or {}),
        "checklist":dict(checklist_atomic_review.get("semantic_engine_audit") or {}),
        "evidence_coverage_pct":coverage_matrix.get("evidence_coverage_pct",0),
        "strict_coverage_pct":coverage_matrix.get("coverage_pct",0),
        "semantic_consensus_completed":coverage_matrix.get("semantic_consensus_completed",0),
    }
    report_quality_gate=validate_review_plan(
        review_plan,
        object_registry=object_registry,
        checklist_rows=(automatic_review.get('results') or []) if isinstance(automatic_review,dict) else [],
        comparisons=cross_section_checks,
    )
    if report_quality_gate.get('status')!='PASSED':
        pipeline_errors.append({
            'stage':'report_quality_gate',
            'error':'Нарушены инварианты итоговых метрик.',
            'issues':report_quality_gate.get('issues') or [],
        })
    analysis_snapshot = build_analysis_snapshot(
        documents, page_corpus=assignment_page_corpus,
        fact_graph=universal_project_fact_graph,
        object_registry=object_registry,
        quality_gate_comparisons=cross_section_checks,
    )
    # The structures below describe the analysis run as a whole, not an
    # individual source document.  Storing them on every document multiplied a
    # real 12-volume project result roughly twelvefold and caused Streamlit
    # Community Cloud to terminate the process while the workspace snapshot was
    # saved after object confirmation.  Keep lightweight per-document metadata
    # on every row and attach the run-level evidence graph only to the first row;
    # all UI/report consumers already read these structures from documents[0].
    for doc_index, doc in enumerate(documents):
        doc["core_version"] = "17.1-proof-th-cross-section"
        doc["Распознано страниц с таблицами"] = table_pages_by_doc.get(doc.get("Файл", ""), 0)
        if doc_index:
            continue
        doc["deep_evidence_review"] = deep_evidence_review
        doc["evidence_reconstruction"] = evidence_reconstruction
        doc["high_value_sanitization_audit"] = high_value_sanitization_audit
        doc["report_quality_gate"] = report_quality_gate
        doc["verified_core_gate"] = verified_core_gate_summary
        doc["cross_section_verified_gate"] = cross_section_gate_summary
        doc["technology_proof_summary"] = technology_proof
        doc["coverage_matrix"] = coverage_matrix
        doc["semantic_evidence_engine"] = semantic_engine_summary
        doc["semantic_project_graph"] = semantic_project_graph
        doc["coverage_acceleration_budget"] = acceleration_budget.as_dict()
        doc["analysis_snapshot"] = analysis_snapshot
        doc["knowledge_summary"] = summary
        doc["knowledge_engine_summary"] = default_knowledge_engine().summary()
        doc["universal_object_discovery_audit"] = universal_discovery_audit
        doc["universal_registry_audit"] = universal_registry_audit
        doc["cognitive_document_intelligence"] = {
            "pages": cognitive_page_structures,
            "audit": cognitive_audit,
            "findings": len(cognitive_findings),
            "official_register_objects": sum(1 for x in cognitive_findings if x.get("parameter_code") in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}),
            "row_locked_properties": sum(1 for x in cognitive_findings if x.get("binding_status") == "ROW_LOCKED"),
        }
        doc["evidence_base_summary"] = knowledge_base.summary()
        doc["xml_engine_summary"] = {
            "files": len(xml_files),
            "findings": len(xml_findings),
            "warnings": xml_warnings,
            "normalized_characteristics": sum(1 for f in xml_findings if f.get("parameter_code") not in {"XML_TEI", "OBJECT_CANDIDATE", "OBJECT_ENTRY", "PROJECT_NAME", "PROJECT_CODE", "PROJECT_YEAR", "ISSUE_AUTHOR", "CHIEF_ENGINEER", "RESOURCE", "CONSTRUCTION_TYPE", "RESPONSIBILITY_LEVEL", "FIRE_DANGER"}),
            "pdf_xml_checks": len(pdf_xml_checks),
            "pdf_xml_mismatches": sum(1 for row in pdf_xml_checks if row.get("status") == "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ"),
            "cross_section_checks": len(cross_section_checks),
            "cross_section_mismatches": sum(1 for row in cross_section_checks if row.get("status") in {"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ", "КОНФЛИКТ ВНУТРИ РАЗДЕЛА"}),
            "cross_section_unconfirmed": sum(1 for row in cross_section_checks if row.get("status") == "НЕДОСТАТОЧНО ДАННЫХ"),
        }
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
        doc["trusted_object_audit"] = trusted_object_audit
        doc["object_candidates"] = object_candidates
        doc["consolidated_candidates"] = consolidated_candidates
        doc["consolidated_registry"] = consolidated_registry
        doc["register_reconciliation_audit"] = reconciliation_audit
        doc["consolidated_registry_summary"] = {
            "records": len(consolidated_registry),
            "confirmed_3plus": sum(1 for row in consolidated_registry if row.get("Количество источников", 0) >= 3),
            "missing_in_pz": sum(1 for row in consolidated_registry if row.get("Статус консолидации") == "Есть на генплане — отсутствует в ПЗ"),
            "source_conflicts": sum(1 for row in consolidated_registry if row.get("Конфликты")),
        }
        doc["project_profile_summary"] = project_profile_summary
        doc["general_plan_audit"] = general_plan_audit
        doc["pz_complex_object_audit"] = pz_complex_object_audit
        doc["pz_complex_object_count"] = len([x for x in pz_complex_objects if x.get("parameter_code") == "OBJECT_ENTRY"])
        doc["engineering_plausibility_audit"] = engineering_plausibility_audit
        doc["composition_baseline"] = composition_baseline
        doc["composition_baseline_audit"] = composition_baseline_audit
        doc["pz_authoritative_registry_audit"] = pz_authoritative_audit_consolidated
        doc["general_plan_anchor_audit"] = general_plan_anchor_audit
        doc["general_plan_coverage"] = general_plan_coverage
        doc["general_plan_summary"] = {
            "entries": len(gp_findings),
            "from_explication": sum(1 for row in gp_findings if row.get("general_plan_explication")),
            "confirmed_on_drawing": sum(1 for row in gp_findings if row.get("general_plan_field")),
            "requires_field_review": sum(1 for row in gp_findings if row.get("general_plan_explication") and not row.get("general_plan_field")),
            "objects_checked_in_documents": len(general_plan_coverage),
            "missing_in_pz": sum(1 for row in general_plan_coverage if row.get("missing_in_pz")),
        }
        doc["object_passports"] = [passport.to_dict() for passport in object_passports]
        doc["object_passport_summary"] = object_passport_summary
        doc["ai_pipeline_audit"] = ai_pipeline_audit
        doc["pipeline_errors"] = pipeline_errors
        doc["structure_guard_audit"] = structure_guard_audit
        doc["object_gate_audit"] = object_gate_audit
        doc["object_recovery_audit"] = object_recovery_audit
        doc["object_discovery_3_summary"] = {
            "general_plan_first": True,
            "general_plan_explication_objects": sum(1 for x in gp_findings if x.get("general_plan_explication")),
            "general_plan_seed_trusted": int(gp_seed_audit.get("general_plan_seed_trusted", 0)) + int(gp_seed_audit_consolidated.get("general_plan_seed_trusted", 0)),
            "general_plan_seed_candidates": int(gp_seed_audit.get("general_plan_seed_candidates", 0)) + int(gp_seed_audit_consolidated.get("general_plan_seed_candidates", 0)),
            "recovery_mode_triggered": recovery_mode_triggered,
            "trusted_objects": len(object_registry),
            "candidate_objects": len(object_candidates),
        }
        doc["ai_scope_discovery"] = {
            "sources_sent": ai_scope_sent,
            "objects_recovered": len(ai_scope_objects),
            "provider": getattr(ai_scope_result, "provider", "") if ai_scope_result else "",
            "error": getattr(ai_scope_result, "error", "") if ai_scope_result and not ai_scope_result.ok else "",
        }
        doc["scan_document_audit"] = scan_audit
        doc["ocr_object_audit"] = ocr_object_audit
        doc["pp87_project_profile"] = pp87_project_profile
        doc["learning_engine_summary"] = {"examples_loaded": len(learning_examples), "rules_applied": learning_applied}
        doc["mandatory_document_audit"] = mandatory_document_audit
        doc["normative_reference_audit"] = normative_reference_audit
        doc["drawing_intelligence_summary"] = drawing_intelligence_summary
        doc["drawing_intelligence_v2"] = drawing_graph
        doc["drawing_intelligence_v2_summary"] = drawing_graph.get("summary", {})
        doc["decision_coverage"] = decision_coverage
        doc["normative_validity_audit"] = normative_validity_audit
        doc["normative_validity_summary"] = normative_validity_summary
        doc["normative_reference_summary"] = normative_reference_summary
        doc["normative_requirement_audit"] = normative_requirement_audit
        doc["normative_compliance_audit"] = normative_compliance_audit
        doc["normative_compliance_summary"] = normative_compliance_summary
        doc["normative_knowledge_summary"] = normative_layer.summary()
        doc["automatic_checklist_review"] = automatic_review
        doc["project_review_plan"] = review_plan
        doc["project_understanding"] = project_understanding
        doc["project_understanding_quality"] = project_understanding_quality
        doc["assignment_requirements"] = assignment_requirements
        doc["assignment_compliance"] = assignment_compliance
        doc["assignment_atomic_compliance"] = assignment_atomic_rows
        doc["atomic_requirement_graph"] = atomic_requirement_graph
        doc["universal_project_fact_graph"] = {
            **universal_project_fact_graph,
            "passages": [],
        }
        doc["assignment_compliance_summary"] = assignment_compliance_summary
        doc["engineering_review_summary"] = {**engineering_review.summary(), "enriched_comparisons": engineering_review_count}
        doc["entity_property_binding_summary"] = entity_property_binding_audit
        doc["table_row_integrity_summary"] = table_row_integrity_audit
        doc["evidence_provenance_summary"] = evidence_provenance_audit
        doc["expert_practice_summary"] = {**expert_practice.summary(), "enriched_comparisons": expert_practice_count}
        doc["remark_learning_summary"] = {"matched_comparisons": remark_learning_count, "case_count": len(remark_learning.cases)}
        doc["evidence_graph"] = evidence_graph

    progress(100, "Готово", "Проверка проекта завершена")
    return documents, findings, comparisons
