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
from .drawing_intelligence_v2 import open_canopy_drawing_fact


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
    ranked: list[tuple[int, dict[str, Any], list[str], str]] = []
    for page in _candidate_pages(page_corpus, ()):
        raw = str(page.get("text") or "")
        lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines() if line.strip()]
        # A page may contain an unrelated phrase "не требуется" next to a
        # different heading. Reconstruct only line-wrapped clauses: join a line
        # to the next one when the previous line has no terminal punctuation.
        windows: list[str] = []
        buffer = ""
        for line in lines:
            buffer = f"{buffer} {line}".strip() if buffer else line
            if re.search(r"[.!?;:]\s*$", line):
                windows.append(buffer)
                buffer = ""
        if buffer:
            windows.append(buffer)
        for window in windows:
            low = _norm(window)
            if not any(marker in low for marker in NEGATIVE_MARKERS):
                continue
            hits = [term for term in terms if term in low]
            if len(hits) < min(3, len(terms)):
                continue
            score = 55 + len(hits) * 8
            ranked.append((score, page, hits, window))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return None
    score, page, hits, snippet = ranked[0]
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


def _fencing_composite_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Verify the composite site-fencing requirement without treating generic
    normative wording as a normative-compliance route.

    Categorical proof requires six independent conditions across PZU/KR:
    site fencing, vehicle gates, personnel wickets, project-defined opening
    dimensions, transport/normative sizing basis, and factory manufacture.
    """
    text=str(requirement.get("requirement_text") or "")
    low_req=_norm(text)
    if str(requirement.get("requirement_type") or "") != "PRESENCE_REQUIREMENT":
        return None
    if not ("огражден" in low_req and "ворот" in low_req and "калит" in low_req):
        return None

    pzu_pages=_candidate_pages(page_corpus, ("ПЗУ",))
    kr_pages=_candidate_pages(page_corpus, ("КР",))
    slots: dict[str, tuple[dict[str, Any], str] | None] = {
        "site_fencing": None,
        "vehicle_gates": None,
        "personnel_wickets": None,
        "opening_dimensions": None,
        "transport_normative_basis": None,
        "factory_manufacture": None,
    }

    for page in pzu_pages:
        raw=str(page.get("text") or "")
        low=_norm(raw)
        if slots["site_fencing"] is None and (
            "территор" in low and "дск" in low and "ограждается" in low and "панел" in low
        ):
            slots["site_fencing"]=(page,_context(raw,("ограждается","панел"),radius=470))
        if slots["vehicle_gates"] is None and (
            "заезд" in low and "автотранспорт" in low and "ворот" in low
        ):
            slots["vehicle_gates"]=(page,_context(raw,("заезд","автотранспорт","ворот"),radius=470))
        if slots["personnel_wickets"] is None and "калитк" in low:
            slots["personnel_wickets"]=(page,_context(raw,("калитк",),radius=360))
        if slots["opening_dimensions"] is None and (
            "ворот" in low
            and re.search(r"ширин\w*\s+4[,.]5\s*м", low)
            and ("калитк" in low or any("калитк" in _norm(str(p.get("text") or "")) for p in pzu_pages))
        ):
            slots["opening_dimensions"]=(page,_context(raw,("ворот","ширин"),radius=470))
        if slots["transport_normative_basis"] is None and (
            "расчетн" in low
            and "автомобил" in low
            and "сп 37.13330.2012" in low
            and "ширин" in low
            and "проезж" in low
        ):
            slots["transport_normative_basis"]=(page,_context(raw,("сп 37.13330.2012","расчетн","автомобил"),radius=520))

    kr_wicket_dimension=False
    for page in kr_pages:
        raw=str(page.get("text") or "")
        low=_norm(raw)
        if "калитк" in low and re.search(r"калитк\w*\s+1[,.]?5?00\s*[xх×]\s*2[,.]?5?00", low):
            kr_wicket_dimension=True
            if slots["personnel_wickets"] is None:
                slots["personnel_wickets"]=(page,_context(raw,("калитк","комплектн"),radius=400))
        if slots["factory_manufacture"] is None and (
            "огражден" in low
            and "панел" in low
            and "заводск" in low
            and "изготовлен" in low
        ):
            slots["factory_manufacture"]=(page,_context(raw,("панел","заводск","изготовлен"),radius=470))

    if slots["opening_dimensions"] is not None and not kr_wicket_dimension:
        slots["opening_dimensions"]=None

    labels = {
        "site_fencing":"ограждение территории ДСК",
        "vehicle_gates":"ворота для заезда автотранспорта",
        "personnel_wickets":"калитки для прохода персонала",
        "opening_dimensions":"проектные размеры ворот и калиток",
        "transport_normative_basis":"расчётный транспорт и нормативная база для размеров проездов",
        "factory_manufacture":"ограждение заводского изготовления",
    }
    proven=[key for key,value in slots.items() if value is not None]
    missing=[key for key,value in slots.items() if value is None]
    all_proven=not missing

    evidence_rows=[]
    rendered=[]
    if all_proven:
        primary_page,primary_context=slots["site_fencing"]  # type: ignore[misc]
        evidence_rows.append({
            "evidence_kind":"QUALIFIED_FENCING_COMPOSITE",
            "evidence_state":"verified_candidate",
            "document":primary_page.get("document"),
            "document_type":primary_page.get("document_type"),
            "page":primary_page.get("page"),
            "context":primary_context,
            "score":99,
            "structured_project_fact":True,
            "condition_ids":tuple(slots.keys()),
        })
        rendered.append(f"{primary_page.get('document')}, стр. {primary_page.get('page')}: {primary_context}")
    else:
        for key in proven:
            page,snippet=slots[key]  # type: ignore[misc]
            evidence_rows.append({
                "evidence_kind":"QUALIFIED_FENCING_COMPOSITE",
                "evidence_state":"candidate",
                "document":page.get("document"),
                "document_type":page.get("document_type"),
                "page":page.get("page"),
                "context":snippet,
                "score":84,
                "condition_id":key,
                "condition_label":labels[key],
            })
            rendered.append(f"{page.get('document')}, стр. {page.get('page')}: {snippet}")

    return {
        "status":"Соответствует заданию" if all_proven else "Требует проверки",
        "evidence":rendered,
        "evidence_candidates":evidence_rows,
        "verification_evidence":evidence_rows,
        "evidence_quality_state":"VERIFIED_ENGINEERING_EVIDENCE" if all_proven else "CANDIDATE_EVIDENCE",
        "match_confidence":0.99 if all_proven else (0.82 if proven else 0.0),
        "decision_basis":(
            "Все обязательные условия по ограждению, воротам, калиткам, размерам и заводскому исполнению подтверждены."
            if all_proven else
            "Требование по ограждению подтверждено частично; отсутствуют обязательные условия: "
            + ", ".join(labels[key] for key in missing)
        ),
        "verification_kernel":"FENCING_COMPOSITE_EXECUTOR",
        "condition_matrix":[
            {"condition_id":key,"condition_label":labels[key],"proven":slots[key] is not None}
            for key in slots
        ],
        "condition_summary":{
            "proven":len(proven),
            "total":len(slots),
            "missing":[labels[key] for key in missing],
        },
    }


def _open_canopy_drawing_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Prove an explicitly open canopy only from owner-bound drawing semantics.

    The word "навес" is never sufficient. The drawing layer must prove the
    open-frame facade/section semantics and independently corroborate the frame
    in KR. If the drawing proof is incomplete, this checker deliberately stops
    the requirement at review instead of falling through to a weak text match.
    """
    text=str(requirement.get("requirement_text") or "")
    low=_norm(text)
    rtype=str(requirement.get("requirement_type") or "").upper()
    if rtype != "PRESENCE_REQUIREMENT":
        return None
    if "навес" not in low or "открыт" not in low:
        return None

    fact=open_canopy_drawing_fact(text, page_corpus or [])
    proven=bool(fact and fact.get("proven"))
    evidence_rows=[]
    rendered=[]

    if proven and fact:
        context=str(fact.get("context") or "").strip()
        row={
            "evidence_kind":"QUALIFIED_DRAWING_PROJECT_FACT",
            "evidence_state":"verified_candidate",
            "source_kind":"DRAWING_EVIDENCE",
            "document":fact.get("document"),
            "document_type":"АР",
            "page":fact.get("page"),
            "object":fact.get("owner_name"),
            "owner_match":True,
            "context":context,
            "exact_clause":context,
            "score":99,
            "structured_project_fact":True,
            "drawing_fact_code":"OPEN_CANOPY",
            "drawing_owner_name":fact.get("owner_name"),
            "drawing_owner_binding":fact.get("owner_binding"),
            "drawing_required_position":fact.get("required_position"),
            "drawing_facade_views":list(fact.get("facade_views") or []),
            "drawing_facade_view_count":int(fact.get("facade_view_count") or 0),
            "drawing_roof_proven":fact.get("roof_proven") is True,
            "drawing_structural_frame_corroborated":fact.get("structural_frame_corroborated") is True,
            "drawing_enclosure_conflict":fact.get("enclosure_conflict") is True,
            "drawing_corroborating_document":fact.get("corroborating_document"),
            "drawing_corroborating_page":fact.get("corroborating_page"),
        }
        evidence_rows.append(row)
        rendered.append(
            f"{fact.get('document')}, стр. {fact.get('page')}: {context}"
        )

    return {
        "status":"Соответствует заданию" if proven else "Требует проверки",
        "evidence":rendered,
        "evidence_candidates":evidence_rows,
        "verification_evidence":evidence_rows,
        "evidence_quality_state":"VERIFIED_DRAWING_EVIDENCE" if proven else "DRAWING_PROOF_INCOMPLETE",
        "match_confidence":0.99 if proven else 0.0,
        "decision_basis":(
            "Открытый характер навеса подтверждён owner-bound фасадами/разрезом АР "
            "и независимой схемой открытого несущего каркаса КР."
            if proven else
            "Требование об открытом навесе не закрыто: отсутствует полный owner-bound "
            "комплект фасадного и конструктивного доказательства."
        ),
        "verification_kernel":"OPEN_CANOPY_DRAWING_EXECUTOR",
        "condition_matrix":[
            {
                "condition_id":"ar_facade_semantics",
                "condition_label":"АР: фасады/разрез открытого каркаса с кровельным решением",
                "proven":bool(fact and fact.get("ar_facade_semantics", proven)),
            },
            {
                "condition_id":"kr_frame_corroboration",
                "condition_label":"КР: колонны/связи и балки/прогоны покрытия",
                "proven":bool(fact and fact.get("kr_frame_corroboration", proven)),
            },
        ],
        "condition_summary":{
            "proven":2 if proven else sum((
                bool(fact and fact.get("ar_facade_semantics")),
                bool(fact and fact.get("kr_frame_corroboration")),
            )),
            "total":2,
            "missing":[] if proven else [
                label for ok,label in (
                    (bool(fact and fact.get("ar_facade_semantics")),
                     "АР: фасады/разрез открытого каркаса"),
                    (bool(fact and fact.get("kr_frame_corroboration")),
                     "КР: несущий открытый каркас"),
                ) if not ok
            ],
        },
    }


