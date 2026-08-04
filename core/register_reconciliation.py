from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable

from .object_register_engine import normalize_position, normalize_name, name_similarity, parent_position
from .object_identity import ObjectIdentityEngine

SOURCE_GROUPS = {
    "PZ": {"ПЗ"},
    "GENERAL_PLAN": {"ПЗУ1", "ПЗУ2"},
    "SECTIONS": {"АР1", "АР2", "ТХ1", "ТХ2", "ИОС1", "ИОС2", "ПОС", "ООС", "ПБ", "КР"},
    "XML": {"XML"},
}

SOURCE_LABELS = {
    "PZ": "ПЗ",
    "GENERAL_PLAN": "Генплан",
    "SECTIONS": "Разделы ПД",
    "XML": "XML",
}


@dataclass
class ReconciledObject:
    position: str
    parent_position: str
    accepted_name: str
    quantity: int
    in_pz: bool
    in_general_plan: bool
    in_sections: bool
    in_xml: bool
    source_count: int
    status: str
    conflicts: str
    source_names: dict[str, list[str]]
    source_documents: dict[str, list[str]]
    confidence: float
    identity_method: str
    accepted_name_source: str
    name_confidence: float
    quantity_status: str
    quantity_source: str
    quantity_confidence: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.update({
            "Позиция по ГП": self.position,
            "Родительская позиция": self.parent_position,
            "Наименование объекта": self.accepted_name,
            "Количество": self.quantity,
            "В ПЗ": self.in_pz,
            "В генплане": self.in_general_plan,
            "В разделах ПД": self.in_sections,
            "В XML": self.in_xml,
            "Количество источников": self.source_count,
            "Статус консолидации": self.status,
            "Конфликты": self.conflicts,
            "Уверенность консолидации": self.confidence,
            "Способ идентификации": self.identity_method,
            "Источник принятого наименования": self.accepted_name_source,
            "Уверенность наименования": self.name_confidence,
            "Статус количества": self.quantity_status,
            "Источник количества": self.quantity_source,
            "Уверенность количества": self.quantity_confidence,
        })
        return data


def _source_group(item: dict[str, Any]) -> str:
    if item.get("general_plan_explication") or item.get("general_plan_field"):
        return "GENERAL_PLAN"
    doc_type = str(item.get("document_type") or "").strip()
    for group, types in SOURCE_GROUPS.items():
        if doc_type in types:
            return group
    return "SECTIONS"


def _is_object_finding(item: dict[str, Any]) -> bool:
    return str(item.get("parameter_code") or "") in {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}


def _name(item: dict[str, Any]) -> str:
    return str(item.get("value_text") or item.get("object_hint") or "").strip()


def _quantity(item: dict[str, Any]) -> int:
    try:
        return max(1, int(round(float(item.get("quantity") or item.get("value") or 1))))
    except (TypeError, ValueError):
        return 1


