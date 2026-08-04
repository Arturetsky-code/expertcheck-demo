from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any

from .object_identity import ObjectIdentityEngine
from .normalization import normalize_text


_TOLERANCES: dict[str, tuple[float, float, str]] = {
    "AREA_BUILD": (0.1, 0.001, "Высокий"),
    "AREA_TOTAL": (0.1, 0.001, "Высокий"),
    "VOLUME_BUILD": (1.0, 0.002, "Высокий"),
    "HEIGHT_BUILD": (0.05, 0.002, "Средний"),
    "FLOORS": (0.0, 0.0, "Высокий"),
    "CAPACITY": (0.01, 0.002, "Высокий"),
    "RES_VOLUME": (0.1, 0.001, "Высокий"),
    "POWER_KTP": (1.0, 0.002, "Высокий"),
    "POWER_INSTALLED": (1.0, 0.002, "Высокий"),
    "POWER_CALCULATED": (1.0, 0.002, "Высокий"),
    "PERSONNEL": (0.0, 0.0, "Средний"),
    "LENGTH": (0.1, 0.001, "Средний"),
    "QUANTITY": (0.0, 0.0, "Высокий"),
}


def _section(item: dict[str, Any]) -> str:
    return str(item.get("section") or item.get("document_type") or "").strip()


def _value(item: dict[str, Any]) -> float | None:
    value = item.get("value_num")
    if value is None:
        value = item.get("value")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None




def _context_supports_object(candidate: dict[str, Any], object_name: str) -> bool:
    """Проверяет локальную связь значения PDF с объектом.

    Это защитный барьер против ситуации, когда общий контекст большой таблицы
    содержит несколько объектов, а legacy-парсер присвоил значение соседней строке.
    """
    context = normalize_text(candidate.get("context") or "")
    name = normalize_text(object_name)
    if not context or not name or name not in context:
        return False
    value = _value(candidate)
    if value is None:
        return False
    variants = {f"{value:g}", f"{value:g}".replace(".", ",")}
    positions = [context.find(v) for v in variants if v and context.find(v) >= 0]
    if not positions:
        return False
    value_pos = min(positions)
    name_pos = context.rfind(name, 0, value_pos + 1)
    return name_pos >= 0 and 0 <= value_pos - (name_pos + len(name)) <= 180

def _best_object_match(xml_item: dict[str, Any], candidates: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float, list[str]]:
    xml_name = str(xml_item.get("object_hint") or "").strip()
    if not xml_name or xml_name == "Не определён":
        return None, 0.0, ["в XML не определён объект"]
    best = None
    best_score = 0.0
    best_reasons: list[str] = []
    for candidate in candidates:
        name = str(candidate.get("object_hint") or "").strip()
        if not name or name == "Не определён":
            continue
        if not _context_supports_object(candidate, xml_name):
            continue
        decision = ObjectIdentityEngine().compare(
            xml_name,
            name,
            str(xml_item.get("genplan_position") or ""),
            str(candidate.get("genplan_position") or ""),
        )
        score = float(decision.score)
        if score > best_score:
            best = candidate
            best_score = score
            best_reasons = list(decision.reasons)
    return best, best_score, best_reasons


def build_pdf_xml_checks(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Формирует отдельные объяснимые проверки PDF ↔ XML.

    Сравнение выполняется только для нормализованных числовых характеристик.
    XML не считается автоматически истинным источником: при расхождении
    формируется конфликт, требующий инженерной проверки.
    """
    xml_findings = [f for f in findings if f.get("source_kind") == "xml" and f.get("parameter_code") in _TOLERANCES and _value(f) is not None]
    pdf_findings = [f for f in findings if f.get("source_kind") != "xml" and f.get("parameter_code") in _TOLERANCES and _value(f) is not None]
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in pdf_findings:
        by_code[str(item.get("parameter_code"))].append(item)

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for xml_item in xml_findings:
        code = str(xml_item.get("parameter_code"))
        candidate, identity_score, identity_reasons = _best_object_match(xml_item, by_code.get(code, []))
        if candidate is None or identity_score < 0.72:
            continue
        xml_object = str(xml_item.get("object_hint") or "")
        pdf_object = str(candidate.get("object_hint") or "")
        key = (code, normalize_text(xml_object), str(candidate.get("document") or ""))
        if key in seen:
            continue
        seen.add(key)

        xml_value = _value(xml_item)
        pdf_value = _value(candidate)
        if xml_value is None or pdf_value is None:
            continue
        abs_tol, rel_tol, priority = _TOLERANCES[code]
        same = math.isclose(xml_value, pdf_value, abs_tol=abs_tol, rel_tol=rel_tol)
        unit = str(xml_item.get("unit") or candidate.get("unit") or "")
        parameter_name = str(xml_item.get("parameter_name") or candidate.get("parameter_name") or code)
        status = "СОВПАДАЕТ" if same else "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ"
        check_code = f"XML-PDF-{code}-{re.sub(r'[^A-Za-zА-Яа-я0-9]+', '-', xml_object)[:28]}"
        rows.append({
            "check_code": check_code,
            "object": xml_object or pdf_object,
            "parameter_code": code,
            "parameter_name": parameter_name,
            "unit": unit,
            "priority": priority,
            "rule_name": "Соответствие структурированной ПЗ XML и проектной документации PDF",
            "category": "Согласованность PDF ↔ XML",
            "check_type": "Межформатная сверка",
            "rationale": "Одинаковая характеристика одного объекта должна быть согласована между структурированной ПЗ XML и PDF-разделами проекта.",
            "expected_documents": "ПЗ XML, PDF",
            "tolerance": f"абс. {abs_tol:g}; отн. {rel_tol:.3%}",
            "evidence_level": "Высокий" if identity_score >= 0.9 else "Средний",
            "evidence_count": 2,
            "rejected_count": 0,
            "status": status,
            "min_value": min(xml_value, pdf_value),
            "max_value": max(xml_value, pdf_value),
            "difference": abs(xml_value - pdf_value),
            "documents": f"ПЗ XML, {_section(candidate)}",
            "document_values": f"ПЗ XML: {xml_value:g} {unit} | {_section(candidate)}: {pdf_value:g} {unit}",
            "sources": f"{xml_item.get('document')}: {xml_item.get('value_text')} | {candidate.get('document')}, стр. {candidate.get('page')}: {candidate.get('value_text')}",
            "comment": "Значения согласованы." if same else "Проверить, синхронизированы ли XML ПЗ и соответствующий PDF-раздел.",
            "explanation": (
                f"Сопоставление объектов: {identity_score:.0%}. "
                f"Признаки: {', '.join(identity_reasons) or 'сходство наименований'}. "
                f"Сравнены XML и {_section(candidate)} с допуском {abs_tol:g}."
            ),
            "identity_score": round(identity_score, 3),
            "rule_source": "core/xml",
            "knowledge_rule_code": "CORE-XML-001",
            "knowledge_rule_name": "Согласованность PDF и XML",
        })
    order = {"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ": 0, "СОВПАДАЕТ": 1}
    rows.sort(key=lambda x: (order.get(x["status"], 9), x["object"], x["parameter_name"]))
    return rows
