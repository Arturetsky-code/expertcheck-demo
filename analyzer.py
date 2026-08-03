from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

import fitz


@dataclass
class Finding:
    document: str
    document_type: str
    page: int
    parameter_code: str
    parameter_name: str
    value: float | None
    value_text: str
    unit: str | None
    context: str
    confidence: float
    object_hint: str
    match_method: str = "контекстный поиск"
    review_note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\xad", "")
    text = text.replace("‐", "-").replace("‑", "-").replace("–", "-")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalized_search_text(text: str) -> str:
    return text.lower().replace("ё", "е")


def normalize_number(raw: str) -> float | None:
    cleaned = raw.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def read_pdf(file_obj: BinaryIO | bytes, filename: str) -> list[tuple[int, str]]:
    data = file_obj if isinstance(file_obj, bytes) else file_obj.read()
    doc = fitz.open(stream=data, filetype="pdf")
    return [(i + 1, normalize_text(page.get_text("text"))) for i, page in enumerate(doc)]


def classify_document(filename: str, first_pages_text: str, document_types: list[dict]) -> str:
    haystack = normalized_search_text(f"{filename}\n{first_pages_text}")
    # Сначала ищем точные шифры частей: ПЗУ1, ПЗУ2, АР1, АР2, ТХ1, ТХ2.
    for item in sorted(document_types, key=lambda x: len(x["code"]), reverse=True):
        code = item["code"]
        token_patterns = [
            rf"(?<![а-яa-z0-9]){re.escape(code.lower())}(?![а-яa-z0-9])",
            rf"-пд-{re.escape(code.lower())}(?![а-яa-z0-9])",
        ]
        if any(re.search(p, haystack) for p in token_patterns):
            return code
    scores: list[tuple[int, str]] = []
    for item in document_types:
        score = sum(1 for p in item["patterns"] if normalized_search_text(p) in haystack)
        scores.append((score, item["code"]))
    scores.sort(reverse=True)
    return scores[0][1] if scores and scores[0][0] else "НЕОПРЕДЕЛЕН"


def _context(text: str, start: int, end: int, window: int = 220) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    fragment = text[left:right].replace("\n", " ")
    return re.sub(r"\s+", " ", fragment).strip()


def _object_occurrences(text: str, objects: list[dict]) -> list[tuple[int, int, int, str, str]]:
    low = normalized_search_text(text)
    hits: list[tuple[int, int, int, str, str]] = []
    for obj in objects:
        for alias in obj["aliases"]:
            alias_low = normalized_search_text(alias)
            for match in re.finditer(re.escape(alias_low), low):
                hits.append((match.start(), match.end(), len(alias_low), obj["canonical"], alias))
    return hits


def detect_object(page_text: str, match_start: int, match_end: int, objects: list[dict]) -> tuple[str, float]:
    """Связывает показатель с ближайшим названием объекта на странице.

    В таблицах ПЗ название объекта часто расположено после ТЭП, а в текстовых
    разделах — перед ними. Поэтому поиск выполняется в обе стороны, а не только
    по предшествующему фрагменту.
    """
    center = (match_start + match_end) / 2
    candidates = []
    for start, end, alias_len, canonical, alias in _object_occurrences(page_text, objects):
        alias_center = (start + end) / 2
        distance = abs(alias_center - center)
        if distance > 650:
            continue
        # Более длинное точное название надёжнее короткой аббревиатуры.
        score = distance - min(alias_len, 80) * 1.8
        # Заголовок/название после набора ТЭП типично для таблицы ПЗ.
        if start >= match_end and distance <= 320:
            score -= 35
        candidates.append((score, distance, -alias_len, canonical))
    if not candidates:
        return "Не определён", 0.0
    candidates.sort()
    best = candidates[0]
    confidence = 0.94 if best[1] <= 160 else 0.84 if best[1] <= 320 else 0.70
    return best[3], confidence


def _page_is_contents(text: str) -> bool:
    low = normalized_search_text(text)
    return "содержание" in low[:700] and (low.count(".....") >= 2 or low.count("....") >= 4)


def _excluded_context(segment: str, param: dict) -> bool:
    low = normalized_search_text(segment)
    return any(normalized_search_text(x) in low for x in param.get("exclude_context", []))


