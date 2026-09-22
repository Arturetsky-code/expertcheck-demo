from __future__ import annotations

import math
import re
from difflib import SequenceMatcher
from typing import Any, Iterable

from .normalization import normalize_text
from .page_evidence_store import is_assignment_source, section_matches
from .metric_semantics import (
    capacity_level_label,
    capacity_levels_equivalent,
    capacity_semantic_level,
)


DESIGN_MARKERS = (
    "предусмотрен", "предусмотрена", "предусмотрено", "предусмотрены", "предусматривается",
    "предусматривает", "разработан", "разработана", "разработаны", "выполнен", "выполнена",
    "выполнено", "принят", "принята", "принято", "приняты", "проектом предусматривается",
    "оборудуется", "ограждается", "осуществляется", "обеспечивается", "организована",
)

NEGATIVE_MARKERS = (
    "не требуется", "не предусматривается", "не предусмотрено",
    "разработка не требуется", "требования отсутствуют", "не применяется",
    "отсутствует необходимость",
)

NORMATIVE_REF_RE = re.compile(
    r"\b(?:ГОСТ(?:\s+Р)?|СП|СНиП|ФЗ)\s*[A-ZА-Я0-9.-]+(?:\s*[-–—]\s*\d{2,4})?",
    re.I,
)

STOP_WORDS = {
    "предусмотреть", "принять", "выполнить", "разработать", "обеспечить",
    "проект", "проектом", "проектной", "документации", "требование",
    "согласно", "часть", "площадка", "объект", "следующий", "который",
    "должен", "должна", "должны", "необходимо", "заказчик",
}

NUMBER_WORDS = {
    "одним": 1, "одной": 1, "один": 1, "одна": 1,
    "двумя": 2, "двух": 2, "два": 2, "две": 2,
    "тремя": 3, "трех": 3, "трёх": 3, "три": 3,
    "четырьмя": 4, "четырех": 4, "четырёх": 4, "четыре": 4,
}


CONCEPTS: tuple[dict[str, Any], ...] = (
    {
        "id": "FLOOD_PROTECTION",
        "requirement": (("подтоплен",),),
        "evidence": (("защит", "подтоплен"), ("систем", "водоотвед"), ("нагорн", "канал"), ("водопропускн", "труб")),
        "sections": ("ПЗУ",), "minimum_groups": 2,
    },
    {
        "id": "INTERNAL_ROADS",
        "requirement": (("внутриплощадочн", "проезд"), ("дорожн", "сет")),
        "evidence": (("внутриплощадочн", "проезд"), ("существующ", "дорог"), ("покрыт", "проезд"), ("примыкан", "дорог")),
        "sections": ("ПЗУ",), "minimum_groups": 2,
    },
    {
        "id": "FENCING",
        "requirement": (("огражден",),),
        "evidence": (("территор", "огражд"), ("панел", "столб"), ("ворот",), ("калит",)),
        "sections": ("ПЗУ", "КР"), "minimum_groups": 2,
    },
    {
        "id": "SITE_LIGHTING",
        "requirement": (("электроосвещ",), ("светодиодн", "светильник"), ("искусственн", "освещен")),
        "evidence": (("освещен", "территор"), ("мачт", "освещен"), ("светильник", "опор")),
        "sections": ("ПЗУ", "ИОС1"), "minimum_groups": 2,
    },
    {
        "id": "GROUNDING_LIGHTNING",
        "requirement": (("заземля",), ("молниезащит",)),
        "evidence": (("заземля", "устройств"), ("молниезащит",), ("молниеприем",), ("контур", "заземлен")),
        "sections": ("ИОС1",), "minimum_groups": 2,
    },
    {
        "id": "VIDEO_SURVEILLANCE",
        "requirement": (("видеонаблюден",),),
        "evidence": (("видеонаблюден",), ("камер",), ("видеосервер",), ("волс",), ("архив", "запис")),
        "sections": ("ИОС5",), "minimum_groups": 3,
    },
    {
        "id": "WASTEWATER_SYSTEMS",
        "requirement": (("водоотвед",), ("канализац",)),
        "evidence": (("хозяйственно-бытов", "канализац"), ("ливнев", "канализац"), ("выгреб",), ("очистн", "сооружен"), ("поверхностн", "сток")),
        "sections": ("ИОС2", "ПЗУ"), "minimum_groups": 3,
    },
    {
        "id": "PERSONNEL_AND_VEHICLE_ACCESS",
        "requirement": (("проезд", "техник", "проход", "персонал"),),
        "evidence": (("внутриплощадочн", "проезд"), ("пешеходн", "связ"), ("металлическ", "лестниц")),
        "sections": ("ПЗУ",), "minimum_groups": 2,
    },
)


