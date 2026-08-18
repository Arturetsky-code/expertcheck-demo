from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from .ai_gateway import AIProvider, AIResult, _extract_json, _ensure_russian_payload
from .normalization import normalize_text


@dataclass
class AIPipelineAudit:
    enabled: bool = False
    level: str = "off"
    provider: str = ""
    object_candidates_sent: int = 0
    object_reviews_received: int = 0
    property_checks_sent: int = 0
    property_reviews_received: int = 0
    errors: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["errors"] = list(self.errors or [])
        return data


def _safe_fragment(item: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "value_text", "object_hint", "genplan_position", "object_lifecycle_status",
        "document", "document_type", "page", "section_title", "structural_zone",
        "table_title", "table_evidence", "context", "source_type",
        "object_intelligence_decision", "object_intelligence_confidence",
        "object_intelligence_reason", "core2_confidence", "structure_guard_blocked", "structure_guard_reason",
    )
    return {key: item.get(key) for key in keys if item.get(key) not in (None, "", [])}


def review_object_candidates(
    provider: AIProvider | None,
    findings: list[dict[str, Any]],
    *,
    limit: int = 12,
    learning_examples: list[dict[str, Any]] | None = None,
) -> tuple[AIResult | None, dict[str, dict[str, Any]], int]:
    if provider is None:
        return None, {}, 0
    candidates: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for item in findings:
        if str(item.get("parameter_code") or "") not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            continue
        decision = str(item.get("object_intelligence_decision") or "review")
        if item.get("structure_guard_blocked"):
            continue
        confidence = int(item.get("object_intelligence_confidence") or 0)
        if decision == "trusted" and confidence >= 90:
            continue
        name = str(item.get("value_text") or item.get("object_hint") or "").strip()
        position = str(item.get("genplan_position") or "").strip()
        key = f"{position}|{name.lower()}"
        if not name or key in seen:
            continue
        seen.add(key)
        candidates.append((key, _safe_fragment(item)))
        if len(candidates) >= limit:
            break
    if not candidates:
        return None, {}, 0

    system = (
        "Вы — модуль вторичной проверки состава проектируемых объектов. "
        "Верните только JSON без Markdown. Не создавайте сведения, которых нет во фрагментах. "
        "Ответ: {\"items\":[{\"key\":\"...\",\"entity_type\":\"project_object|equipment|document_service|context_object|unknown\","
        "\"design_status\":\"projected|reconstructed|existing|prospective|unknown\","
        "\"independent_object\":true,\"confidence\":0.0,\"recommended_action\":\"include|review|exclude\","
        "\"reason\":\"...\",\"evidence_refs\":[\"document/page/table\"]}]}. "
        "Рекомендация include допустима только при явном доказательстве самостоятельного проектируемого объекта."
    )
    payload = {"task": "object_registry_review", "candidates": [{"key": k, **v} for k, v in candidates], "verified_user_examples": list(learning_examples or [])[-20:]}
    result = provider.generate(json.dumps(payload, ensure_ascii=False, indent=2), system)
    parsed = _extract_json(result.text) if result.ok else None
    reviews: dict[str, dict[str, Any]] = {}
    if isinstance(parsed, dict):
        for row in parsed.get("items") or []:
            if isinstance(row, dict) and row.get("key"):
                reviews[str(row["key"])] = row
    return result, reviews, len(candidates)


def apply_object_reviews(findings: list[dict[str, Any]], reviews: dict[str, dict[str, Any]]) -> int:
    applied = 0
    for item in findings:
        if str(item.get("parameter_code") or "") not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            continue
        name = str(item.get("value_text") or item.get("object_hint") or "").strip()
        position = str(item.get("genplan_position") or "").strip()
        key = f"{position}|{name.lower()}"
        review = reviews.get(key)
        if not review:
            continue
        item["ai_object_review"] = review
        item["ai_object_action"] = review.get("recommended_action")
        item["ai_object_confidence"] = review.get("confidence")
        item["ai_object_reason"] = review.get("reason")
        # AI is advisory. It may strengthen review or block obvious service/equipment,
        # but never upgrades a candidate to trusted without deterministic evidence.
        if review.get("recommended_action") == "exclude" and float(review.get("confidence") or 0) >= 0.85:
            if item.get("general_plan_explication") or item.get("object_recovery_strong_evidence"):
                # AI cannot erase a deterministic official-register row. It may
                # only request human review when its semantic interpretation differs.
                item["object_intelligence_decision"] = "review"
                item["object_intelligence_reason"] = "AI сомневается в объекте из сильного источника; требуется проверка пользователя: " + str(review.get("reason") or "")
            else:
                item["object_intelligence_decision"] = "blocked"
                item["object_intelligence_reason"] = "AI-вторичная проверка: " + str(review.get("reason") or "кандидат не является объектом проекта")
        elif review.get("recommended_action") == "include" and item.get("object_intelligence_decision") != "trusted":
            item["object_intelligence_decision"] = "review"
            item["object_intelligence_reason"] = "AI рекомендует включение, но требуется подтверждение пользователя: " + str(review.get("reason") or "")
        applied += 1
    return applied


