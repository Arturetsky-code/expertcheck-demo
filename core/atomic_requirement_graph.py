from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any, Iterable

from .normalization import normalize_text
from .requirement_contracts import build_contract


GRAPH_VERSION = "1.0-atomic-requirements"

_BULLET_RE = re.compile(r"\s*[•●▪◦−–]\s+")
_SENTENCE_RE = re.compile(r"(?<=[.;])\s+(?=[А-ЯA-ZЁ])")
_WORD_RE = re.compile(r"[a-zа-яё0-9-]+", re.I)
_NORMATIVE_RE = re.compile(
    r"\b(?:сп|гост|снип|санпин|рд|со|пуэ|фнп|федеральн\w*\s+закон|"
    r"постановлен\w*\s+правительств|градостроительн\w*\s+кодекс)\b",
    re.I,
)
_NUMBER_UNIT_RE = re.compile(
    r"(?P<value>\d[\d\s]*(?:[,.]\d+)?)\s*"
    r"(?P<unit>тыс\.?\s*тонн(?:\s*в\s*год)?|тонн(?:ы|а)?(?:\s*в\s*год)?|т\s*/\s*ч|"
    r"тонн\s*/\s*час|м[³3]|м²|м2|мм|см|км|час(?:а|ов)?|сут(?:ок|ки)?|дн(?:я|ей)|"
    r"в|кв|квт|мвт|гц|ом|кадр(?:ов)?\s*в\s*сек|минут(?:ы)?|шт\.?)\b",
    re.I,
)

_NUMBER_WORDS = {
    "один": 1, "одна": 1, "одним": 1, "одной": 1,
    "два": 2, "две": 2, "двумя": 2, "двух": 2,
    "три": 3, "тремя": 3, "трех": 3, "трёх": 3,
    "четыре": 4, "четырьмя": 4, "четырех": 4, "четырёх": 4,
}

_EQUIPMENT_TERMS = (
    "погрузчик", "самосвал", "автосамосвал", "насос", "дробилк", "грохот",
    "конвейер", "питател", "трансформатор", "резервуар", "ёмкост", "емкост",
)

_ACTION_MARKERS = (
    "предусмотр", "выполн", "принят", "примен", "обеспеч", "осуществ",
    "определ", "разработ", "установ", "подач", "проклад", "сброс", "материал",
    "тип ", "систем", "долж", "не требуется", "требования отсутствуют",
    "в электронном виде", "на бумажном носителе", "соответств",
)

_SECTION_ROUTES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("электроснаб", "электропит", "кабел", "заземл", "молниезащ", "освещен", "светильник"), ("ИОС1",)),
    (("водоснаб", "водоотвед", "канализац", "сток", "резервуар", "выгреб"), ("ИОС2",)),
    (("автоматизац", "диспетчер", "автоматизированн рабоч", "видеонаблюден", "волс"), ("ИОС5", "ТХ")),
    (("производительност", "технологическ", "оборудован", "погрузчик", "самосвал", "конвейер", "дробил"), ("ТХ",)),
    (("генеральн", "планировочн", "проезд", "дорог", "огражден", "подтоплен", "рельеф"), ("ПЗУ",)),
    (("архитектур", "фасад", "помещен", "объемно-планиров"), ("АР",)),
    (("конструктив", "фундамент", "подпорн", "металлоконструк"), ("КР",)),
    (("организац", "строительств", "производств работ"), ("ПОС",)),
    (("камер", "видеозапис", "архив запис"), ("ИОС5",)),
    (("железобетон", "фбс", "паг ", "фундаментн блок"), ("КР",)),
    (("градостроитель", "постановлен", "законодательств", "строительн норм", "идентификационн"), ("ПЗ",)),
    (("состав объект", "приложени 1", "техническ услов", "ту заказчик"), ("ПЗ",)),
)


