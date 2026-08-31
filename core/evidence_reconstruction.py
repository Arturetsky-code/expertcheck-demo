from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any, Iterable

from .normalization import normalize_text
from .page_evidence_store import canonical_section, is_assignment_source


ENGINE_VERSION = "1.0-exact-span-material-reconstruction"

_HIGH_VALUE_PATTERNS = {
    "BULK_DENSITY": [re.compile(
        r"(?:насыпн\w*\s+(?:плотност\w*|масс\w*)|плотност\w*\s+(?:насыпн\w*\s+)?(?:материал\w*|сырь\w*)?)"
        r"[^.;]{0,100}?(?P<value>\d{1,4}(?:[,.]\d+)?)\s*"
        r"(?P<unit>т\s*/\s*м[³3]|кг\s*/\s*м[³3])",
        re.I | re.S,
    ), re.compile(
        r"насыпн\w*\s+(?:плотност\w*|масс\w*)[^.;]{0,50}?(?P<unit>т\s*/\s*м[³3]|кг\s*/\s*м[³3])"
        r"[^.;]{0,100}?исходн\w*\s+руд\w*[^.;]{0,40}?(?P<value>\d{1,4}(?:[,.]\d+)?)",
        re.I | re.S,
    ), re.compile(
        r"насыпн\w*\s+(?:плотност\w*|масс\w*)[^.;]{0,50}?(?P<unit>т\s*/\s*м[³3]|кг\s*/\s*м[³3])"
        r"[^.;]{0,150}?дробленн\w*\s+руд\w*[^.;]{0,40}?(?P<value>\d{1,4}(?:[,.]\d+)?)",
        re.I | re.S,
    )],
    "MOISTURE": [re.compile(
        r"(?:влажност\w*|массов\w*\s+дол\w*\s+влаг\w*)"
        r"[^.;]{0,100}?(?P<value>\d{1,3}(?:[,.]\d+)?)\s*(?P<unit>%)",
        re.I | re.S,
    ), re.compile(
        r"(?:влажност\w*|массов\w*\s+дол\w*\s+влаг\w*)"
        r"[^.;]{0,50}?(?P<unit>%)[^.;]{0,50}?(?P<value>\d{1,3}(?:[,.]\d+)?)",
        re.I | re.S,
    )],
    "POWER_INSTALLED": [re.compile(
        r"установленн\w*\s+мощност\w*[^\n.;]{0,100}?(?P<value>\d{1,7}(?:[,.]\d+)?)\s*(?P<unit>квт|мвт)",
        re.I | re.S,
    )],
    "PRESSURE": [re.compile(
        r"(?:рабоч\w*\s+|расчетн\w*\s+|расчётн\w*\s+)?давлен\w*[^\n.;]{0,80}?(?P<value>\d{1,4}(?:[,.]\d+)?)\s*(?P<unit>бар|мпа|кпа)",
        re.I | re.S,
    )],
    "VOLTAGE": [re.compile(
        r"напряжен\w*[^\n.;]{0,80}?(?P<value>\d{1,3}(?:[,.]\d+)?(?:\s*/\s*\d{1,3}(?:[,.]\d+)?)?)\s*(?P<unit>кв|в)",
        re.I | re.S,
    )],
    "RES_VOLUME": [re.compile(
        r"(?:аккумулирующ\w*\s+е?мкост\w*|резервуар\w*)[\s\S]{0,500}?(?:объе?м\w*[\s\S]{0,40}?)"
        r"(?P<value>\d{1,7}(?:[,.]\d+)?)\s*(?P<unit>м[³3])",
        re.I | re.S,
    )],
}

_PARAMETER_NAMES = {
    "BULK_DENSITY": "Насыпная плотность",
    "MOISTURE": "Влажность материала",
    "POWER_INSTALLED": "Установленная мощность",
    "PRESSURE": "Давление",
    "VOLTAGE": "Напряжение",
    "RES_VOLUME": "Объём резервуара / ёмкости",
}

_SCOPES = {
    "BULK_DENSITY": ("MATERIAL_OR_PROCESS", "MATERIAL", "Материал / технологический поток"),
    "MOISTURE": ("MATERIAL_OR_PROCESS", "MATERIAL", "Материал / технологический поток"),
    "POWER_INSTALLED": ("SYSTEM_OR_EQUIPMENT", "EQUIPMENT", "Инженерная система / оборудование"),
    "PRESSURE": ("SYSTEM_OR_EQUIPMENT", "SYSTEM", "Инженерная система / оборудование"),
    "VOLTAGE": ("SYSTEM_OR_EQUIPMENT", "SYSTEM", "Система электроснабжения / оборудование"),
    "RES_VOLUME": ("EQUIPMENT_OR_OBJECT", "EQUIPMENT", "Аккумулирующая ёмкость / резервуар"),
}