def review_ambiguous_comparisons(
    provider: AIProvider | None,
    comparisons: list[dict[str, Any]],
    *,
    limit: int = 6,
) -> tuple[AIResult | None, dict[str, dict[str, Any]], int]:
    if provider is None:
        return None, {}, 0
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(comparisons):
        status = str(row.get("status") or row.get("Статус") or "").upper()
        if not any(token in status for token in ("РАСХОЖ", "КОНФЛИКТ", "НЕДОСТАТОЧНО", "ТРЕБУЕТ")):
            continue
        key = str(row.get("comparison_id") or row.get("rule_id") or f"cmp-{idx}")
        rows.append({
            "key": key,
            "object": row.get("object") or row.get("Объект"),
            "parameter": row.get("parameter") or row.get("Параметр") or row.get("parameter_code"),
            "status": row.get("status") or row.get("Статус"),
            "values": row.get("values") or row.get("Значения"),
            "sources": row.get("sources") or row.get("Источники") or row.get("sections"),
            "explanation": row.get("explanation") or row.get("Пояснение"),
        })
        row["ai_pipeline_key"] = key
        if len(rows) >= limit:
            break
    if not rows:
        return None, {}, 0
    system = (
        "Вы — модуль контроля привязки технико-экономических показателей. Верните только JSON без Markdown. "
        "Все пользовательские пояснения reason пишите только на русском языке. "
        "Строго различайте СУЩНОСТИ: object — это объект проектирования (например КПП, насосная станция, КТП), "
        "parameter — это характеристика/ТЭП (например площадь застройки, мощность, высота). "
        "Название ТЭП никогда не является объектом. Проверяйте, достаточно ли доказательств, что значения относятся к ОДНОМУ объекту и ОДНОМУ показателю. "
        "Ответ: {\"items\":[{\"key\":\"...\",\"binding\":\"valid|suspicious|insufficient\","
        "\"confidence\":0.0,\"reason\":\"...\",\"recommended_status\":\"keep|requires_review|suppress\"}]}. "
        "Не сравнивайте числа заново и не выдумывайте источники."
    )
    result = provider.generate(json.dumps({"task": "property_binding_review", "comparisons": rows}, ensure_ascii=False, indent=2), system)
    parsed = _extract_json(result.text) if result.ok else None
    parsed = _ensure_russian_payload(provider, parsed) if parsed is not None else parsed
    reviews: dict[str, dict[str, Any]] = {}
    if isinstance(parsed, dict):
        for item in parsed.get("items") or []:
            if isinstance(item, dict) and item.get("key"):
                reviews[str(item["key"])] = item
    return result, reviews, len(rows)


def apply_comparison_reviews(comparisons: list[dict[str, Any]], reviews: dict[str, dict[str, Any]]) -> int:
    applied = 0
    for row in comparisons:
        review = reviews.get(str(row.get("ai_pipeline_key") or ""))
        if not review:
            continue
        row["ai_property_review"] = review
        row["ai_binding_status"] = review.get("binding")
        row["ai_binding_reason"] = review.get("reason")
        # A suspicious binding must not be shown as a categorical discrepancy.
        if review.get("recommended_status") in {"requires_review", "suppress"} and float(review.get("confidence") or 0) >= 0.75:
            row["status_before_ai"] = row.get("status") or row.get("Статус")
            row["status"] = "НЕДОСТАТОЧНО ДАННЫХ"
            row["explanation"] = "AI-контроль выявил неоднозначную привязку ТЭП: " + str(review.get("reason") or "требуется проверка источника")
        applied += 1
    return applied


