from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from typing import Any, Iterable

from .object_semantics import is_service_object_candidate, classify_object, object_candidate_evidence

POSITION_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){1,5}$")
CLASSIFIER_RE = re.compile(r"^\d{2}\.\d{2}\.\d{3}\.\d{3}$")

SOURCE_WEIGHTS = {
    "ПЗ": 100,
    "ПЗУ1": 95,
    "ПЗУ2": 92,
    "XML": 95,
    "АР1": 90,
    "АР2": 88,
    "ТХ1": 90,
    "ТХ2": 88,
    "ИОС1": 85,
    "ИОС2": 85,
    "ПОС": 70,
    "ООС": 60,
}

STOP_WORDS = {
    "объект", "здание", "сооружение", "площадка", "проектируемый",
    "проектируемая", "проектируемое", "капитального", "строительства",
    "станция", "система", "комплекс",
}


@dataclass
class RegisterRecord:
    include: bool
    position: str
    parent_position: str
    name: str
    quantity: int
    quantity_status: str
    quantity_evidence: str
    sources: str
    confirmations: int
    status: str
    confidence: float
    pages: str
    original_names: str
    merge_method: str
    source_priority: int
    in_pz_registry: bool
    in_general_plan_explication: bool
    on_general_plan_drawing: bool
    source_conflict: str
    inspector_decision: str
    inspector_reasons: str
    object_type_code: str = "GENERIC_OBJECT"
    object_type_name: str = "Инженерный объект"
    object_type_confidence: float = 0.0

    def to_ui_dict(self) -> dict[str, Any]:
        return {
            "Включить": self.include,
            "Позиция по ГП": self.position,
            "Родительская позиция": self.parent_position,
            "Наименование объекта": self.name,
            "Количество": self.quantity,
            "Статус количества": self.quantity_status,
            "Основание количества": self.quantity_evidence,
            "Источники": self.sources,
            "Подтверждений": self.confirmations,
            "Статус": self.status,
            "Уверенность": self.confidence,
            "Страницы": self.pages,
            "Исходные наименования": self.original_names,
            "Способ объединения": self.merge_method,
            "Приоритет источника": self.source_priority,
            "В ПЗ": self.in_pz_registry,
            "В экспликации ГП": self.in_general_plan_explication,
            "На поле генплана": self.on_general_plan_drawing,
            "Конфликт источников": self.source_conflict,
            "Решение инспектора": self.inspector_decision,
            "Причины решения": self.inspector_reasons,
            "Тип объекта": self.object_type_name,
            "Код типа объекта": self.object_type_code,
            "Уверенность типа": self.object_type_confidence,
        }


def normalize_position(value: Any) -> str:
    clean = re.sub(r"\s+", "", str(value or "").strip())
    if POSITION_RE.fullmatch(clean) and not CLASSIFIER_RE.fullmatch(clean):
        return clean
    return ""


def parent_position(position: str) -> str:
    parts = normalize_position(position).split(".")
    return ".".join(parts[:-1]) if len(parts) > 2 else ""


def normalize_name(value: Any) -> str:
    text = str(value or "").lower().replace("ё", "е")
    text = re.sub(r"^\s*\d{1,3}(?:\.\d{1,3}){1,5}\s*[-–—:]?\s*", "", text)
    text = re.sub(r"[^а-яa-z0-9№]+", " ", text)
    words = [word for word in text.split() if word not in STOP_WORDS]
    return " ".join(words).strip()