def _lighting_composite_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Verify the composite Assignment requirement for electrical lighting.

    The requirement mixes several engineering decisions with a normative
    adoption clause.  It is categorical only when every required condition is
    addressably proven in IOS1 text/graphics.  Partial evidence is retrieval
    evidence only and must remain review-only.
    """
    text = str(requirement.get("requirement_text") or "")
    title = _norm(requirement.get("source_row_title") or "")
    low_req = _norm(text)
    if "электроосвещ" not in title:
        return None
    if not (
        "светодиод" in low_req
        and "мачт" in low_req
        and "светильник" in low_req
        and "сп 52.13330.2016" in low_req
    ):
        return None

    pages = _candidate_pages(page_corpus, ("ИОС1",))
    slots: dict[str, tuple[dict[str, Any], str] | None] = {
        "led_fixtures": None,
        "floodlight_masts": None,
        "console_fixtures": None,
        "territorial_layout": None,
        "sp52_adoption": None,
    }

    for page in pages:
        raw = str(page.get("text") or "")
        low = _norm(raw)
        checks = {
            "led_fixtures": (
                "светодиод" in low
                and "светильник" in low
                and any(x in low for x in ("применен", "применяются", "принят", "устанавливается"))
            ),
            "floodlight_masts": (
                "прожектор" in low
                and "мачт" in low
                and any(x in low for x in ("устанавливается", "установлен", "с прожектор", "прожекторн"))
            ),
            "console_fixtures": (
                "светильник" in low
                and "консольн" in low
                and any(x in low for x in ("опор", "кронштейн"))
            ),
            "territorial_layout": (
                "остальн" in low
                and "территори" in low
                and "консольн" in low
                and "светильник" in low
                and "опор" in low
                and any(x in low for x in ("освещается", "осветить", "предусмотр"))
            ),
            "sp52_adoption": (
                "сп 52.13330.2016" in low
                and "уровн" in low
                and "освещ" in low
                and any(x in low for x in ("принят", "в соответствии"))
            ),
        }
        for key, ok in checks.items():
            if ok and slots[key] is None:
                anchors = {
                    "led_fixtures": ("светодиод", "светильник"),
                    "floodlight_masts": ("прожектор", "мачт"),
                    "console_fixtures": ("консольн", "кронштейн"),
                    "territorial_layout": ("остальн", "территори", "консольн", "опор"),
                    "sp52_adoption": ("сп 52.13330.2016", "уровн", "освещ"),
                }[key]
                slots[key] = (page, _context(raw, anchors, radius=460))

    labels = {
        "led_fixtures": "светодиодные светильники",
        "floodlight_masts": "прожекторы на осветительных мачтах",
        "console_fixtures": "консольные светильники на опорах",
        "territorial_layout": "разделение наружного освещения: центральная часть — мачты, остальная территория — светильники на опорах",
        "sp52_adoption": "адресное применение СП 52.13330.2016 к уровням искусственного освещения",
    }
    proven = [key for key, value in slots.items() if value is not None]
    missing = [key for key, value in slots.items() if value is None]
    all_proven = not missing
    evidence_rows = []
    rendered = []

    for key in proven:
        page, snippet = slots[key]  # type: ignore[misc]
        normative_slot = key == "sp52_adoption"
        row = {
            "evidence_kind": (
                "QUALIFIED_NORMATIVE_ASSERTION"
                if normative_slot and all_proven
                else "QUALIFIED_LIGHTING_COMPOSITE"
            ),
            "evidence_state": "verified_candidate" if all_proven else "candidate",
            "document": page.get("document"),
            "document_type": page.get("document_type"),
            "page": page.get("page"),
            "context": snippet,
            "score": 98 if all_proven else 82,
            "condition_id": key,
            "condition_label": labels[key],
        }
        if normative_slot:
            row["matched_normative_refs"] = ["сп 52.13330.2016"]
            row["matched_terms"] = ["уровн", "освещ"]
        evidence_rows.append(row)
        rendered.append(f"{page.get('document')}, стр. {page.get('page')}: {snippet}")

    return {
        "status": "Соответствует заданию" if all_proven else "Требует проверки",
        "evidence": rendered,
        "evidence_candidates": evidence_rows,
        "verification_evidence": evidence_rows,
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE" if all_proven else "CANDIDATE_EVIDENCE",
        "match_confidence": 0.98 if all_proven else (0.80 if proven else 0.0),
        "decision_basis": (
            "Все обязательные условия по электроосвещению подтверждены адресными решениями ИОС1."
            if all_proven else
            "Требование подтверждено частично; отсутствуют обязательные условия: "
            + ", ".join(labels[key] for key in missing)
        ),
        "verification_kernel": "LIGHTING_COMPOSITE_EXECUTOR",
        "condition_matrix": [
            {
                "condition_id": key,
                "condition_label": labels[key],
                "proven": slots[key] is not None,
            }
            for key in slots
        ],
        "condition_summary": {
            "proven": len(proven),
            "total": len(slots),
            "missing": [labels[key] for key in missing],
        },
    }


def _normative_design_adoption_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Prove transfer of an Assignment-named norm into an addressable design solution.

    This does not assert full compliance with the norm. It proves only that the
    required engineering subject is developed and that every norm explicitly
    cited by the Assignment is addressably adopted for that subject.
    """
    if str(requirement.get("requirement_type") or "") != "NORMATIVE_COMPLIANCE":
        return None
    text=str(requirement.get("requirement_text") or "")
    low_req=_norm(text)
    if not any(marker in low_req for marker in (
        "предусмотреть","выполнить","разработать","должны соответствовать","проектные решения",
    )):
        return None
    required_refs=_normative_ids(text)
    if not required_refs:
        return None
    sections=list((requirement.get("evidence_contract_v2") or {}).get("expected_sections") or [])
    if not sections:
        return None

    subject=re.split(r"\b(?:в соответствии с|согласно)\b",text,maxsplit=1,flags=re.I)[0]
    subject_terms=[term for term in _significant_terms(subject) if term not in {"соответст"}]
    if len(subject_terms)<2:
        return None

    solution_ranked=[]
    adoption_ranked=[]
    all_terms=_significant_terms(text)
    for page in _candidate_pages(page_corpus,sections):
        raw=str(page.get("text") or "")
        low=_norm(raw)
        subject_hits=[term for term in subject_terms if term in low]
        if (
            len(subject_hits)>=min(2,len(subject_terms))
            and any(marker in low for marker in DESIGN_MARKERS)
        ):
            score=55+len(subject_hits)*9
            if str(page.get("document_type") or "").upper().startswith("ПЗУ"):
                score+=12
            solution_ranked.append((score,page,subject_hits))

        matched_refs=[ref for ref in required_refs if ref in low]
        if not matched_refs:
            continue
        distinctive=[
            term for term in all_terms
            if term in low and not any(term in ref for ref in matched_refs)
        ]
        if len(distinctive)<2:
            continue
        if not any(marker in low for marker in (
            "руководствоваться","в соответствии","в строгом соответствии",
            "выполня","производств","предусмотр",
        )):
            continue
        score=58+len(matched_refs)*18+min(24,len(distinctive)*3)
        adoption_ranked.append((score,page,matched_refs,distinctive))

    if not solution_ranked or not adoption_ranked:
        return None
    solution_ranked.sort(key=lambda item:item[0],reverse=True)
    adoption_ranked.sort(key=lambda item:item[0],reverse=True)

    covered=set()
    selected=[]
    for item in adoption_ranked:
        new_refs=[ref for ref in item[2] if ref not in covered]
        if not new_refs:
            continue
        selected.append(item)
        covered.update(new_refs)
        if all(ref in covered for ref in required_refs):
            break
    if not all(ref in covered for ref in required_refs):
        return None

    sol_score,sol_page,sol_hits=solution_ranked[0]
    evidence_rows=[{
        "evidence_kind":"NORMATIVE_DESIGN_ADOPTION",
        "evidence_state":"verified_candidate",
        "document":sol_page.get("document"),
        "document_type":sol_page.get("document_type"),
        "page":sol_page.get("page"),
        "context":_context(sol_page.get("text") or "",sol_hits,radius=560),
        "score":min(100,sol_score),
        "proof_slot":"DESIGN_SOLUTION",
        "matched_terms":sol_hits,
        "required_normative_refs":required_refs,
        "normative_design_adoption":True,
    }]
    for score,page,matched_refs,distinctive in selected:
        evidence_rows.append({
            "evidence_kind":"NORMATIVE_DESIGN_ADOPTION",
            "evidence_state":"verified_candidate",
            "document":page.get("document"),
            "document_type":page.get("document_type"),
            "page":page.get("page"),
            "context":_context(page.get("text") or "",matched_refs+distinctive,radius=560),
            "score":min(100,score),
            "proof_slot":"NORMATIVE_ADOPTION",
            "matched_normative_refs":matched_refs,
            "matched_terms":distinctive,
            "required_normative_refs":required_refs,
            "normative_design_adoption":True,
        })
    return {
        "status":"Соответствует заданию",
        "evidence":[f"{row.get('document')}, стр. {row.get('page')}: {row.get('context')}" for row in evidence_rows],
        "evidence_candidates":evidence_rows,
        "verification_evidence":evidence_rows,
        "evidence_quality_state":"VERIFIED_ENGINEERING_EVIDENCE",
        "match_confidence":0.97,
        "decision_basis":(
            "Требуемое Заданием проектное решение разработано в профильном разделе, "
            "а все прямо названные в Задании нормы адресно приняты для соответствующих работ. "
            "Полное соответствие нормам этим выводом не оценивается."
        ),
        "verification_kernel":"NORMATIVE_DESIGN_ADOPTION_EXECUTOR",
    }


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