def _norm(value: Any) -> str:
    text = str(value or "").replace("\u00ad", "")
    text = re.sub(r"(?<=[A-Za-zА-Яа-яЁё])-\s+(?=[A-Za-zА-Яа-яЁё])", "", text)
    return normalize_text(text).lower().replace("ё", "е")


def _context(text: str, anchors: Iterable[str], radius: int = 430) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    low = _norm(clean)
    positions = [low.find(_norm(x)) for x in anchors if x and low.find(_norm(x)) >= 0]
    pos = min(positions) if positions else 0
    return clean[max(0, pos - radius): pos + radius * 2][:1100]


def _groups_present(text: str, groups: Iterable[Iterable[str]]) -> list[tuple[str, ...]]:
    low = _norm(text)
    return [tuple(group) for group in groups if all(_norm(token) in low for token in group)]


def _requirement_matches(text: str, groups: Iterable[Iterable[str]]) -> bool:
    return bool(_groups_present(text, groups))


def _significant_terms(text: str) -> list[str]:
    words = re.findall(r"[a-zа-яе0-9-]{5,}", _norm(text))
    out: list[str] = []
    for word in words:
        if word in STOP_WORDS or word.isdigit():
            continue
        stem = word[: max(5, min(len(word), 9))]
        if stem not in out:
            out.append(stem)
    return out[:18]


def _candidate_pages(page_corpus: list[dict[str, Any]], sections: Iterable[str]) -> list[dict[str, Any]]:
    return [
        p for p in page_corpus or []
        if not is_assignment_source(p)
        and section_matches(p.get("document_type") or p.get("document"), sections)
    ]


def _concept_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = str(requirement.get("requirement_text") or "")
    rtype = str(requirement.get("requirement_type") or "")
    contract = requirement.get("evidence_contract_v2") or {}
    for concept in CONCEPTS:
        if not _requirement_matches(text, concept["requirement"]):
            continue
        sections = list(contract.get("expected_sections") or concept["sections"])
        ranked: list[tuple[int, dict[str, Any], list[tuple[str, ...]]]] = []
        for page in _candidate_pages(page_corpus, sections):
            groups = _groups_present(page.get("text") or "", concept["evidence"])
            if not groups:
                continue
            low = _norm(page.get("text") or "")
            score = len(groups) * 18 + (18 if any(marker in low for marker in DESIGN_MARKERS) else 0) + 15
            ranked.append((score, page, groups))
        ranked.sort(key=lambda x: x[0], reverse=True)
        if not ranked:
            return None
        all_groups: set[tuple[str, ...]] = set()
        for _, _, groups in ranked[:5]:
            all_groups.update(groups)
        strong = len(all_groups) >= int(concept.get("minimum_groups") or 1) and any(
            any(marker in _norm(page.get("text") or "") for marker in DESIGN_MARKERS)
            for _, page, _ in ranked[:5]
        )
        evidence_rows = []
        evidence_text = []
        for score, page, groups in ranked[:4]:
            anchors = [token for group in groups for token in group]
            snippet = _context(page.get("text") or "", anchors)
            evidence_rows.append({
                "evidence_kind": "QUALIFIED_PROJECT_PASSAGE" if strong else "CANDIDATE_PROJECT_PASSAGE",
                "evidence_state": "verified_candidate" if strong else "candidate",
                "document": page.get("document"), "document_type": page.get("document_type"),
                "page": page.get("page"), "context": snippet, "score": min(100, score),
                "concept": concept["id"],
            })
            evidence_text.append(f"{page.get('document')}, стр. {page.get('page')}: {snippet}")
        closable = strong and rtype == "PRESENCE_REQUIREMENT"
        return {
            "status": "Соответствует заданию" if closable else "Требует проверки",
            "evidence": evidence_text, "evidence_candidates": evidence_rows,
            "verification_evidence": evidence_rows,
            "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE" if strong else "CANDIDATE_EVIDENCE",
            "match_confidence": 0.94 if closable else 0.82,
            "decision_basis": (
                f"Проектное решение подтверждено профильными источниками по контракту {concept['id']}."
                if closable else
                f"Найдены профильные проектные решения по контракту {concept['id']}; требуется проверить полноту всех условий и нормативную часть требования."
            ),
            "verification_kernel": concept["id"],
        }
    return None