def _value_candidates(segment: str, param: dict) -> list[tuple[re.Match, str]]:
    patterns = param.get("value_patterns") or ([param["value_pattern"]] if param.get("value_pattern") else [])
    matches: list[tuple[re.Match, str]] = []
    for index, pattern in enumerate(patterns):
        for match in re.finditer(pattern, segment, flags=re.I | re.S):
            matches.append((match, f"шаблон {index + 1}"))
    matches.sort(key=lambda item: (item[0].start(), item[0].end() - item[0].start()))
    return matches


def extract_findings(
    filename: str,
    document_type: str,
    pages: list[tuple[int, str]],
    parameters: list[dict],
    objects: list[dict],
) -> list[Finding]:
    findings: list[Finding] = []
    identity_added: set[str] = set()

    for page_no, text in pages:
        low = normalized_search_text(text)
        contents_page = _page_is_contents(text)
        for param in parameters:
            # Идентификационные признаки извлекаются один раз на документ.
            if param.get("once_per_document") and param["code"] in identity_added:
                continue
            if contents_page and not param.get("allow_contents", False):
                continue
            allowed_docs = param.get("document_types")
            if allowed_docs and document_type not in allowed_docs:
                continue

            for keyword in param["keywords"]:
                key = normalized_search_text(keyword)
                for km in re.finditer(re.escape(key), low):
                    local_before = text[max(0, km.start() - 90):km.start()]
                    local_after = text[km.start():min(len(text), km.end() + param.get("search_window", 180))]
                    if _excluded_context(local_before + " " + local_after, param):
                        continue

                    if not param.get("value_patterns") and not param.get("value_pattern"):
                        ctx = _context(text, km.start(), km.end())
                        object_hint, object_conf = detect_object(text, km.start(), km.end(), objects)
                        confidence = 0.97 if page_no <= 2 else 0.82
                        findings.append(Finding(
                            document=filename,
                            document_type=document_type,
                            page=page_no,
                            parameter_code=param["code"],
                            parameter_name=param["name"],
                            value=None,
                            value_text=keyword,
                            unit=param.get("unit"),
                            context=ctx,
                            confidence=confidence,
                            object_hint=object_hint,
                            match_method="идентификационный признак",
                        ))
                        identity_added.add(param["code"])
                        break

                    segment_end = min(len(text), km.end() + param.get("search_window", 180))
                    segment = text[km.start():segment_end]
                    candidates = _value_candidates(segment, param)
                    if not candidates:
                        continue
                    vm, method = candidates[0]
                    raw_value = vm.groupdict().get("value")
                    raw_unit = vm.groupdict().get("unit")
                    if raw_value is None:
                        continue
                    value = normalize_number(raw_value)
                    if value is None:
                        continue
                    absolute_end = km.start() + vm.end()
                    absolute_value_start = km.start() + vm.start()
                    object_hint, object_conf = detect_object(text, km.start(), absolute_end, objects)

                    distance = vm.start()
                    confidence = 0.96 if distance <= 55 else 0.88 if distance <= 110 else 0.76
                    if object_hint == "Не определён":
                        confidence -= 0.16
                    else:
                        confidence = min(0.98, confidence * 0.78 + object_conf * 0.22)
                    if contents_page:
                        confidence -= 0.25

                    ctx = _context(text, km.start(), absolute_end)
                    findings.append(Finding(
                        document=filename,
                        document_type=document_type,
                        page=page_no,
                        parameter_code=param["code"],
                        parameter_name=param["name"],
                        value=value,
                        value_text=re.sub(r"\s+", " ", vm.group(0)).strip(),
                        unit=raw_unit or param.get("unit"),
                        context=ctx,
                        confidence=max(0.0, round(confidence, 3)),
                        object_hint=object_hint,
                        match_method=method,
                        review_note="" if confidence >= 0.82 else "Проверить привязку значения к объекту",
                    ))

    # Удаление дублей: одинаковое значение одного параметра на одной странице.
    unique: dict[tuple, Finding] = {}
    for item in findings:
        key = (
            item.document,
            item.page,
            item.parameter_code,
            item.object_hint,
            item.value,
            normalize_unit(item.unit),
        )
        previous = unique.get(key)
        if previous is None or item.confidence > previous.confidence:
            unique[key] = item
    return list(unique.values())


def normalize_unit(unit: str | None) -> str:
    if not unit:
        return ""
    u = normalized_search_text(unit)
    u = re.sub(r"\s+", "", u).replace("²", "2").replace("³", "3").replace(".", "")
    aliases = {
        "квм": "м2", "м²": "м2", "кубм": "м3", "м³": "м3",
        "человек": "чел", "человека": "чел", "чел": "чел",
        "эт": "эт", "этаж": "эт", "этажа": "эт",
    }
    return aliases.get(u, u)