def name_similarity(left: Any, right: Any) -> float:
    a, b = normalize_name(left), normalize_name(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return min(len(a), len(b)) / max(len(a), len(b)) * 0.94 + 0.04
    aw, bw = set(a.split()), set(b.split())
    token_score = len(aw & bw) / max(1, len(aw | bw))
    sequence_score = SequenceMatcher(None, a, b).ratio()
    return round(0.62 * token_score + 0.38 * sequence_score, 4)


def _source_weight(document_type: Any) -> int:
    return SOURCE_WEIGHTS.get(str(document_type or "").strip(), 50)


def _quantity(value: Any) -> int:
    try:
        return max(1, int(round(float(value))))
    except (TypeError, ValueError):
        return 1


def _candidate_name(item: dict[str, Any]) -> str:
    return str(item.get("value_text") or item.get("object_hint") or "").strip()


def _is_valid_candidate(item: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    name = _candidate_name(item)
    position = normalize_position(item.get("genplan_position"))
    code = str(item.get("parameter_code") or "")
    if code not in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}:
        return False, ["не является объектной находкой"]
    service, service_reasons = is_service_object_candidate(item)
    if service:
        return False, service_reasons
    evidence_strength, evidence_reasons = object_candidate_evidence(item)
    if evidence_strength <= 0:
        return False, evidence_reasons
    item["_object_evidence_strength"] = evidence_strength
    if not name or len(normalize_name(name)) < 2:
        return False, ["пустое или слишком короткое наименование"]
    low = name.lower()
    bad_tokens = (
        "ситуационный план", "условные обозначения", "экспликация помещений",
        "ведомость ссылочных", "план на отм", "разрез ", "спецификация",
        "технико-экономические показатели", "наименование объекта капитального",
    )
    if any(token in low for token in bad_tokens):
        return False, ["служебный заголовок или название чертежа"]
    reasons.extend(evidence_reasons)
    if position:
        reasons.append("найдена точная позиция по генплану")
    if code == "OBJECT_ENTRY":
        reasons.append("строка официального реестра ПЗ")
    else:
        reasons.append("кандидат из смежного раздела")
    return True, reasons


class ObjectRegisterEngine:
    """Формирует проектный реестр объектов из объектных находок.

    Принципы:
    * точная позиция по генплану является первичным ключом;
    * родительская и дочерняя позиции никогда не объединяются;
    * запись без позиции присоединяется только при однозначном совпадении имени;
    * ПЗ задаёт опорное наименование, остальные разделы подтверждают его;
    * каждое решение сопровождается диагностикой для режима «Инспектор».
    """

    def build(self, findings: Iterable[dict[str, Any]]) -> tuple[list[RegisterRecord], list[dict[str, Any]]]:
        candidates: list[dict[str, Any]] = []
        audit: list[dict[str, Any]] = []
        for idx, raw in enumerate(findings):
            item = dict(raw)
            accepted, reasons = _is_valid_candidate(item)
            audit_row = {
                "candidate_id": idx,
                "document": item.get("document", ""),
                "document_type": item.get("document_type", ""),
                "page": item.get("page", ""),
                "position": normalize_position(item.get("genplan_position")),
                "name": _candidate_name(item),
                "decision": "принято" if accepted else "отклонено",
                "reasons": "; ".join(reasons),
                "matched_position": "",
                "match_score": 0.0,
                "merge_method": "",
            }
            audit.append(audit_row)
            if accepted:
                item["_candidate_id"] = idx
                item["_position"] = normalize_position(item.get("genplan_position"))
                item["_name"] = _candidate_name(item)
                item["_source_weight"] = _source_weight(item.get("document_type"))
                candidates.append(item)

        positioned: dict[str, list[dict[str, Any]]] = {}
        unpositioned: list[dict[str, Any]] = []
        for item in candidates:
            if item["_position"]:
                positioned.setdefault(item["_position"], []).append(item)
            else:
                unpositioned.append(item)

        # Записи без позиции могут только подтверждать уже существующую позицию.
        standalone: list[list[dict[str, Any]]] = []
        for item in unpositioned:
            scores: list[tuple[float, str]] = []
            for position, group in positioned.items():
                best = max(name_similarity(item["_name"], row["_name"]) for row in group)
                scores.append((best, position))
            scores.sort(reverse=True)
            top = scores[0] if scores else (0.0, "")
            second = scores[1][0] if len(scores) > 1 else 0.0
            audit_row = audit[item["_candidate_id"]]
            audit_row["match_score"] = top[0]
            if top[0] >= 0.88 and top[0] - second >= 0.08:
                positioned[top[1]].append(item)
                audit_row["matched_position"] = top[1]
                audit_row["merge_method"] = "однозначное совпадение наименования с реестровой позицией"
                audit_row["reasons"] += "; присоединено к позиции по однозначному совпадению"
            else:
                # Безпозиционный кандидат сам по себе не создаёт объект. Он должен
                # иметь сильное основание либо подтверждаться минимум двумя независимыми разделами.
                attached = False
                for group in standalone:
                    score = max(name_similarity(item["_name"], row["_name"]) for row in group)
                    if score >= 0.94:
                        group.append(item)
                        attached = True
                        audit_row["merge_method"] = "совпадение безпозиционных наименований"
                        break
                if not attached:
                    standalone.append([item])
                audit_row["reasons"] += "; ожидается подтверждение независимым источником"

        records: list[RegisterRecord] = []
        for position in sorted(positioned, key=self._position_sort_key):
            records.append(self._make_record(positioned[position], position))
        for group in standalone:
            sections = {str(row.get("document_type") or "") for row in group if row.get("document_type")}
            max_strength = max(int(row.get("_object_evidence_strength") or 0) for row in group)
            official = any(row.get("parameter_code") == "OBJECT_ENTRY" for row in group)
            if official or max_strength >= 2 or len(sections) >= 2:
                records.append(self._make_record(group, ""))
            else:
                for row in group:
                    a = audit[row["_candidate_id"]]
                    a["decision"] = "отклонено"
                    a["reasons"] += "; недостаточно оснований для включения в подтверждённый реестр"
        return records, audit

    @staticmethod
    def _position_sort_key(position: str) -> tuple[int, ...]:
        return tuple(int(part) for part in position.split("."))

    def _make_record(self, group: list[dict[str, Any]], position: str) -> RegisterRecord:
        ranked = sorted(
            group,
            key=lambda row: (
                str(row.get("parameter_code")) == "OBJECT_ENTRY",
                row.get("_source_weight", 0),
                float(row.get("confidence") or 0),
                len(row.get("_name", "")),
            ),
            reverse=True,
        )
        best = ranked[0]
        names = list(dict.fromkeys(row["_name"] for row in ranked if row["_name"]))
        sources = sorted({str(row.get("document_type") or "") for row in group if row.get("document_type")})
        pages = sorted({f"{row.get('document_type', '')}: стр. {row.get('page', '')}" for row in group})
        confirmations = len(sources)
        has_pz_registry = any(
            row.get("parameter_code") == "OBJECT_ENTRY" and row.get("document_type") == "ПЗ"
            for row in group
        )
        in_gp_explication = any(bool(row.get("general_plan_explication")) for row in group)
        on_gp_drawing = any(bool(row.get("general_plan_field")) for row in group)
        confidence = max(float(row.get("confidence") or 0) for row in group)

        explicit_quantity_rows = [
            row for row in group
            if "определено явно" in str(row.get("review_note") or "").lower()
        ]
        preferred_quantity_rows = [
            row for row in explicit_quantity_rows
            if row.get("parameter_code") == "OBJECT_ENTRY" and row.get("document_type") == "ПЗ"
        ] or explicit_quantity_rows
        if preferred_quantity_rows:
            quantity_values = [_quantity(row.get("value")) for row in preferred_quantity_rows]
            quantity = quantity_values[0]
            distinct_quantities = sorted(set(quantity_values))
            if len(distinct_quantities) > 1:
                quantity_status = "Требует проверки"
            else:
                quantity_status = "Подтверждено явным указанием"
            quantity_evidence = " | ".join(
                str(row.get("review_note") or "") for row in preferred_quantity_rows
            )
        else:
            quantity = 1
            quantity_status = "Не указано — принято 1"
            quantity_evidence = "В источниках не найдено явное количество"

        if has_pz_registry and in_gp_explication:
            status = "Подтверждено ПЗ и генпланом"
        elif in_gp_explication and not has_pz_registry:
            status = "Обнаружено на генплане — отсутствует в ПЗ"
        elif has_pz_registry and confirmations >= 2:
            status = "Подтверждено несколькими разделами"
        elif has_pz_registry:
            status = "Подтверждено реестром ПЗ"
        elif position and confirmations >= 2:
            status = "Частично подтверждено"
        else:
            status = "Требует подтверждения"
        method = "Точная позиция по генплану"
        if not position:
            method = "Только по наименованию — требуется подтверждение"
        elif any(not row.get("_position") for row in group):
            method = "Позиция + однозначное совпадение наименования"
        pz_names = {normalize_name(row.get("_name")) for row in group if row.get("document_type") == "ПЗ" and row.get("_name")}
        gp_names = {normalize_name(row.get("_name")) for row in group if row.get("general_plan_explication") and row.get("_name")}
        source_conflict = ""
        if pz_names and gp_names and max(name_similarity(a, b) for a in pz_names for b in gp_names) < 0.78:
            source_conflict = "Различаются наименования в ПЗ и экспликации генплана"

        reasons = [
            f"опорный источник: {best.get('document_type', 'не определён')}",
            f"источников подтверждения: {confirmations}",
            f"количество: {quantity_status}",
        ]
        if position:
            reasons.append("точная позиция используется как первичный ключ")
        if has_pz_registry:
            reasons.append("присутствует строка официального реестра ПЗ")
        type_decision = classify_object(best["_name"])
        return RegisterRecord(
            include=True,
            position=position,
            parent_position=parent_position(position),
            name=best["_name"],
            quantity=quantity,
            quantity_status=quantity_status,
            quantity_evidence=quantity_evidence,
            sources=", ".join(sources),
            confirmations=confirmations,
            status=status,
            confidence=confidence,
            pages="; ".join(pages),
            original_names=" | ".join(names),
            merge_method=method,
            source_priority=max(row.get("_source_weight", 0) for row in group),
            in_pz_registry=has_pz_registry,
            in_general_plan_explication=in_gp_explication,
            on_general_plan_drawing=on_gp_drawing,
            source_conflict=source_conflict,
            inspector_decision="принято в реестр",
            inspector_reasons="; ".join(reasons),
            object_type_code=type_decision.code,
            object_type_name=type_decision.name,
            object_type_confidence=type_decision.confidence,
        )


def build_registry(findings: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records, audit = ObjectRegisterEngine().build(findings)
    return [record.to_ui_dict() for record in records], audit