def _quantity(text: str) -> int | None:
    low = _norm(text)
    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", low):
            return value
    match = re.search(r"(?:количеств\w*\s*[-–—:=]?\s*|[-–—]\s*)(\d{1,3})\s*шт", low)
    return int(match.group(1)) if match else None


def _latin_model(value: str) -> str:
    table = str.maketrans({"А":"A", "В":"B", "С":"C", "Е":"E", "Н":"H", "К":"K", "М":"M", "О":"O", "Р":"P", "Т":"T", "Х":"X"})
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper().translate(table))


def _model_tokens(text: str) -> list[str]:
    raw = re.findall(r"\b[A-ZА-ЯЁ][A-ZА-ЯЁ0-9-]{2,}\d[A-ZА-ЯЁ0-9-]*\b", str(text or ""), re.I)
    return list(dict.fromkeys(_latin_model(x) for x in raw if len(_latin_model(x)) >= 4))


def _brand_after_equipment(text: str) -> str:
    match = re.search(r"(?:автосамосвал\w*|самосвал\w*|погрузчик\w*)\s+([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9-]{2,})", str(text or ""), re.I)
    return _latin_model(match.group(1)) if match else ""


def _equipment_record(text: str, task_models: list[str], equipment: str) -> str:
    """Return the most relevant equipment-register row instead of a whole page."""
    lines = [re.sub(r"\s+", " ", line).strip() for line in str(text or "").splitlines() if line.strip()]
    ranked: list[tuple[int, str]] = []
    for index in range(len(lines)):
        # Prefer the physical register row itself.  Including the previous row
        # mixed adjacent truck/loader brands in the same evidence packet.
        windows = [lines[index]]
        if index + 1 < len(lines):
            windows.append(" ".join(lines[index:index + 2]))
        for window_rank, window in enumerate(windows):
            low = _norm(window)
            if equipment not in low:
                continue
            models = _model_tokens(window)
            score = 35 - window_rank * 8
            if task_models and any(model in models for model in task_models):
                score += 80
            if re.search(r"[-–—]\s*\d{1,3}\s*шт", window, re.I):
                score += 45
            if models:
                score += 15
            ranked.append((score, window))
    if ranked:
        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked[0][1][:1100]
    return _context(text, task_models or (equipment,), radius=520)