def run_ai_pipeline(
    findings: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    *,
    provider: AIProvider | None,
    level: str = "helper",
    progress_callback=None,
    skip_object_review: bool = False,
) -> dict[str, Any]:
    normalized = str(level or "off").strip().lower()
    audit = AIPipelineAudit(enabled=provider is not None and normalized != "off", level=normalized, provider=getattr(provider, "name", ""), errors=[])
    if not audit.enabled:
        return audit.to_dict()

    if not skip_object_review:
        if progress_callback:
            progress_callback(75, 'AI-анализ объектов', 'Проверяем только неоднозначные позиции; при недоступности API Core продолжит работу')
        result, reviews, sent = review_object_candidates(provider, findings, limit=24)
        audit.object_candidates_sent = sent
        if result and not result.ok:
            audit.errors.append("Object AI: " + str(result.error))
        audit.object_reviews_received = apply_object_reviews(findings, reviews)

    if normalized in {"extended", "maximum", "расширенный", "максимальный"}:
        if progress_callback:
            progress_callback(78, 'AI-контроль ТЭП', 'Проверяем неоднозначные привязки показателей')
        result2, reviews2, sent2 = review_ambiguous_comparisons(provider, comparisons)
        audit.property_checks_sent = sent2
        if result2 and not result2.ok:
            audit.errors.append("Property AI: " + str(result2.error))
        audit.property_reviews_received = apply_comparison_reviews(comparisons, reviews2)
    return audit.to_dict()


def discover_objects_from_scope_evidence(
    provider: AIProvider | None,
    scope_audit: list[dict[str, Any]],
    *,
    limit_pages: int = 6,
) -> tuple[AIResult | None, list[dict[str,Any]], int]:
    """AI-assisted *discovery* from strong project-scope evidence.

    Unlike secondary candidate review, this step can recover an object that a
    deterministic parser did not tokenize. Every returned name is verified to
    occur in the supplied source excerpt before it is admitted as a candidate.
    """
    if provider is None:
        return None, [], 0
    sources=[]
    for row in scope_audit:
        if row.get('decision')!='scope_source' or not row.get('excerpt'):
            continue
        sources.append({
            'source_key':f"{row.get('document')}|{row.get('page')}",
            'document':row.get('document'),'document_type':row.get('document_type'),
            'page':row.get('page'),'reason':row.get('reason'),'excerpt':row.get('excerpt'),
        })
        if len(sources)>=limit_pages:break
    if not sources:
        return None, [], 0
    system=(
        'Вы — модуль первичного определения состава проектируемых объектов. Верните только JSON без Markdown. '
        'Анализируйте только предоставленные фрагменты сильных источников: состав сложного объекта, идентификационные признаки, '
        'формулировки «проектом предусматривается строительство/реконструкция», экспликации и перечни объектов. '
        'Не включайте разделы, пункты, даты, оборудование внутри самостоятельного объекта, нормативные документы и существующие объекты. '
        'Ответ: {"objects":[{"source_key":"...","name":"точное наименование из текста","position":"",'
        '"design_status":"projected|reconstructed|existing|prospective|unknown","independent_object":true,'
        '"confidence":0.0,"reason":"..."}]}. Название должно быть дословно подтверждено исходным фрагментом.'
    )
    payload={'task':'deep_project_object_discovery','sources':sources}
    result=provider.generate(json.dumps(payload,ensure_ascii=False),system)
    parsed=_extract_json(result.text) if result.ok else None
    accepted=[]
    if not isinstance(parsed,dict):
        return result, accepted, len(sources)
    by_key={x['source_key']:x for x in sources}
    for obj in parsed.get('objects') or []:
        if not isinstance(obj,dict):continue
        key=str(obj.get('source_key') or '')
        src=by_key.get(key)
        name=str(obj.get('name') or '').strip()
        if not src or not name:continue
        # Mandatory hallucination guard: exact normalized name must occur in evidence.
        if normalize_text(name) not in normalize_text(src.get('excerpt') or ''):
            continue
        if str(obj.get('design_status') or '') not in {'projected','reconstructed'}:
            continue
        if obj.get('independent_object') is False:
            continue
        try: conf=float(obj.get('confidence') or 0)
        except Exception: conf=0
        if conf < 0.72:continue
        accepted.append({
            'parameter_code':'OBJECT_CANDIDATE','parameter_name':'Проектируемый объект (AI discovery)',
            'value_text':name,'object_hint':name,'genplan_position':str(obj.get('position') or ''),
            'document':src.get('document'),'document_type':src.get('document_type'),'page':src.get('page'),
            'confidence':min(0.9,max(0.72,conf)),'core2_confidence':min(0.9,max(0.72,conf)),
            'source_type':'OBJECT_REGISTER','source_kind':'ai_scope_discovery',
            'match_method':'AI Project Scope Discovery','structural_zone':'сильный источник состава проектируемых объектов',
            'context':src.get('excerpt'),'object_lifecycle_status':'Реконструируемый' if obj.get('design_status')=='reconstructed' else 'Проектируемый',
            'trusted_zone':'OBJECT_REGISTER','ai_discovery_reason':obj.get('reason'),'ai_discovery_confidence':conf,
            'record_kind':'project_object',
        })
    return result, accepted, len(sources)
