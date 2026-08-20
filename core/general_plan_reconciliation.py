from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable

OBJECT_CODES = {"OBJECT_ENTRY", "OBJECT_CANDIDATE"}
SECTION_GROUPS = {
    "ПЗ": "ПЗ", "ПЗ XML": "ПЗ", "XML": "ПЗ",
    "ПЗУ1": "ПЗУ", "ПЗУ2": "ПЗУ",
    "АР1": "АР", "АР2": "АР",
    "КР1": "КР", "КР2": "КР",
    "ТХ1": "ТХ", "ТХ2": "ТХ",
    "ИОС1": "ИОС", "ИОС1.1": "ИОС", "ИОС2": "ИОС", "ИОС2.1": "ИОС",
    "ПОС1": "ПОС", "ПОС2": "ПОС",
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _norm(value: Any) -> str:
    text = _clean(value).lower().replace("ё", "е")
    text = re.sub(r"^\d+(?:\.\d+)*\s*[-–—.:]?\s*", "", text)
    text = re.sub(r"[^а-яa-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _section(item: dict[str, Any]) -> str:
    raw = _clean(item.get("document_type") or item.get("section"))
    if raw in SECTION_GROUPS:
        return SECTION_GROUPS[raw]
    for prefix, group in SECTION_GROUPS.items():
        if raw.startswith(prefix):
            return group
    return raw or "Не определён"


def _name_score(source: str, target: str) -> float:
    a, b = _norm(source), _norm(target)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.88
    aa, bb = set(a.split()), set(b.split())
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def anchor_findings_to_general_plan(
    findings: list[dict[str, Any]],
    gp_findings: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Привязывает характеристики к объектам генплана только при однозначном совпадении.

    Приоритет: точная позиция -> точное/сильное наименование. Неоднозначные совпадения
    намеренно не применяются, чтобы не создавать ложные межраздельные расхождения.
    """
    anchors: list[dict[str, str]] = []
    by_position: dict[str, dict[str, str]] = {}
    for row in gp_findings:
        position = _clean(row.get("genplan_position"))
        name = _clean(row.get("object_hint") or row.get("value_text"))
        if not name:
            continue
        anchor = {"position": position, "name": name}
        anchors.append(anchor)
        if position:
            by_position[position] = anchor

    audit: list[dict[str, Any]] = []
    for item in findings:
        if item.get("parameter_code") in OBJECT_CODES:
            continue
        existing_position = _clean(item.get("semantic_anchor_position"))
        existing_name = _clean(item.get("semantic_anchor_name"))
        source_position = _clean(item.get("genplan_position"))
        source_name = _clean(item.get("object_hint"))

        if source_position and source_position in by_position:
            anchor = by_position[source_position]
            item["semantic_anchor_position"] = anchor["position"]
            item["semantic_anchor_name"] = anchor["name"]
            item["general_plan_anchor_method"] = "точная позиция генплана"
            item["general_plan_anchor_confidence"] = 1.0
            audit.append({"decision": "привязано", "method": "position", "position": anchor["position"], "name": anchor["name"], "document": item.get("document"), "page": item.get("page")})
            continue

        if existing_position or existing_name or not source_name:
            continue

        scored = sorted(((_name_score(source_name, a["name"]), a) for a in anchors), key=lambda x: x[0], reverse=True)
        if not scored:
            continue
        best_score, best = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else 0.0
        if best_score >= 0.86 and best_score - second_score >= 0.12:
            item["semantic_anchor_position"] = best["position"]
            item["semantic_anchor_name"] = best["name"]
            item["general_plan_anchor_method"] = "однозначное совпадение наименования"
            item["general_plan_anchor_confidence"] = round(best_score, 3)
            audit.append({"decision": "привязано", "method": "name", "score": round(best_score, 3), "position": best["position"], "name": best["name"], "source_name": source_name, "document": item.get("document"), "page": item.get("page")})
        elif best_score >= 0.65:
            audit.append({"decision": "не привязано", "method": "ambiguous_name", "score": round(best_score, 3), "second_score": round(second_score, 3), "candidate": best["name"], "source_name": source_name, "document": item.get("document"), "page": item.get("page")})
    return audit


def build_general_plan_document_checks(
    findings: Iterable[dict[str, Any]],
    gp_findings: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Сверяет каждый объект генплана с последующими разделами документации."""
    all_findings = list(findings)
    checks: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []

    for gp in gp_findings:
        position = _clean(gp.get("genplan_position"))
        name = _clean(gp.get("object_hint") or gp.get("value_text"))
        if not name:
            continue
        sections: set[str] = {"ПЗУ"}
        matched_findings = 0
        parameter_codes: set[str] = set()
        for item in all_findings:
            if item is gp:
                continue
            item_position = _clean(item.get("semantic_anchor_position") or item.get("genplan_position"))
            item_name = _clean(item.get("semantic_anchor_name") or item.get("object_hint"))
            match = bool(position and item_position == position) or _name_score(item_name, name) >= 0.88
            if not match:
                continue
            sections.add(_section(item))
            matched_findings += 1
            code = _clean(item.get("parameter_code"))
            if code and code not in OBJECT_CODES:
                parameter_codes.add(code)

        status = "ПОДТВЕРЖДЕНО" if len(sections - {"ПЗУ"}) >= 2 else ("ТРЕБУЕТ ПРОВЕРКИ" if sections - {"ПЗУ"} else "НЕ НАЙДЕН В ДРУГИХ РАЗДЕЛАХ")
        missing_pz = "ПЗ" not in sections
        coverage.append({
            "position": position,
            "name": name,
            "sections": sorted(sections),
            "status": status,
            "matched_findings": matched_findings,
            "parameter_count": len(parameter_codes),
            "missing_in_pz": missing_pz,
        })
        if missing_pz:
            checks.append({
                "category": "Сверка состава по генплану",
                "object": name,
                "genplan_position": position,
                "parameter_code": "OBJECT_PRESENCE_PZ",
                "parameter_name": "Наличие объекта генплана в ПЗ",
                "status": "ТРЕБУЕТ ПРОВЕРКИ",
                "severity": "warning",
                "sections": ", ".join(sorted(sections)),
                "values": "ПЗУ: найден; ПЗ: не найден",
                "explanation": "Объект обнаружен на генеральном плане, но не подтверждён в ПЗ.",
                "recommendation": "Проверить перечень объектов и сведения о сложном объекте в ПЗ.",
                "confidence": 0.98 if gp.get("general_plan_explication") else 0.84,
            })
    return checks, coverage


def build_general_plan_field_checks(gp_findings: Iterable[dict[str, Any]], audit: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Формирует явные результаты экспликация ↔ поле чертежа."""
    checks: list[dict[str, Any]] = []
    for gp in gp_findings:
        position = _clean(gp.get("genplan_position"))
        name = _clean(gp.get("object_hint") or gp.get("value_text"))
        if not position:
            continue
        confirmed = bool(gp.get("general_plan_field"))
        checks.append({
            "category": "Сверка генплана",
            "object": name,
            "genplan_position": position,
            "parameter_code": "GP_EXPLICATION_FIELD",
            "parameter_name": "Экспликация ↔ поле чертежа",
            "status": "СОВПАДАЕТ" if confirmed else "ТРЕБУЕТ ПРОВЕРКИ",
            "severity": "info" if confirmed else "warning",
            "sections": "ПЗУ2",
            "values": f"Экспликация: да; позиция на поле: {'да' if confirmed else 'не подтверждена'}",
            "explanation": "Позиция подтверждена на поле чертежа." if confirmed else "Позиция есть в экспликации, но независимое подтверждение на поле чертежа не получено.",
            "recommendation": "" if confirmed else "Визуально проверить наличие позиции на поле генерального плана.",
            "confidence": float(gp.get("confidence") or 0),
            "finding_type": "PROJECT_STATUS" if confirmed else "SYSTEM_LIMITATION",
            "user_status": "Проверено" if confirmed else "Ограничение автоматической проверки",
            "risk_eligible": False,
        })
    return checks