def _equipment_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = str(requirement.get("requirement_text") or "")
    low = _norm(text)
    if not any(token in low for token in ("погрузчик", "автосамосвал", "самосвал")):
        return None
    if str(requirement.get('requirement_type') or '')!='VALUE_COMPARISON' and not _model_tokens(text):
        return None
    equipment = "погрузчик" if "погрузчик" in low else "самосвал"
    task_models = _model_tokens(text)
    task_brand = _brand_after_equipment(text)
    task_qty = _quantity(text)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for page in _candidate_pages(page_corpus, ("ТХ", "ПЗУ")):
        page_low = _norm(page.get("text") or "")
        if equipment not in page_low:
            continue
        score = 30
        page_models = _model_tokens(page.get("text") or "")
        page_brand = _brand_after_equipment(page.get("text") or "")
        if task_models and any(model in page_models for model in task_models):
            score += 45
        if task_brand and task_brand in _latin_model(page.get("text") or ""):
            score += 20
        if "рабочий парк" in page_low or ("переч" in page_low and "оборудован" in page_low):
            score += 45
        if re.search(r"[-–—]\s*\d{1,3}\s*шт", str(page.get("text") or ""), re.I):
            score += 30
        if str(page.get("document_type") or "").upper().startswith("ТХ"):
            score += 12
        if page_brand:
            score += 8
        ranked.append((score, page))
    ranked.sort(key=lambda x: x[0], reverse=True)
    if not ranked:
        return None
    page = ranked[0][1]
    snippet = _equipment_record(page.get("text") or "", task_models, equipment)
    project_models = _model_tokens(snippet)
    project_brand = _brand_after_equipment(snippet)
    project_qty = _quantity(snippet)
    same_model = bool(task_models and any(model in project_models for model in task_models))
    brand_similarity = SequenceMatcher(None, task_brand, project_brand).ratio() if task_brand and project_brand else 0.0
    differences: list[str] = []
    if task_brand and project_brand and task_brand != project_brand and brand_similarity < 0.90:
        differences.append(f"обозначение изготовителя/марки: в Задании {task_brand}, в ПД {project_brand}")
    if task_qty is not None and project_qty is not None and task_qty != project_qty:
        differences.append(f"количество: в Задании {task_qty}, в ПД {project_qty}")
    if task_models and project_models and not same_model:
        differences.append("модель оборудования не совпала")
    source_is_register = bool(
        str(page.get("document_type") or "").upper().startswith("ТХ")
        and re.search(r"[-–—]\s*\d{1,3}\s*шт", snippet, re.I)
        and project_brand
    )
    verified_difference = bool(differences) and source_is_register
    evidence = {
        "evidence_kind": "EQUIPMENT_REGISTER_COMPARISON", "evidence_state": "verified_candidate",
        "document": page.get("document"), "document_type": page.get("document_type"), "page": page.get("page"),
        "context": snippet, "score": min(100, ranked[0][0] + 15),
        "task_models": task_models, "project_models": project_models,
        "task_quantity": task_qty, "project_quantity": project_qty,
    }
    return {
        "status": "Выявлено отклонение" if verified_difference else "Требует проверки",
        "evidence": [f"{page.get('document')}, стр. {page.get('page')}: {snippet}"],
        "evidence_candidates": [evidence], "verification_evidence": [evidence],
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE",
        "match_confidence": 0.95 if verified_difference else (0.9 if same_model else 0.84),
        "difference": "; ".join(differences) if verified_difference else None,
        "decision_basis": (
            "В профильном перечне оборудования подтверждено отклонение от Задания: " + "; ".join(differences)
            if verified_difference else
            "Найден профильный перечень оборудования. Требуется согласовать: " + "; ".join(differences)
            if differences else
            "Найдено оборудование того же типа/модели, но комплект атрибутов Задания подтверждён не полностью."
        ),
        "verification_kernel": "EQUIPMENT_IDENTITY_AND_QUANTITY",
    }


