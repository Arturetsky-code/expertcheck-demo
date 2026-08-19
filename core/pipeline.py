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
from .automatic_review import AutomaticProjectReview
from .remark_learning import RemarkLearningEngine
from .learning_engine import apply_learning_examples
from .object_discovery_orchestrator import ensure_general_plan_registry_visibility, needs_object_recovery
from .composition_registry import build_composition_baseline, merge_baseline_with_registry
from .pz_complex_object_register import extract_pz_complex_object_register_from_uploaded, enforce_authoritative_pz_registry
from .engineering_review_engine import CrossSectionDependencyEngine
from .expert_practice_intelligence import ExpertPracticeIntelligence
from .entity_property_binding import annotate_findings as annotate_entity_property_bindings
from .assignment_compliance import extract_requirements as extract_assignment_requirements, compare_requirements as compare_assignment_requirements, summary as assignment_summary
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
        item["core_version"] = "9.2.0-processing-binding-reliability-alpha1"

    # Универсальный поиск выполняется после распознавания контекста таблиц.
    discovered_objects, universal_discovery_audit = discover_object_candidates(findings)
    findings.extend(discovered_objects)
    structure_guard_audit_2 = apply_structure_guards(findings)
    structure_guard_audit = {k: int(structure_guard_audit.get(k,0))+int(structure_guard_audit_2.get(k,0)) for k in set(structure_guard_audit)|set(structure_guard_audit_2)}
    object_gate_audit_2 = apply_hard_object_gate(findings)
    object_gate_audit = {k: int(object_gate_audit.get(k,0))+int(object_gate_audit_2.get(k,0)) for k in set(object_gate_audit)|set(object_gate_audit_2)}
    _enrich_semantics(findings)
    enrich_findings_with_object_semantics(findings)
    entity_property_binding_audit = annotate_entity_property_bindings(findings)
    trusted_object_audit.extend(annotate_findings(findings))
    # Генплан является опорным реестром: повторно и консервативно привязываем ТЭП
    # после универсального поиска объектов, затем строим проверки состава.
    general_plan_anchor_audit.extend(anchor_findings_to_general_plan(findings, gp_findings))
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
    project_profile_summary = ProjectProfileRegistry(root / "knowledge").summary()

    progress(81, "Задание на проектирование", "Извлекаем требования Задания и сопоставляем их с проектными решениями")
    try:
        assignment_requirements = extract_assignment_requirements(pdf_files, legacy.read_pdf)
        assignment_compliance = compare_assignment_requirements(assignment_requirements, findings, object_registry)
        assignment_compliance_summary = assignment_summary(assignment_compliance)
    except Exception as exc:
        assignment_requirements, assignment_compliance = [], []
        assignment_compliance_summary = {"total":0,"compliant":0,"deviation":0,"unconfirmed":0,"semantic":0,"error":str(exc)}
        pipeline_errors.append({"stage":"assignment_compliance","error":str(exc)})

    # Цифровая инженерная модель строится только из извлечённых доказательств.
    progress(82, "Межраздельная сверка", "Сравниваем инженерные характеристики и формируем объяснения")
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
    try:
        normative_requirement_audit = NormativeRequirementAnalyzer(root / "knowledge").audit_uploaded_pdfs(pdf_files, legacy.read_pdf)
    except Exception as exc:
        normative_requirement_audit = []
        pipeline_errors.append({"stage":"normative_requirement_analysis","error":str(exc)})
    evidence_graph = build_evidence_graph(findings, comparisons)
    progress(91, "Формирование результата", "Рассчитываем риски, статусы и цифровые паспорта")
    for item in comparisons:
        item["core_version"] = "9.2.0-processing-binding-reliability-alpha1"
        item["dem_model_quality"] = model_quality.get("model_quality_index", 0.0)
    for item in findings:
        item["dem_object_count"] = dem.metadata.get("object_count", 0)
        item["dem_unassigned_values"] = dem.metadata.get("unassigned_value_count", 0)
    pp87_project_profile = detect_pp87_profile(findings, documents)
    progress(93, "Автоматические чек-листы", "Определяем разделы и запускаем подходящие корпоративные чек-листы")
    project_context = {
        "project_type": str(pp87_project_profile.get("project_type") or pp87_project_profile.get("profile") or "") if isinstance(pp87_project_profile, dict) else str(pp87_project_profile or ""),
        "name": " ".join(str(x.get("Файл") or "") for x in documents[:5]),
        "description": " ".join(str(x.get("Раздел") or x.get("Тип документа") or "") for x in documents),
    }
    try:
        automatic_review = AutomaticProjectReview(root / "knowledge").execute(
            documents, comparisons, findings, project_context=project_context
        )
    except Exception as exc:
        automatic_review = {"programme":[],"runs":[],"results":[],"summary":{"automatic":True,"error":str(exc)}}
        pipeline_errors.append({"stage":"automatic_checklists","error":str(exc)})
    for doc in documents:
        doc["core_version"] = "9.2.0-processing-binding-reliability-alpha1"
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
        doc["normative_validity_audit"] = normative_validity_audit
        doc["normative_validity_summary"] = normative_validity_summary
        doc["normative_requirement_audit"] = normative_requirement_audit
        doc["normative_knowledge_summary"] = normative_layer.summary()
        doc["automatic_checklist_review"] = automatic_review
        doc["assignment_requirements"] = assignment_requirements
        doc["assignment_compliance"] = assignment_compliance
        doc["assignment_compliance_summary"] = assignment_compliance_summary
        doc["engineering_review_summary"] = {**engineering_review.summary(), "enriched_comparisons": engineering_review_count}
        doc["entity_property_binding_summary"] = entity_property_binding_audit
        doc["expert_practice_summary"] = {**expert_practice.summary(), "enriched_comparisons": expert_practice_count}
        doc["remark_learning_summary"] = {"matched_comparisons": remark_learning_count, "case_count": len(remark_learning.cases)}
        doc["evidence_graph"] = evidence_graph
        doc["Распознано страниц с таблицами"] = table_pages_by_doc.get(doc.get("Файл", ""), 0)

    progress(100, "Готово", "Проверка проекта завершена")
    return documents, findings, comparisons
