from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from .normalization import normalize_text
from .evidence_registry import evidence_record, is_forbidden_evidence
from .object_quality_rules import strong_object_name

OFFICIAL_SOURCE_TYPES = {"OBJECT_REGISTER"}
SUPPORTING_SOURCE_TYPES = {"OBJECT_TEP", "DRAWING_FIELD"}
WEAK_SOURCE_TYPES = {"NARRATIVE"}
PROJECT_LIFECYCLES = {"Проектируемый", "Реконструируемый", "Переносимый"}


@dataclass(frozen=True)
class ObjectDecision:
    key: str
    name: str
    position: str
    decision: str
    confidence: int
    lifecycle: str
    official_sources: int
    supporting_sources: int
    independent_documents: int
    forbidden_sources: int
    reason: str
    canonical_source: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _candidate_key(item: dict[str, Any]) -> str:
    position = str(item.get("genplan_position") or "").strip()
    name = normalize_text(item.get("value_text") or item.get("object_hint") or "")
    return f"{position}|{name}"


def _document_identity(rec: dict[str, Any]) -> str:
    return normalize_text(rec.get("document") or rec.get("document_type") or "")


def _source_rank(rec: dict[str, Any]) -> tuple[int, float]:
    source_type = str(rec.get("source_type") or "")
    base = 0
    if source_type in OFFICIAL_SOURCE_TYPES:
        base = 4
    elif source_type in SUPPORTING_SOURCE_TYPES:
        base = 3
    elif source_type in WEAK_SOURCE_TYPES:
        base = 1
    if rec.get("forbidden"):
        base = -10
    try:
        confidence = float(rec.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    return base, confidence


def build_object_decisions(findings: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    names: dict[str, str] = {}
    positions: dict[str, str] = {}
    lifecycles: dict[str, list[str]] = defaultdict(list)

    for item in findings:
        if str(item.get("parameter_code") or "") not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            continue
        key = _candidate_key(item)
        if key == "|":
            continue
        grouped[key].append(evidence_record(item))
        names[key] = str(item.get("value_text") or item.get("object_hint") or "").strip()
        positions[key] = str(item.get("genplan_position") or "").strip()
        lifecycles[key].append(str(item.get("object_lifecycle_status") or "Не определён"))

    decisions: dict[str, dict[str, Any]] = {}
    for key, records in grouped.items():
        valid = [r for r in records if not r.get("forbidden")]
        forbidden = [r for r in records if r.get("forbidden")]
        official = [r for r in valid if r.get("source_type") in OFFICIAL_SOURCE_TYPES]
        supporting = [r for r in valid if r.get("source_type") in SUPPORTING_SOURCE_TYPES]
        independent = {_document_identity(r) for r in valid if _document_identity(r)}
        lifecycle_values = lifecycles.get(key, [])
        lifecycle = next((v for v in lifecycle_values if v in PROJECT_LIFECYCLES), None)
        if lifecycle is None:
            lifecycle = next((v for v in lifecycle_values if v != "Не определён"), "Не определён")

        canonical = max(valid, key=_source_rank, default=None)
        name_ok, name_reasons = strong_object_name(names.get(key, ""), position=positions.get(key, ""), official=bool(official))
        if not name_ok:
            decision = "blocked"
            confidence = 0
            reason = "Кандидат отклонён строгими правилами: " + "; ".join(name_reasons) + "."
        elif forbidden and not valid:
            decision = "blocked"
            confidence = 0
            reason = "Кандидат найден только в запрещённых служебных источниках."
        elif lifecycle not in PROJECT_LIFECYCLES:
            decision = "context"
            confidence = 40 if valid else 0
            reason = f"Статус объекта: {lifecycle}. В основной состав текущего проекта не включается автоматически."
        elif official and positions.get(key):
            decision = "trusted"
            confidence = 99 if len(independent) >= 2 else 96
            reason = "Объект имеет позицию и найден в официальном объектном источнике."
        elif official and len(independent) >= 2:
            decision = "trusted"
            confidence = 92
            reason = "Безпозиционный объект подтверждён официальным реестром и вторым независимым документом."
        elif len(supporting) >= 2 and len(independent) >= 2 and positions.get(key):
            decision = "review"
            confidence = 74
            reason = "Есть позиция и два инженерных подтверждения, но нет официальной объектной таблицы. Требуется подтверждение пользователя."
        elif supporting or valid:
            decision = "review"
            confidence = 45 if supporting else 25
            reason = "Недостаточно строгих оснований: требуется официальный объектный источник либо позиция и независимые подтверждения."
        else:
            decision = "blocked"
            confidence = 0
            reason = "Допустимые доказательства отсутствуют."

        obj = ObjectDecision(
            key=key,
            name=names.get(key, ""),
            position=positions.get(key, ""),
            decision=decision,
            confidence=confidence,
            lifecycle=lifecycle,
            official_sources=len(official),
            supporting_sources=len(supporting),
            independent_documents=len(independent),
            forbidden_sources=len(forbidden),
            reason=reason,
            canonical_source=canonical,
        )
        decisions[key] = obj.to_dict()
    return decisions


def annotate_findings_with_object_intelligence(findings: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    findings_list = list(findings)
    decisions = build_object_decisions(findings_list)
    for item in findings_list:
        if str(item.get("parameter_code") or "") not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
            continue
        decision = decisions.get(_candidate_key(item))
        if not decision:
            continue
        item["object_intelligence_decision"] = decision["decision"]
        item["object_intelligence_confidence"] = decision["confidence"]
        item["object_intelligence_reason"] = decision["reason"]
        item["object_independent_documents"] = decision["independent_documents"]
    return decisions