def _capacity_topology_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = str(requirement.get("requirement_text") or "")
    low = _norm(text)
    if "производительност" not in low or not any(x in low for x in ("лини", "т/ч")):
        return None
    if requirement.get('required_value') is None and 'т/ч' not in low:
        return None
    required = requirement.get("required_value")
    required_level = capacity_semantic_level(text, requirement.get("qualifier"), requirement.get("unit"))
    candidates: list[tuple[int, dict[str, Any], list[float], list[float], int | None]] = []
    for page in _candidate_pages(page_corpus, ("ТХ",)):
        page_low = _norm(page.get("text") or "")
        if not any(x in page_low for x in ("производительност", "т/ч")):
            continue
        values = []
        for match in re.finditer(r"(\d[\d\s]*(?:[,.]\d+)?)\s*(?:т\s*/\s*ч|тонн\s*/\s*час)", page_low):
            try:
                values.append(float(match.group(1).replace(" ", "").replace(",", ".")))
            except ValueError:
                continue
        summary_values: list[float] = []
        for match in re.finditer(
            r"часов\w*\s+производительност\w*\s+(?:отделени\w*\s*)?(?:,?\s*(?:т(?:онн)?\s*/\s*час))?\s+(\d[\d\s]*(?:[,.]\d+)?)",
            page_low,
        ):
            try:
                summary_values.append(float(match.group(1).replace(" ", "").replace(",", ".")))
            except ValueError:
                continue
        line_count = None
        line_match = re.search(r"количеств\w*\s+лини\w*\s*,?\s*шт\.?\s*(\d{1,2})", page_low)
        if line_match:
            line_count = int(line_match.group(1))
        if values or summary_values:
            score = len(values) + (4 if "требуем" in page_low else 0)
            score += 90 if summary_values else 0
            score += 35 if line_count is not None else 0
            score += 25 if "технологическ" in page_low and "режим" in page_low else 0
            candidates.append((score, page, values, summary_values, line_count))
    candidates.sort(key=lambda x: x[0], reverse=True)
    if not candidates:
        return None
    _, page, values, summary_values, line_count = candidates[0]
    snippet = _context(page.get("text") or "", ("производительност", "т/ч"), radius=600)
    observed_level = capacity_semantic_level(snippet)
    comparable_level = capacity_levels_equivalent(required_level, observed_level)
    exact = False
    try:
        comparison_values = summary_values or values
        exact = required is not None and any(math.isclose(float(required), value, rel_tol=.002, abs_tol=.05) for value in comparison_values)
    except (TypeError, ValueError):
        pass
    verified_difference = bool(required is not None and summary_values and not exact and comparable_level)
    evidence = {
        "evidence_kind": "TECHNOLOGY_CAPACITY_TOPOLOGY", "evidence_state": "verified_candidate",
        "document": page.get("document"), "document_type": page.get("document_type"), "page": page.get("page"),
        "context": snippet, "score": 96 if verified_difference else 88,
        "candidate_values": values[:20], "summary_hourly_values": summary_values[:5],
        "line_count": line_count,
        "capacity_required_level": required_level,
        "capacity_observed_level": observed_level,
        "capacity_level_compatible": comparable_level,
    }
    return {
        "status": "Выявлено отклонение" if verified_difference else "Требует проверки",
        "evidence": [f"{page.get('document')}, стр. {page.get('page')}: {snippet}"],
        "evidence_candidates": [evidence], "verification_evidence": [evidence],
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE",
        "match_confidence": 0.96 if verified_difference else 0.9,
        "difference": min(abs(float(required) - value) for value in summary_values) if verified_difference else None,
        "decision_basis": (
            f"В Задании указано {float(required):g} т/ч, а в таблице технологических режимов ТХ — "
            f"{', '.join(f'{x:g}' for x in summary_values)} т/ч"
            + (f" при количестве линий {line_count}." if line_count is not None else ".")
            if verified_difference else
            f"Найдены сопоставимые по единицам, но разные по смысловому уровню значения: требование — "
            f"{capacity_level_label(required_level)}, ТХ — {capacity_level_label(observed_level)}. "
            "Автоматическое отклонение не формируется."
            if summary_values and not comparable_level else
            "В ТХ найдено требуемое значение, но необходимо подтвердить, что оно относится к суммарной производительности и двум независимым линиям."
            if exact else
            f"В ТХ найдены связанные значения производительности ({', '.join(f'{x:g}' for x in values[:8])} т/ч), но требуемая суммарная производительность и схема двух независимых линий автоматически не подтверждены."
        ),
        "verification_kernel": "CAPACITY_AND_PROCESS_TOPOLOGY",
    }


def _query_text(requirement: dict[str, Any]) -> str:
    return " ".join(
        part for part in (
            str(requirement.get("source_row_title") or ""),
            str(requirement.get("requirement_text") or ""),
        ) if part.strip()
    )


def _negative_applicability_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    if str(requirement.get("requirement_type") or "") != "PROHIBITION_OR_NOT_REQUIRED":
        return None
    title = str(requirement.get("source_row_title") or "")
    terms = _significant_terms(title)
    if len(terms) < 2:
        return None
    ranked: list[tuple[int, dict[str, Any], list[str]]] = []
    for page in _candidate_pages(page_corpus, ()):
        low = _norm(page.get("text") or "")
        if not any(marker in low for marker in NEGATIVE_MARKERS):
            continue
        hits = [term for term in terms if term in low]
        if len(hits) < min(3, len(terms)):
            continue
        score = 55 + len(hits) * 8
        ranked.append((score, page, hits))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return None
    score, page, hits = ranked[0]
    snippet = _context(page.get("text") or "", hits + list(NEGATIVE_MARKERS), radius=500)
    evidence = {
        "evidence_kind": "QUALIFIED_NEGATIVE_APPLICABILITY",
        "evidence_state": "verified_candidate",
        "document": page.get("document"), "document_type": page.get("document_type"),
        "page": page.get("page"), "context": snippet,
        "score": min(100, score), "matched_terms": hits,
        "negative_assertion": True,
    }
    return {
        "status": "Соответствует заданию",
        "evidence": [f"{page.get('document')}, стр. {page.get('page')}: {snippet}"],
        "evidence_candidates": [evidence], "verification_evidence": [evidence],
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE",
        "match_confidence": min(0.97, score / 100),
        "decision_basis": "В проектной документации найдено адресное явное подтверждение неприменимости/отсутствия требуемого решения.",
        "verification_kernel": "NEGATIVE_APPLICABILITY_EXECUTOR",
    }