def _clean_text(value: Any) -> str:
    text = str(value or "").replace("\u00ad", "")
    text = re.sub(r"(?<=[A-Za-zА-Яа-яЁё])[-‐]\s+(?=[A-Za-zА-Яа-яЁё])", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ;")
    return text


def _stable_id(parent_id: str, index: int, text: str, focus: str = "") -> str:
    digest = hashlib.sha1(f"{parent_id}|{index}|{focus}|{text}".encode("utf-8", "ignore")).hexdigest()[:10].upper()
    return f"{parent_id}-A{index:03d}-{digest}"


def _has_action(text: str) -> bool:
    low = normalize_text(text).lower()
    return any(marker in low for marker in _ACTION_MARKERS)


def _split_sentences(text: str) -> list[str]:
    protected = str(text or "")
    for token in ("т. д.", "т. п.", "т. е.", "г. №", "РФ."):
        protected = protected.replace(token, token.replace(".", "<DOT>"))
    parts = _SENTENCE_RE.split(protected)
    result: list[str] = []
    for part in parts:
        part = _clean_text(part.replace("<DOT>", "."))
        if not part:
            continue
        if result and len(part) < 22 and not _has_action(part):
            result[-1] = _clean_text(result[-1] + "; " + part)
        else:
            result.append(part)
    return result


def _split_requirement(text: str) -> list[dict[str, Any]]:
    clean = _clean_text(text)
    # PDF extraction can remove the line break after this label and glue the
    # following prohibition to it.  Keep the label as its own unresolved atom
    # and preserve an exact prohibition clause for evidence matching/reporting.
    clean = re.sub(
        r"(Тип\s+применяемых\s+опор)\s*:\s*(?=Прокладк)",
        r"\1. ", clean, flags=re.I,
    )
    bullet_parts = _BULLET_RE.split(clean)
    has_bullets = len(bullet_parts) > 1
    prefix = _clean_text(bullet_parts[0]) if has_bullets else ""
    clauses: list[dict[str, Any]] = []

    if has_bullets:
        prefix_sentences = _split_sentences(prefix.rstrip(":"))
        for sentence in prefix_sentences:
            # "АСУ должна обеспечивать:" is context for the children, while
            # "АСУ поставляется комплектно." is a standalone obligation.
            if sentence.endswith(":") or ("должна обеспечивать" in normalize_text(sentence) and len(prefix_sentences) == 1):
                continue
            if _has_action(sentence) and not sentence.lower().endswith("обеспечивать"):
                clauses.append({"text": sentence, "context": "", "from_bullet": False})

        context = prefix.rstrip(":")
        for raw_part in bullet_parts[1:]:
            for sentence in _split_sentences(raw_part):
                if not sentence:
                    continue
                clauses.append({"text": sentence, "context": context, "from_bullet": True})
    else:
        for sentence in _split_sentences(clean):
            clauses.append({"text": sentence, "context": "", "from_bullet": False})

    return clauses or [{"text": clean, "context": "", "from_bullet": False}]


def _parse_number(value: str) -> float | None:
    try:
        return float(value.replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _canonical_unit(value: str) -> str:
    low = normalize_text(value).lower().replace(" ", "")
    aliases = {
        "тонн/час": "т/ч", "м3": "м3", "м³": "м3", "м2": "м2", "м²": "м2",
        "тонн": "т", "тонна": "т", "тонны": "т", "т": "т",
        "кадроввсек": "кадр/с", "кадрвсек": "кадр/с", "минуты": "мин", "минут": "мин",
        "час": "ч", "часа": "ч", "часов": "ч", "штуки": "шт", "шт.": "шт",
    }
    return aliases.get(low, low)


def _parameter_for_measure(text: str, unit: str) -> str:
    low = normalize_text(text).lower()
    if unit == "т" and ("г/п" in low or "грузопод" in low):
        return "CARRY_CAPACITY"
    if unit == "м3" and "ковш" in low:
        return "BUCKET_VOLUME"
    if unit == "м3" and "кузов" in low:
        return "BODY_VOLUME"
    if "грузопод" in low:
        return "CARRY_CAPACITY"
    if "производительност" in low or unit == "т/ч":
        return "CAPACITY"
    if "напряжен" in low:
        return "VOLTAGE"
    if "частот" in low:
        return "FREQUENCY"
    if "срок" in low or "хранен" in low:
        return "RETENTION_PERIOD"
    if "резерв" in low and unit == "мин":
        return "BACKUP_DURATION"
    if "объем" in low or "объём" in low or unit == "м3":
        return "VOLUME"
    if unit == "м2":
        return "AREA"
    return "NUMERIC_VALUE"


def _quantity_word(text: str) -> int | None:
    low = normalize_text(text).lower()
    for word, value in _NUMBER_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", low):
            return value
    match = re.search(r"(?:количеств\w*\s*[-–—:=]?\s*|[-–—]\s*)(\d{1,3})\s*шт", low)
    return int(match.group(1)) if match else None


def _equipment_identity(text: str) -> tuple[str, list[str]]:
    low = normalize_text(text).lower()
    if not any(term in low for term in _EQUIPMENT_TERMS):
        return "", []
    models = re.findall(r"\b[A-ZА-ЯЁ][A-ZА-ЯЁ0-9-]{2,}\d[A-ZА-ЯЁ0-9-]*\b", text, re.I)
    brands = re.findall(
        r"(?:погрузчик\w*|самосвал\w*|автосамосвал\w*|насос\w*|дробилк\w*)\s+"
        r"([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9-]{2,})",
        text,
        re.I,
    )
    brand = brands[0] if brands else ""
    # A word following an equipment noun is not automatically a manufacturer:
    # e.g. «выгрузка автосамосвалов производится…».  Accept a brand only when
    # it is visibly brand-like; model tokens remain an independent identity cue.
    if brand and not (re.search(r"[A-Za-z]", brand) or (brand.isupper() and len(brand) >= 3)):
        brand = ""
    return brand, list(dict.fromkeys(models))


def _expand_clause(clause: dict[str, Any]) -> list[dict[str, Any]]:
    text = clause["text"]
    context = clause.get("context") or ""
    low = normalize_text(text).lower()
    expanded: list[dict[str, Any]] = []
    brand, models = _equipment_identity(text)
    measurements = []
    for match in _NUMBER_UNIT_RE.finditer(text):
        value = _parse_number(match.group("value"))
        unit = _canonical_unit(match.group("unit"))
        if value is None:
            continue
        measurements.append({"value": value, "unit": unit, "span": match.span(), "parameter_code": _parameter_for_measure(text, unit)})

    quantity = _quantity_word(text) if brand or models else None
    if brand or models:
        expanded.append({
            **clause,
            "text": _clean_text(f"{context + ': ' if context else ''}{text}"),
            "focus": "EQUIPMENT_IDENTITY",
            "atomic_kind": "EQUIPMENT_IDENTITY",
            "required_brand": brand,
            "required_models": models,
        })
        if quantity is not None:
            expanded.append({
                **clause,
                "text": _clean_text(f"Количество оборудования: {quantity}. {text}"),
                "focus": "EQUIPMENT_QUANTITY",
                "atomic_kind": "VALUE_COMPARISON",
                "parameter_code": "QUANTITY",
                "required_value": quantity,
                "unit": "шт",
            })

    # Split multiple independently measurable attributes.  The original clause
    # remains available as context, but every value gets its own verdict.
    for measurement in measurements:
        expanded.append({
            **clause,
            "text": _clean_text(text),
            "focus": measurement["parameter_code"],
            "atomic_kind": "VALUE_COMPARISON",
            "parameter_code": measurement["parameter_code"],
            "required_value": measurement["value"],
            "unit": measurement["unit"],
        })

    if "производительност" in low and "лини" in low:
        line_count = _quantity_word(text)
        if line_count is not None:
            expanded.append({
                **clause,
                "text": _clean_text(f"Количество технологических линий: {line_count}. {text}"),
                "focus": "PROCESS_LINE_COUNT",
                "atomic_kind": "TOPOLOGY_REQUIREMENT",
                "parameter_code": "PROCESS_LINE_COUNT",
                "required_value": line_count,
                "unit": "шт",
            })

    if expanded:
        # Remove exact duplicates produced by a single generic NUMERIC_VALUE and
        # a more specific equipment/topology attribute.
        unique: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()
        for item in expanded:
            key = (item.get("focus"), item.get("required_value"), item.get("unit"), item.get("text"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique
    local_decision = any(
        token in normalize_text(text).lower()
        for token in ("не предусматривать", "не требуется", "разработка не требуется", "требования отсутствуют")
    )
    rendered = text if local_decision else f"{context + ': ' if context else ''}{text}"
    return [{**clause, "text": _clean_text(rendered)}]


def _infer_kind(text: str, inherited: str = "") -> str:
    low = normalize_text(text).lower()
    if "не предусматривать" in low:
        return "PROHIBITION"
    if any(token in low for token in ("не требуется", "разработка не требуется", "требования отсутствуют")):
        return "APPLICABILITY_DECLARATION"
    if _NORMATIVE_RE.search(low) and any(token in low for token in ("соответств", "согласно", "требован")):
        return "NORMATIVE_CLAUSE"
    if any(token in low for token in ("согласно ту", "согласно инженерным изысканиям", "документации завода", "предоставляемой заказчиком")):
        return "TRACEABILITY"
    if any(token in low for token in ("в электронном виде", "бумажном носителе", "редактируемом формате")):
        return "DOCUMENT_DELIVERABLE"
    if "определить проект" in low or "определить при разработке" in low:
        return "DESIGN_DETERMINED"
    if "должна обеспечивать" in low or "должен обеспечивать" in low:
        return "FEATURE_PRESENCE"
    if _NUMBER_UNIT_RE.search(text):
        return "VALUE_COMPARISON"
    if "состав объектов" in low or "согласно приложению" in low and "состав" in low:
        return "SET_COMPARISON"
    if inherited in {"VALUE_COMPARISON", "SET_COMPARISON"}:
        return inherited
    return "PRESENCE_REQUIREMENT"


def _mapped_requirement_type(kind: str) -> str:
    return {
        "PROHIBITION": "PROHIBITION_OR_NOT_REQUIRED",
        "APPLICABILITY_DECLARATION": "APPLICABILITY_DECLARATION",
        "NORMATIVE_CLAUSE": "NORMATIVE_CLAUSE",
        "TRACEABILITY": "SOURCE_TRACEABILITY",
        "DOCUMENT_DELIVERABLE": "SOURCE_TRACEABILITY",
        "DESIGN_DETERMINED": "DESIGN_DETERMINED",
        "FEATURE_PRESENCE": "PRESENCE_REQUIREMENT",
        "EQUIPMENT_IDENTITY": "VALUE_COMPARISON",
        "TOPOLOGY_REQUIREMENT": "VALUE_COMPARISON",
        "VALUE_COMPARISON": "VALUE_COMPARISON",
        "SET_COMPARISON": "SET_COMPARISON",
    }.get(kind, "PRESENCE_REQUIREMENT")


def _infer_sections(text: str, kind: str) -> list[str]:
    low = normalize_text(text).lower()
    sections: list[str] = []
    for markers, routed in _SECTION_ROUTES:
        if any(marker in low for marker in markers):
            for section in routed:
                if section not in sections:
                    sections.append(section)
    if kind in {"DOCUMENT_DELIVERABLE", "TRACEABILITY"} and not sections:
        sections.append("ПЗ")
    if kind == "NORMATIVE_CLAUSE" and not sections:
        sections.append("ПЗ")
    if not sections:
        # ALL is an explicit project-wide scope, not an unresolved scope.  It
        # does not relax the verdict gate: without a typed recipe and addressable
        # evidence the result still remains a system limitation.
        sections.append("ALL")
    return sections


def atomize_requirement(requirement: dict[str, Any], *, domain: str = "assignment") -> list[dict[str, Any]]:
    parent_id = str(requirement.get("requirement_id") or requirement.get("id") or "REQ")
    parent_text = _clean_text(requirement.get("requirement_text") or requirement.get("requirement") or requirement.get("question") or "")
    inherited_type = str(requirement.get("requirement_type") or "")
    clauses: list[dict[str, Any]] = []
    for clause in _split_requirement(parent_text):
        clauses.extend(_expand_clause(clause))

    atoms: list[dict[str, Any]] = []
    for index, clause in enumerate(clauses, 1):
        atom_text = _clean_text(clause.get("text") or "")
        if not atom_text:
            continue
        kind = str(clause.get("atomic_kind") or _infer_kind(atom_text, inherited_type))
        focus = str(clause.get("focus") or kind)
        atom_id = _stable_id(parent_id, index, atom_text, focus)
        atom = {
            **requirement,
            "requirement_id": atom_id,
            "atom_id": atom_id,
            "parent_requirement_id": parent_id,
            "source_requirement_id": parent_id,
            "domain": domain,
            "atom_index": index,
            "atom_text": atom_text,
            "requirement_text": atom_text,
            "parent_requirement_text": parent_text,
            "atomic_kind": kind,
            "focus": focus,
            "logical_operator": "AND",
            "from_bullet": bool(clause.get("from_bullet")),
            "context_prefix": clause.get("context") or "",
            "requirement_type": _mapped_requirement_type(kind),
            "atomic_status": "UNVERIFIED",
        }
        for key in ("parameter_code", "required_value", "unit", "required_brand", "required_models"):
            if key in clause:
                atom[key] = clause[key]
        # Parent numeric fields may be reused only for a single atom or for an
        # atom explicitly focused on that parameter.
        if len(clauses) == 1:
            for key in ("parameter_code", "required_value", "unit", "object_name"):
                if requirement.get(key) not in (None, ""):
                    atom[key] = requirement.get(key)
        atom["evidence_contract_v2"] = build_contract(atom)
        atom["expected_sections"] = list((atom["evidence_contract_v2"] or {}).get("expected_sections") or [])
        if not atom["expected_sections"]:
            atom["expected_sections"] = _infer_sections(atom_text, kind)
            if atom["expected_sections"]:
                atom["evidence_contract_v2"] = {
                    **(atom["evidence_contract_v2"] or {}),
                    "expected_sections": list(atom["expected_sections"]),
                    "section_routing": "UNIVERSAL_ATOMIC_ROUTE",
                }
        atoms.append(atom)
    return atoms


def build_atomic_requirement_graph(
    requirements: Iterable[dict[str, Any]],
    *,
    domain: str = "assignment",
) -> dict[str, Any]:
    atoms: list[dict[str, Any]] = []
    parent_nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    for requirement in requirements or []:
        parent_id = str(requirement.get("requirement_id") or requirement.get("id") or f"REQ-{len(parent_nodes)+1:04d}")
        parent_nodes.append({
            "node_id": parent_id,
            "node_type": "REQUIREMENT_GROUP",
            "domain": domain,
            "text": _clean_text(requirement.get("requirement_text") or requirement.get("requirement") or requirement.get("question") or ""),
        })
        children = atomize_requirement({**requirement, "requirement_id": parent_id}, domain=domain)
        atoms.extend(children)
        edges.extend({"from": parent_id, "to": child["atom_id"], "relation": "HAS_ATOMIC_CONDITION"} for child in children)

    by_kind = Counter(str(atom.get("atomic_kind") or "UNCLASSIFIED") for atom in atoms)
    scoped = sum(bool(atom.get("expected_sections") or atom.get("object_name") or (atom.get("evidence_contract_v2") or {}).get("scope") not in {None, "", "UNRESOLVED"}) for atom in atoms)
    return {
        "version": GRAPH_VERSION,
        "domain": domain,
        "parents": parent_nodes,
        "atoms": atoms,
        "edges": edges,
        "summary": {
            "source_requirements": len(parent_nodes),
            "atomic_requirements": len(atoms),
            "additional_conditions": max(0, len(atoms) - len(parent_nodes)),
            "scoped_atoms": scoped,
            "scope_coverage_pct": round(100 * scoped / max(1, len(atoms)), 1),
            "by_kind": dict(sorted(by_kind.items())),
        },
    }


def flatten_atomic_rows(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return list(graph.get("atoms") or [])