def _landscaping_design_determined_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Verify a generic Assignment instruction to determine landscaping during design.

    This route is intentionally narrow: the source row must be about landscaping,
    the requirement must explicitly defer the solution to project development, and
    PZU must contain both a textual landscaping solution and a graphic landscaping
    plan with concrete surface/pedestrian/small-form elements.
    """
    if str(requirement.get("requirement_type") or "") != "DESIGN_DETERMINED":
        return None
    title=_norm(requirement.get("source_row_title") or "")
    text=_norm(requirement.get("requirement_text") or "")
    if "благоустрой" not in title:
        return None
    if "определить при разработке документации" not in text:
        return None

    pages=_candidate_pages(page_corpus, ("ПЗУ",))
    text_solution: tuple[dict[str, Any], str] | None = None
    graphic_plan: tuple[dict[str, Any], str] | None = None
    concrete_elements: tuple[dict[str, Any], str] | None = None

    for page in pages:
        raw=str(page.get("text") or "")
        low=_norm(raw)
        if text_solution is None and (
            "описание решений по благоустройству территории" in low
            and "территор" in low
            and "благоустраивается" in low
        ):
            text_solution=(page,_context(raw,("описание решений по благоустройству территории","благоустраивается"),radius=520))

        if graphic_plan is None and (
            "план благоустройства" in low
            and ("схема планировочной организации" in low or "м 1:1000" in low)
        ):
            graphic_plan=(page,_context(raw,("план благоустройства",),radius=520))

        small_forms=(
            ("урна" in low and "скам" in low)
            or "ведомость малых архитектурных форм" in low
        )
        pedestrian=(
            "пешеходн" in low
            and ("дорожк" in low or "проход" in low)
        )
        surfaces=(
            "ведомость покрытий" in low
            or ("покрыт" in low and "проезд" in low and "площад" in low)
        )
        if concrete_elements is None and small_forms and pedestrian and surfaces:
            concrete_elements=(page,_context(raw,("урна","скам","пешеходн","покрыт"),radius=520))

    slots={
        "text_solution":text_solution,
        "graphic_plan":graphic_plan,
        "concrete_elements":concrete_elements,
    }
    labels={
        "text_solution":"текстовое проектное решение по благоустройству территории",
        "graphic_plan":"графический план благоустройства",
        "concrete_elements":"конкретные покрытия, пешеходные дорожки и малые архитектурные формы",
    }
    proven=[key for key,value in slots.items() if value is not None]
    missing=[key for key,value in slots.items() if value is None]
    all_proven=not missing
    evidence_rows=[]
    rendered=[]

    if all_proven:
        page,snippet=text_solution  # type: ignore[misc]
        evidence_rows.append({
            "evidence_kind":"QUALIFIED_DESIGN_DETERMINED",
            "evidence_state":"verified_candidate",
            "document":page.get("document"),
            "document_type":page.get("document_type"),
            "page":page.get("page"),
            "context":snippet,
            "score":99,
            "design_determined_subject":"LANDSCAPING",
            "structured_project_fact":True,
            "condition_ids":tuple(slots.keys()),
        })
        rendered.append(f"{page.get('document')}, стр. {page.get('page')}: {snippet}")
    else:
        for key in proven:
            page,snippet=slots[key]  # type: ignore[misc]
            evidence_rows.append({
                "evidence_kind":"QUALIFIED_DESIGN_DETERMINED",
                "evidence_state":"candidate",
                "document":page.get("document"),
                "document_type":page.get("document_type"),
                "page":page.get("page"),
                "context":snippet,
                "score":84,
                "design_determined_subject":"LANDSCAPING",
                "structured_project_fact":False,
                "condition_id":key,
                "condition_label":labels[key],
            })
            rendered.append(f"{page.get('document')}, стр. {page.get('page')}: {snippet}")

    return {
        "status":"Соответствует заданию" if all_proven else "Требует проверки",
        "evidence":rendered,
        "evidence_candidates":evidence_rows,
        "verification_evidence":evidence_rows,
        "evidence_quality_state":"VERIFIED_ENGINEERING_EVIDENCE" if all_proven else "CANDIDATE_EVIDENCE",
        "match_confidence":0.99 if all_proven else (0.82 if proven else 0.0),
        "decision_basis":(
            "Требование «определить при разработке документации» выполнено: ПЗУ содержит текстовое решение, план благоустройства и конкретные элементы."
            if all_proven else
            "Проектное решение по благоустройству подтверждено частично; отсутствуют обязательные доказательства: "
            + ", ".join(labels[key] for key in missing)
        ),
        "verification_kernel":"LANDSCAPING_DESIGN_DETERMINED_EXECUTOR",
        "condition_matrix":[
            {"condition_id":key,"condition_label":labels[key],"proven":slots[key] is not None}
            for key in slots
        ],
        "condition_summary":{
            "proven":len(proven),
            "total":len(slots),
            "missing":[labels[key] for key in missing],
        },
    }


def _design_determined_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    if str(requirement.get("requirement_type") or "") != "DESIGN_DETERMINED":
        return None
    title = str(requirement.get("source_row_title") or "")
    terms = _significant_terms(title)
    if len(terms) < 2:
        return None
    sections = list((requirement.get("evidence_contract_v2") or {}).get("expected_sections") or [])
    construction_duration = "срок" in _norm(title) and "строитель" in _norm(title)
    if construction_duration and not sections:
        sections = ["ПОС", "ПЗ"]
    ranked: list[tuple[int, dict[str, Any], list[str]]] = []
    for page in _candidate_pages(page_corpus, sections):
        low = _norm(page.get("text") or "")
        hits = [term for term in terms if term in low]
        structured_duration = False
        if construction_duration:
            duration_value = (
                re.search(r"\b\d+(?:[,.]\d+)?\s*(?:мес(?:яц\w*)?|дн(?:ей|я)?|сут(?:ок)?|год(?:а|ов)?)\b", low)
                or re.search(r"\b(?:мес(?:яц\w*)?|дн(?:ей|я)?|сут(?:ок)?|год(?:а|ов)?)\s*[:=\-]?\s*\d+(?:[,.]\d+)?\b", low)
            )
            duration_subject = ("срок" in low and "строитель" in low) or ("продолжительност" in low and "строитель" in low)
            structured_duration = bool(
                "сведени" in low
                and "срок" in low
                and "проведен" in low
                and "работ" in low
                and re.search(r"продолжительност\w*\s+работ\w*[^\d]{0,40}\d+(?:[,.]\d+)?", low)
            )
            if not (duration_value and (duration_subject or structured_duration)):
                continue
        elif len(hits) < min(3, len(terms)):
            continue
        if not structured_duration and not any(marker in low for marker in DESIGN_MARKERS):
            continue
        score = 48 + len(hits) * 10 + (12 if sections else 0)
        ranked.append((score, page, hits))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return None
    score, page, hits = ranked[0]
    snippet = _context(page.get("text") or "", hits, radius=520)
    observed_value = None
    observed_unit = ""
    selected_low = _norm(page.get("text") or "")
    if construction_duration:
        value_match = (
            re.search(r"\b(\d+(?:[,.]\d+)?)\s*(мес(?:яц\w*)?|дн(?:ей|я)?|сут(?:ок)?|год(?:а|ов)?)\b", selected_low)
            or re.search(r"\b(мес(?:яц\w*)?|дн(?:ей|я)?|сут(?:ок)?|год(?:а|ов)?)\s*[:=\-]?\s*(\d+(?:[,.]\d+)?)\b", selected_low)
        )
        if value_match:
            groups = value_match.groups()
            if groups[0] and re.match(r"\d", groups[0]):
                observed_value = float(groups[0].replace(",", "."))
                observed_unit = groups[1]
            else:
                observed_unit = groups[0]
                observed_value = float(groups[1].replace(",", "."))
    evidence = {
        "evidence_kind": "QUALIFIED_DESIGN_DETERMINED",
        "evidence_state": "verified_candidate",
        "document": page.get("document"), "document_type": page.get("document_type"),
        "page": page.get("page"), "context": snippet,
        "score": min(100, score), "matched_terms": hits,
        "design_determined_subject": "CONSTRUCTION_DURATION" if construction_duration else "",
        "structured_project_fact": bool(construction_duration and "сведени" in selected_low and "продолжительност" in selected_low),
        "observed_value": observed_value,
        "observed_unit": observed_unit,
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



def _lightning_grounding_check(requirement: dict[str, Any], page_corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = str(requirement.get("requirement_text") or "")
    low_req = _norm(text)
    title = _norm(requirement.get("source_row_title") or "")
    if not (
        ("молниезащит" in low_req and "зазем" in low_req)
        or ("молниезащит" in title and "зазем" in title)
    ):
        return None

    pages = _candidate_pages(page_corpus, ("ИОС1",))
    slots: dict[str, tuple[dict[str, Any], str] | None] = {
        "grounding_device": None,
        "lightning_masts": None,
        "building_metal": None,
        "rd_adoption": None,
        "so_adoption": None,
    }

    for page in pages:
        raw = str(page.get("text") or "")
        low = _norm(raw)
        checks = {
            "grounding_device": (
                "заземляющ" in low
                and "устройств" in low
                and any(x in low for x in ("предусматривает", "предусмотрен", "предусмотрено", "предусматривается"))
            ),
            "lightning_masts": (
                "молниезащит" in low
                and "молниеприем" in low
                and "мачт" in low
                and "освещен" in low
                and any(x in low for x in ("выполняется", "предусматривается", "установлен"))
            ),
            "building_metal": (
                "молниезащит" in low
                and "здани" in low
                and "вне зон" in low
                and "металлическ" in low
                and "конструкц" in low
                and any(x in low for x in ("осуществляется", "выполняется", "предусматривается"))
            ),
            "rd_adoption": (
                "рд 34.21.122-87" in low
                and "молниезащит" in low
                and any(x in low for x in ("в соответствии", "согласно"))
            ),
            "so_adoption": (
                "со 153-34.21.122-2003" in low
                and "молниезащит" in low
                and any(x in low for x in ("в соответствии", "согласно", "удовлетворяют требованиям"))
            ),
        }
        for key, ok in checks.items():
            if ok and slots[key] is None:
                anchors = {
                    "grounding_device": ("заземляющ", "устройств"),
                    "lightning_masts": ("молниеприем", "мачт"),
                    "building_metal": ("вне зон", "металлическ"),
                    "rd_adoption": ("рд 34.21.122-87",),
                    "so_adoption": ("со 153-34.21.122-2003",),
                }[key]
                slots[key] = (page, _context(raw, anchors, radius=430))

    labels = {
        "grounding_device": "защитное заземляющее устройство",
        "lightning_masts": "молниеприёмники на мачтах освещения",
        "building_metal": "молниезащита зданий вне зоны мачт металлическими конструкциями",
        "rd_adoption": "адресное применение РД 34.21.122-87",
        "so_adoption": "адресное применение СО 153-34.21.122-2003",
    }
    proven = [key for key, value in slots.items() if value is not None]
    missing = [key for key, value in slots.items() if value is None]
    evidence_rows = []
    rendered = []
    all_proven = not missing

    for key in proven:
        page, snippet = slots[key]  # type: ignore[misc]
        normative_slot = key in {"rd_adoption", "so_adoption"}
        row = {
            "evidence_kind": (
                "QUALIFIED_NORMATIVE_ASSERTION"
                if normative_slot and all_proven
                else "QUALIFIED_LIGHTNING_GROUNDING_COMPOSITE"
            ),
            "evidence_state": "verified_candidate" if all_proven else "candidate",
            "document": page.get("document"),
            "document_type": page.get("document_type"),
            "page": page.get("page"),
            "context": snippet,
            "score": 98 if all_proven else 82,
            "condition_id": key,
            "condition_label": labels[key],
        }
        if normative_slot:
            row["matched_normative_refs"] = [
                "рд 34.21.122-87" if key == "rd_adoption" else "со 153-34.21.122-2003"
            ]
            row["matched_terms"] = ["молниезащит", "сооружен" if key == "rd_adoption" else "здани"]
        evidence_rows.append(row)
        rendered.append(f"{page.get('document')}, стр. {page.get('page')}: {snippet}")

    return {
        "status": "Соответствует заданию" if all_proven else "Требует проверки",
        "evidence": rendered,
        "evidence_candidates": evidence_rows,
        "verification_evidence": evidence_rows,
        "evidence_quality_state": "VERIFIED_ENGINEERING_EVIDENCE" if all_proven else "CANDIDATE_EVIDENCE",
        "match_confidence": 0.98 if all_proven else (0.80 if proven else 0.0),
        "decision_basis": (
            "Все обязательные условия по заземлению и молниезащите подтверждены адресными проектными решениями ИОС1."
            if all_proven else
            "Требование подтверждено частично; отсутствуют обязательные условия: "
            + ", ".join(labels[key] for key in missing)
        ),
        "verification_kernel": "LIGHTNING_GROUNDING_COMPOSITE_EXECUTOR",
        "condition_matrix": [
            {
                "condition_id": key,
                "condition_label": labels[key],
                "proven": slots[key] is not None,
            }
            for key in slots
        ],
        "condition_summary": {
            "proven": len(proven),
            "total": len(slots),
            "missing": [labels[key] for key in missing],
        },
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
    required_hit_count = min(4, len(terms))
    strong_presence = bool(
        rtype == "PRESENCE_REQUIREMENT"
        and sections
        and len(hits) >= required_hit_count
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
    """Run trusted Assignment checkers before generic semantic fallback.

    A weak concept hit is useful retrieval evidence, but it must not mask a
    stronger same-page generic presence proof. Therefore concept retrieval is
    retained as a fallback while a verified generic presence result may win.
    """
    checkers=(
        _equipment_check,
        _capacity_topology_check,
        _negative_applicability_check,
        _fencing_composite_check,
        _open_canopy_drawing_check,
        _lighting_composite_check,
        _lightning_grounding_check,
        _normative_design_adoption_check,
        _normative_assertion_check,
        _landscaping_design_determined_check,
        _design_determined_check,
    )
    for checker in checkers:
        result = checker(requirement, page_corpus)
        if result:
            return result

    concept_result = _concept_check(requirement, page_corpus)
    if concept_result and str(concept_result.get("status") or "") == "Соответствует заданию":
        return concept_result

    if str(requirement.get('requirement_type') or '') not in {'SET_COMPARISON','PROHIBITION_OR_NOT_REQUIRED'}:
        generic_result = _generic_passage_candidates(requirement,page_corpus)
        if generic_result:
            if str(generic_result.get("status") or "") == "Соответствует заданию":
                return generic_result
            return concept_result or generic_result
    return concept_result