def _normative_ids(text: str) -> list[str]:
    return list(dict.fromkeys(_norm(match.group(0)) for match in NORMATIVE_REF_RE.finditer(str(text or ""))))


def _normative_factual_requirement(text: str) -> bool:
    low = _norm(text)
    if any(token in low for token in (
        "выполнить", "предусмотреть", "должны соответствовать", "разработать",
        "основания для установки", "проектные решения",
    )):
        return False
    if "климатическ" in low and any(token in low for token in ("район", "зона")):
        return True
    material_markers = ("извест", "цемент", "бетон", "сталь", "щебен", "песок")
    return bool(NORMATIVE_REF_RE.search(text) and any(marker in low for marker in material_markers))


def _normative_assertion_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    if str(requirement.get("requirement_type") or "") != "NORMATIVE_COMPLIANCE":
        return None
    text = str(requirement.get("requirement_text") or "")
    norm_ids = _normative_ids(text)
    if not norm_ids:
        return None
    terms = _significant_terms(text)
    factual = _normative_factual_requirement(text)
    sections = list((requirement.get("evidence_contract_v2") or {}).get("expected_sections") or [])
    ranked: list[tuple[int, dict[str, Any], list[str], list[str]]] = []
    for page in _candidate_pages(page_corpus, sections):
        low = _norm(page.get("text") or "")
        matched_norms = [norm for norm in norm_ids if norm in low]
        if not matched_norms:
            continue
        hits = [term for term in terms if term in low]
        distinctive = [term for term in hits if not any(term in norm for norm in matched_norms)]
        if factual and len(distinctive) < 2:
            continue
        score = 48 + len(matched_norms) * 18 + min(28, len(distinctive) * 4)
        ranked.append((score, page, matched_norms, distinctive))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return None
    score, page, matched_norms, distinctive = ranked[0]
    snippet = _context(page.get("text") or "", matched_norms + distinctive, radius=520)
    verified = bool(factual and len(distinctive) >= 2)
    evidence = {
        "evidence_kind": "QUALIFIED_NORMATIVE_ASSERTION" if verified else "NORMATIVE_REFERENCE_CANDIDATE",
        "evidence_state": "verified_candidate" if verified else "candidate",
        "document": page.get("document"), "document_type": page.get("document_type"),
        "page": page.get("page"), "context": snippet,
        "score": min(100, score), "matched_normative_refs": matched_norms,
        "matched_terms": distinctive,
    }
    return {
        "status": "Соответствует заданию" if verified else "Требует проверки",
        "evidence": [f"{page.get('document')}, стр. {page.get('page')}: {snippet}"],
        "evidence_candidates": [evidence], "verification_evidence": [evidence],
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE" if verified else "CANDIDATE_EVIDENCE",
        "match_confidence": 0.95 if verified else min(0.82, score / 100),
        "decision_basis": (
            "В проектной документации адресно подтверждена та же нормативно заданная фактическая характеристика."
            if verified else
            "Найдена та же нормативная ссылка, но выполнение проектного требования требует отдельного доказательства."
        ),
        "verification_kernel": "NORMATIVE_ASSERTION_EXECUTOR",
    }


def _design_determined_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    if str(requirement.get("requirement_type") or "") != "DESIGN_DETERMINED":
        return None
    title = str(requirement.get("source_row_title") or "")
    terms = _significant_terms(title)
    if len(terms) < 2:
        return None
    sections = list((requirement.get("evidence_contract_v2") or {}).get("expected_sections") or [])
    ranked: list[tuple[int, dict[str, Any], list[str]]] = []
    for page in _candidate_pages(page_corpus, sections):
        low = _norm(page.get("text") or "")
        hits = [term for term in terms if term in low]
        if len(hits) < min(3, len(terms)):
            continue
        if not any(marker in low for marker in DESIGN_MARKERS):
            continue
        score = 48 + len(hits) * 10 + (12 if sections else 0)
        ranked.append((score, page, hits))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return None
    score, page, hits = ranked[0]
    snippet = _context(page.get("text") or "", hits, radius=520)
    evidence = {
        "evidence_kind": "QUALIFIED_DESIGN_DETERMINED",
        "evidence_state": "verified_candidate",
        "document": page.get("document"), "document_type": page.get("document_type"),
        "page": page.get("page"), "context": snippet,
        "score": min(100, score), "matched_terms": hits,
    }
    return {
        "status": "Соответствует заданию",
        "evidence": [f"{page.get('document')}, стр. {page.get('page')}: {snippet}"],
        "evidence_candidates": [evidence], "verification_evidence": [evidence],
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE",
        "match_confidence": min(0.95, score / 100),
        "decision_basis": "Параметр, оставленный Заданием на определение проектом, найден в адресном проектном решении.",
        "verification_kernel": "DESIGN_DETERMINED_EXECUTOR",
    }