_MATERIAL_WORDS = (
    "щебень", "песок", "грунт", "руда", "уголь", "сера", "сырьё", "сырье",
    "порода", "концентрат", "материал", "смесь", "гравий", "цемент",
)


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = "|".join(str(part or "") for part in parts)
    digest = hashlib.sha1(payload.encode("utf-8", "ignore")).hexdigest()[:14].upper()
    return f"{prefix}-{digest}"


def _number(value: Any) -> float | None:
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _material_owner(text: str, start: int) -> str:
    window = text[max(0, start - 220): start + 120]
    low = normalize_text(window).lower().replace("ё", "е")
    for word in _MATERIAL_WORDS:
        normalized = word.replace("ё", "е")
        if normalized in low:
            return word.capitalize()
    return "Материал / технологический поток"


def _exact_span(text: str, start: int, end: int) -> tuple[str, int, int]:
    left = max(text.rfind(".", 0, start), text.rfind(";", 0, start), text.rfind("\n", 0, start))
    right_candidates = [position for position in (text.find(".", end), text.find(";", end), text.find("\n", end)) if position >= 0]
    span_start = max(0, left + 1, start - 180)
    span_end = min(len(text), min(right_candidates) + 1 if right_candidates else end + 220)
    return re.sub(r"\s+", " ", text[span_start:span_end]).strip(), span_start, span_end