def _representative_by_document(items: list[Finding]) -> tuple[dict[str, Finding], dict[str, list[float]]]:
    by_doc: dict[str, list[Finding]] = {}
    for item in items:
        if item.confidence < 0.72:
            continue
        by_doc.setdefault(item.document_type, []).append(item)

    representatives: dict[str, Finding] = {}
    ambiguous: dict[str, list[float]] = {}
    for doc_type, doc_items in by_doc.items():
        values = sorted({round(float(i.value), 6) for i in doc_items if i.value is not None})
        if len(values) == 1:
            representatives[doc_type] = max(doc_items, key=lambda x: x.confidence)
        elif len(values) > 1:
            ambiguous[doc_type] = values
    return representatives, ambiguous


def compare_findings(findings: list[Finding], tolerance: float = 0.01) -> list[dict]:
    groups: dict[tuple[str, str, str], list[Finding]] = {}
    for finding in findings:
        if finding.value is None or finding.object_hint == "Не определён":
            continue
        groups.setdefault(
            (finding.object_hint, finding.parameter_code, normalize_unit(finding.unit)), []
        ).append(finding)

    rows: list[dict] = []
    for (object_hint, code, unit), items in groups.items():
        representatives, ambiguous = _representative_by_document(items)
        if len(representatives) + len(ambiguous) < 2:
            continue

        if ambiguous:
            status = "ТРЕБУЕТ УТОЧНЕНИЯ"
            source_parts = []
            for doc, values in sorted(ambiguous.items()):
                source_parts.append(f"{doc}: найдено несколько значений {values}")
            for doc, item in sorted(representatives.items()):
                source_parts.append(f"{doc}, стр. {item.page}: {item.value_text}")
            rows.append({
                "object": object_hint,
                "parameter_code": code,
                "parameter_name": items[0].parameter_name,
                "unit": unit,
                "status": status,
                "min_value": "",
                "max_value": "",
                "documents": ", ".join(sorted(set(representatives) | set(ambiguous))),
                "sources": " | ".join(source_parts),
                "comment": "В одном из разделов найдено несколько значений. Автоматическое сравнение не выполнялось.",
            })
            continue

        if len(representatives) < 2:
            continue
        values = [float(item.value) for item in representatives.values() if item.value is not None]
        min_value, max_value = min(values), max(values)
        mismatch = not math.isclose(min_value, max_value, rel_tol=tolerance, abs_tol=tolerance)
        rows.append({
            "object": object_hint,
            "parameter_code": code,
            "parameter_name": items[0].parameter_name,
            "unit": unit,
            "status": "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ" if mismatch else "СОВПАДАЕТ",
            "min_value": min_value,
            "max_value": max_value,
            "documents": ", ".join(sorted(representatives)),
            "sources": " | ".join(
                f"{doc}, стр. {item.page}: {item.value_text}"
                for doc, item in sorted(representatives.items())
            ),
            "comment": (
                "Значения в разных разделах отличаются. Требуется подтвердить, что сравнивается один показатель."
                if mismatch else "Одинаковое значение подтверждено в нескольких разделах."
            ),
        })

    order = {"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ": 0, "ТРЕБУЕТ УТОЧНЕНИЯ": 1, "СОВПАДАЕТ": 2}
    rows.sort(key=lambda row: (order.get(row["status"], 9), row["object"], row["parameter_name"]))
    return rows


def analyze_uploaded(files: Iterable, config_dir: str | Path) -> tuple[list[dict], list[dict], list[dict]]:
    config_dir = Path(config_dir)
    parameters = load_json(config_dir / "parameters.json")
    document_types = load_json(config_dir / "document_types.json")
    objects = load_json(config_dir / "objects.json")
    documents = []
    all_findings: list[Finding] = []
    for uploaded in files:
        pages = read_pdf(uploaded.getvalue(), uploaded.name)
        first_text = "\n".join(text for _, text in pages[:3])
        doc_type = classify_document(uploaded.name, first_text, document_types)
        documents.append({"Файл": uploaded.name, "Тип документа": doc_type, "Страниц": len(pages)})
        all_findings.extend(extract_findings(uploaded.name, doc_type, pages, parameters, objects))
    return documents, [f.to_dict() for f in all_findings], compare_findings(all_findings)