def _generic_passage_candidates(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = str(requirement.get("requirement_text") or "")
    query_text = _query_text(requirement)
    terms = _significant_terms(query_text)
    if len(terms) < 3:
        return None
    sections = list((requirement.get("evidence_contract_v2") or {}).get("expected_sections") or [])
    ranked: list[tuple[int, dict[str, Any], list[str]]] = []
    for page in _candidate_pages(page_corpus, sections):
        low = _norm(page.get("text") or "")
        hits = [term for term in terms if term in low]
        if len(hits) < 3:
            continue
        score = len(hits) * 7 + (12 if any(marker in low for marker in DESIGN_MARKERS) else 0) + (12 if sections else 0)
        ranked.append((score, page, hits))
    ranked.sort(key=lambda x: x[0], reverse=True)
    if not ranked:
        return None
    score, page, hits = ranked[0]
    snippet = _context(page.get("text") or "", hits)
    rtype = str(requirement.get("requirement_type") or "")
    low = _norm(page.get("text") or "")
    contract = requirement.get("evidence_contract_v2") or {}
    critical = [str(x) for x in contract.get("critical_qualifiers") or []]
    qualifier_ok = all(_norm(item) in low for item in critical)
    denominator = max(1, min(len(terms), 8))
    coverage = len(hits[:8]) / denominator
    strong_presence = bool(
        rtype == "PRESENCE_REQUIREMENT"
        and sections
        and len(hits) >= 4
        and coverage >= 0.60
        and qualifier_ok
        and any(marker in low for marker in DESIGN_MARKERS)
    )
    evidence = {
        "evidence_kind": "QUALIFIED_PROJECT_PASSAGE" if strong_presence else "SOURCE_LOCKED_PASSAGE",
        "evidence_state": "verified_candidate" if strong_presence else "candidate",
        "document": page.get("document"), "document_type": page.get("document_type"), "page": page.get("page"),
        "context": snippet, "score": min(100, score), "matched_terms": hits,
        "semantic_coverage": round(coverage, 3),
        "critical_qualifiers_satisfied": qualifier_ok,
    }
    return {
        "status": "Соответствует заданию" if strong_presence else "Требует проверки",
        "evidence": [f"{page.get('document')}, стр. {page.get('page')}: {snippet}"],
        "evidence_candidates": [evidence], "verification_evidence": [evidence],
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE" if strong_presence else "CANDIDATE_EVIDENCE",
        "match_confidence": min(.95 if strong_presence else .79, score / 100),
        "decision_basis": (
            "Адресное проектное решение подтверждено в ожидаемом профильном разделе с достаточным покрытием ключевых условий."
            if strong_presence else
            "Найден профильный проектный фрагмент. Для категоричного вывода требуется специализированный типизированный checker."
        ),
        "verification_kernel": "GENERIC_PRESENCE_EXECUTOR" if strong_presence else "SOURCE_LOCKED_RETRIEVAL",
    }


def verify_assignment_requirement(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Run trusted Assignment checkers before generic semantic fallback."""
    checkers=(
        _equipment_check,
        _capacity_topology_check,
        _negative_applicability_check,
        _normative_assertion_check,
        _design_determined_check,
        _concept_check,
    )
    for checker in checkers:
        result = checker(requirement, page_corpus)
        if result:
            return result
    if str(requirement.get('requirement_type') or '') not in {'SET_COMPARISON','PROHIBITION_OR_NOT_REQUIRED'}:
        return _generic_passage_candidates(requirement,page_corpus)
    return None