def sanitize_high_value_facts(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Apply semantic unit/scope guards before facts reach comparison engines."""
    summary = {
        "flow_false_positives_blocked": 0,
        "material_scope_rebound": 0,
        "non_admitted_facts_excluded": 0,
    }
    for row in findings or []:
        code = str(row.get("parameter_code") or "").upper()
        unit = normalize_text(row.get("unit") or row.get("units") or "").lower().replace(" ", "")
        if code == "FLOW_RATE" and not any(token in unit for token in ("/ч", "/час", "/с", "/сут")):
            row.update({
                "fact_admission_decision": "REJECT",
                "evidence_quality_decision": "REJECT",
                "comparison_excluded": True,
                "engineering_plausibility_status": "BLOCKED_UNIT_SEMANTICS",
                "engineering_plausibility_reason": (
                    "Показатель классифицирован как расход без единицы потока; число не допускается в сравнение."
                ),
            })
            summary["flow_false_positives_blocked"] += 1
        if code in {"BULK_DENSITY", "MOISTURE"}:
            row.update({
                "evidence_scope": "MATERIAL_OR_PROCESS",
                "entity_type": "MATERIAL",
                "object_hint": row.get("material_name") or "Материал / технологический поток",
                "binding_status": "MATERIAL_SCOPE_RECONSTRUCTED",
                "fact_admission_decision": "HOLD",
                "comparison_excluded": True,
            })
            summary["material_scope_rebound"] += 1
        admission = str(row.get("fact_admission_decision") or "").upper()
        if admission in {"HOLD", "REJECT"} and not row.get("comparison_excluded"):
            reasons = [str(value) for value in row.get("fact_admission_reasons") or [] if str(value).strip()]
            row["comparison_excluded"] = True
            row["comparison_exclusion_reason"] = (
                "; ".join(reasons)
                or "Факт не допущен Evidence Admission Gate и исключён из межраздельных сравнений."
            )
            summary["non_admitted_facts_excluded"] += 1
    return summary


def reconstruct_high_value_evidence(page_corpus: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Reconstruct exact, addressable material-property evidence.

    The module deliberately produces candidate facts and targeted questions.
    A numeric difference is not promoted to a project finding until material,
    process stage, revision and authority are all deterministically aligned.
    """
    facts: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for page in page_corpus or []:
        document = str(page.get("document") or "").strip()
        page_no = page.get("page") or ""
        section = canonical_section(page.get("document_type") or page.get("section") or document)
        text = str(page.get("text") or "")
        if not document or not text or is_assignment_source(page):
            continue
        for code, patterns in _HIGH_VALUE_PATTERNS.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    raw_value = match.group("value")
                    normalized_values = [
                        _number(part) for part in re.split(r"\s*/\s*", raw_value)
                        if _number(part) is not None
                    ]
                    if not normalized_values:
                        continue
                    value = normalized_values[0]
                    unit = re.sub(r"\s+", "", match.group("unit")).replace("³", "3")
                    key = (document, page_no, code, value, unit, match.start())
                    if key in seen:
                        continue
                    seen.add(key)
                    span, span_start, span_end = _exact_span(text, match.start(), match.end())
                    scope, entity_type, default_owner = _SCOPES[code]
                    owner = _material_owner(text, match.start()) if code in {"BULK_DENSITY", "MOISTURE"} else default_owner
                    facts.append({
                        "fact_id": _stable_id("RECON", document, page_no, code, value, unit, span),
                        "parameter_code": code,
                        "parameter_name": _PARAMETER_NAMES[code],
                        "value": value,
                        "value_text": raw_value,
                        "normalized_values": normalized_values,
                        "unit": unit,
                        "document": document,
                        "document_type": section,
                        "section": section,
                        "page": page_no,
                        "object_hint": owner,
                        "material_name": owner,
                        "entity_type": entity_type,
                        "evidence_scope": scope,
                        "source_trace": span,
                        "context": span,
                        "exact_span": span,
                        "exact_span_start": span_start,
                        "exact_span_end": span_end,
                        "source_locator": {
                            "document": document, "page": page_no, "section": section,
                            "span_start": span_start, "span_end": span_end,
                        },
                        "binding_status": "MATERIAL_SCOPE_RECONSTRUCTED",
                        "fact_admission_decision": "HOLD",
                        "fact_admission_reasons": [
                            "Область владельца и стадия процесса должны быть подтверждены до межраздельного вывода."
                        ],
                        "evidence_quality_decision": "SUPPORTED",
                        "evidence_trust_grade": "B",
                        "comparison_excluded": True,
                        "reconstruction_engine": ENGINE_VERSION,
                    })

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        grouped[(fact["parameter_code"], normalize_text(fact["material_name"]).lower())].append(fact)

    comparisons: list[dict[str, Any]] = []
    for (code, owner), rows in grouped.items():
        if code not in {"BULK_DENSITY", "MOISTURE"}:
            continue
        distinct = sorted({float(row["value"]) for row in rows})
        if len(distinct) < 2:
            continue
        minimum, maximum = min(distinct), max(distinct)
        delta = maximum - minimum
        relative = delta / max(abs(minimum), 1e-9)
        if delta <= 0.005 or relative <= 0.01:
            continue
        sources = " | ".join(
            f"{row['document']}, стр. {row['page']}: {row['value']} {row['unit']}"
            for row in rows[:12]
        )
        comparisons.append({
            "check_code": _stable_id("MAT-CHECK", code, owner, distinct),
            "parameter_code": code,
            "parameter_name": _PARAMETER_NAMES[code],
            "object": rows[0]["material_name"],
            "comparison_scope": "MATERIAL_OR_PROCESS",
            "status": "ТРЕБУЕТ ПРОВЕРКИ",
            "finding_type": "REVIEW_QUESTION",
            "verification_kind": "REVIEW_QUESTION",
            "final_verification_kind": "REVIEW_QUESTION",
            "verification_state": "Требует проверки специалистом",
            "proof_kind": "EXACT_SPAN_CANDIDATES",
            "document_values": [
                {"document": row["document"], "page": row["page"], "value": row["value"], "unit": row["unit"]}
                for row in rows
            ],
            "values_by_section": {f"{row['section']} · {row['document']} · стр. {row['page']}": f"{row['value']} {row['unit']}" for row in rows},
            "strong_evidence_count": len(rows),
            "sources": sources,
            "explanation": (
                f"Найдены адресные значения {minimum:g} и {maximum:g}; различие {relative * 100:.1f}%. "
                "Категоричный вывод удержан до подтверждения одного материала, стадии процесса и редакции."
            ),
            "recommendation": "Проверить принадлежность значений материалу и стадии процесса, затем унифицировать исходный параметр.",
            "coverage_state": "TARGETED_REVIEW",
            "coverage_reason_code": "MATERIAL_PROCESS_SCOPE_REVIEW",
            "evidence_candidates": rows,
            "engine_version": ENGINE_VERSION,
        })

    return {
        "version": ENGINE_VERSION,
        "facts": facts,
        "comparisons": comparisons,
        "summary": {
            "exact_facts": len(facts),
            "density_facts": sum(row["parameter_code"] == "BULK_DENSITY" for row in facts),
            "moisture_facts": sum(row["parameter_code"] == "MOISTURE" for row in facts),
            "targeted_questions": len(comparisons),
            "by_parameter": dict(sorted({
                code: sum(row["parameter_code"] == code for row in facts)
                for code in _HIGH_VALUE_PATTERNS
            }.items())),
        },
    }