class RegisterReconciliationEngine:
    """Строит универсальный консолидированный реестр из независимых источников.

    Ядро не использует отраслевые названия объектов. Первичным ключом является
    точная позиция по генплану. Записи без позиции могут только подтверждать
    существующую позицию при однозначном совпадении наименования.
    """

    def __init__(self) -> None:
        self.identity = ObjectIdentityEngine()

    def reconcile(self, findings: Iterable[dict[str, Any]]) -> tuple[list[ReconciledObject], list[dict[str, Any]]]:
        positioned: dict[str, list[dict[str, Any]]] = {}
        unpositioned: list[dict[str, Any]] = []
        audit: list[dict[str, Any]] = []

        for index, raw in enumerate(findings):
            item = dict(raw)
            if not _is_object_finding(item):
                continue
            name = _name(item)
            if not normalize_name(name):
                continue
            item["_name"] = name
            item["_position"] = normalize_position(item.get("genplan_position"))
            item["_group"] = _source_group(item)
            item["_index"] = index
            if item["_position"]:
                positioned.setdefault(item["_position"], []).append(item)
            else:
                unpositioned.append(item)

        # Безпозиционные сведения не создают новую официальную позицию, если есть
        # однозначный позиционный кандидат. Иначе они сохраняются как кандидаты.
        standalone_groups: list[list[dict[str, Any]]] = []
        for item in unpositioned:
            matched_position, decision, second = self.identity.best_position_match(item, positioned)
            top_score = decision.score if decision else 0.0
            if matched_position:
                item["_identity_method"] = decision.method if decision else ""
                positioned[matched_position].append(item)
                audit.append({
                    "candidate": item["_name"], "position": "", "decision": "merged",
                    "matched_position": matched_position, "score": round(top_score, 3),
                    "second_score": round(second, 3),
                    "identity_method": decision.method if decision else "",
                    "reason": "; ".join(decision.reasons) if decision else "однозначное соответствие",
                })
                continue
            attached = False
            for group in standalone_groups:
                score = max(self.identity.compare(item["_name"], row["_name"]).score for row in group)
                if score >= 0.95:
                    group.append(item)
                    attached = True
                    break
            if not attached:
                standalone_groups.append([item])
            audit.append({
                "candidate": item["_name"], "position": "", "decision": "standalone",
                "matched_position": "", "score": round(top_score, 3),
                "reason": "нет однозначного позиционного соответствия",
            })

        records: list[ReconciledObject] = []
        for position in sorted(positioned, key=lambda x: tuple(int(p) for p in x.split("."))):
            records.append(self._build(positioned[position], position))
        for group in standalone_groups:
            records.append(self._build(group, ""))
        return records, audit

    def _build(self, group: list[dict[str, Any]], position: str) -> ReconciledObject:
        by_source: dict[str, list[dict[str, Any]]] = {key: [] for key in SOURCE_GROUPS}
        for item in group:
            by_source.setdefault(item["_group"], []).append(item)

        # Приоритет принятого имени: ПЗ -> Генплан -> XML -> остальные разделы.
        priority = ["PZ", "GENERAL_PLAN", "XML", "SECTIONS"]
        chosen = None
        for source in priority:
            if by_source.get(source):
                chosen = max(by_source[source], key=lambda row: (float(row.get("confidence") or 0), len(row["_name"])))
                break
        chosen = chosen or group[0]
        chosen_source = SOURCE_LABELS.get(str(chosen.get("_group") or ""), str(chosen.get("_group") or ""))

        source_names = {
            SOURCE_LABELS.get(source, source): list(dict.fromkeys(row["_name"] for row in rows))
            for source, rows in by_source.items() if rows
        }
        source_documents = {
            SOURCE_LABELS.get(source, source): sorted({str(row.get("document") or "") for row in rows if row.get("document")})
            for source, rows in by_source.items() if rows
        }

        all_names = [row["_name"] for row in group]
        conflicts: list[str] = []
        if len(all_names) > 1:
            min_score = min(name_similarity(chosen["_name"], name) for name in all_names)
            if min_score < 0.72:
                conflicts.append("существенно различаются наименования источников")

        quantity_rows = [row for row in group if row.get("quantity") not in (None, "")]
        quantities = {_quantity(row) for row in quantity_rows}
        quantity_priority = {"PZ": 100, "GENERAL_PLAN": 95, "XML": 95, "SECTIONS": 80}
        explicit_rows = [row for row in quantity_rows if str(row.get("quantity_evidence") or row.get("quantity_reason") or "").strip()]
        ranked_quantity_rows = explicit_rows or quantity_rows
        if ranked_quantity_rows:
            quantity_row = max(ranked_quantity_rows, key=lambda row: (quantity_priority.get(row.get("_group"), 0), float(row.get("confidence") or 0)))
            quantity = _quantity(quantity_row)
            quantity_source = SOURCE_LABELS.get(quantity_row.get("_group"), str(quantity_row.get("_group") or ""))
            quantity_confidence = min(1.0, 0.72 + (0.18 if explicit_rows else 0.0) + (0.08 if len(quantities) == 1 else 0.0))
        else:
            quantity = 1
            quantity_source = "По умолчанию"
            quantity_confidence = 0.45
        if len(quantities) > 1:
            conflicts.append("различается физическое количество")
            quantity_status = "Требует проверки"
            quantity_confidence = min(quantity_confidence, 0.55)
        elif quantity_rows:
            quantity_status = "Подтверждено"
        else:
            quantity_status = "Не указано — принято 1"

        presence = {
            "PZ": bool(by_source.get("PZ")),
            "GENERAL_PLAN": bool(by_source.get("GENERAL_PLAN")),
            "SECTIONS": bool(by_source.get("SECTIONS")),
            "XML": bool(by_source.get("XML")),
        }
        count = sum(presence.values())
        if presence["GENERAL_PLAN"] and not presence["PZ"]:
            status = "Есть на генплане — отсутствует в ПЗ"
        elif presence["PZ"] and not presence["GENERAL_PLAN"]:
            status = "Есть в ПЗ — не подтверждено генпланом"
        elif conflicts:
            status = "Конфликт источников"
        elif count >= 3:
            status = "Подтверждено тремя и более источниками"
        elif count == 2:
            status = "Подтверждено двумя источниками"
        else:
            status = "Найдено только в одном источнике"

        identity_scores = [self.identity.compare(chosen["_name"], name).score for name in all_names]
        name_confidence = round(sum(identity_scores) / max(1, len(identity_scores)), 3)
        identity_methods = [str(row.get("_identity_method") or "") for row in group if row.get("_identity_method")]
        identity_method = "exact_position" if position else (identity_methods[0] if identity_methods else "standalone_name")
        base_conf = min(1.0, 0.40 + 0.15 * count + (0.16 if position else 0.0) + 0.12 * name_confidence - 0.12 * len(conflicts))
        return ReconciledObject(
            position=position,
            parent_position=parent_position(position),
            accepted_name=chosen["_name"],
            quantity=quantity,
            in_pz=presence["PZ"],
            in_general_plan=presence["GENERAL_PLAN"],
            in_sections=presence["SECTIONS"],
            in_xml=presence["XML"],
            source_count=count,
            status=status,
            conflicts="; ".join(conflicts),
            source_names=source_names,
            source_documents=source_documents,
            confidence=round(max(0.0, base_conf), 3),
            identity_method=identity_method,
            accepted_name_source=chosen_source,
            name_confidence=name_confidence,
            quantity_status=quantity_status,
            quantity_source=quantity_source,
            quantity_confidence=round(quantity_confidence, 3),
        )


def reconcile_register(findings: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records, audit = RegisterReconciliationEngine().reconcile(findings)
    return [record.to_dict() for record in records], audit
