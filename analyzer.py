from __future__ import annotations

import io
import json
import math
import re
from dataclasses import dataclass, asdict
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

    def to_dict(self) -> dict:
        return asdict(self)


def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("­", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_number(raw: str) -> float | None:
    cleaned = raw.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def read_pdf(file_obj: BinaryIO | bytes, filename: str) -> list[tuple[int, str]]:
    data = file_obj if isinstance(file_obj, bytes) else file_obj.read()
    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        pages.append((i + 1, normalize_text(page.get_text("text"))))
    return pages


def classify_document(filename: str, first_pages_text: str, document_types: list[dict]) -> str:
    haystack = f"{filename}\n{first_pages_text}".lower().replace("ё", "е")
    # Уточнение части по имени/шифру имеет приоритет.
    for item in document_types:
        code = item["code"]
        exact_tokens = [code.lower(), code.lower().replace("у", "у")]
        if any(token in haystack for token in exact_tokens):
            return code
    scores: list[tuple[int, str]] = []
    for item in document_types:
        score = sum(1 for p in item["patterns"] if p.lower().replace("ё", "е") in haystack)
        scores.append((score, item["code"]))
    scores.sort(reverse=True)
    return scores[0][1] if scores and scores[0][0] else "НЕОПРЕДЕЛЕН"


def _context(text: str, start: int, end: int, window: int = 180) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    fragment = text[left:right].replace("\n", " ")
    return re.sub(r"\s+", " ", fragment).strip()


def detect_object(context: str, objects: list[dict]) -> str:
    low = context.lower().replace("ё", "е")
    hits = []
    for obj in objects:
        for alias in obj["aliases"]:
            pos = low.rfind(alias.lower().replace("ё", "е"))
            if pos >= 0:
                hits.append((pos, len(alias), obj["canonical"]))
    if not hits:
        return "Не определён"
    hits.sort(reverse=True)
    return hits[0][2]


def extract_findings(
    filename: str,
    document_type: str,
    pages: list[tuple[int, str]],
    parameters: list[dict],
    objects: list[dict],
) -> list[Finding]:
    findings: list[Finding] = []
    for page_no, text in pages:
        low = text.lower().replace("ё", "е")
        for param in parameters:
            for keyword in param["keywords"]:
                key = keyword.lower().replace("ё", "е")
                for km in re.finditer(re.escape(key), low):
                    search_start = km.start()
                    search_end = min(len(text), km.end() + 260)
                    segment = text[search_start:search_end]
                    pattern = param.get("value_pattern")
                    if pattern:
                        vm = re.search(pattern, segment, flags=re.I)
                        if not vm:
                            continue
                        raw_value = vm.group("value")
                        raw_unit = vm.groupdict().get("unit")
                        value = normalize_number(raw_value)
                        value_text = vm.group(0)
                        end = search_start + vm.end()
                        confidence = 0.93 if vm.start() < 120 else 0.78
                    else:
                        value = None
                        raw_unit = None
                        value_text = keyword
                        end = km.end()
                        confidence = 0.85
                    ctx = _context(text, km.start(), end)
                    findings.append(
                        Finding(
                            document=filename,
                            document_type=document_type,
                            page=page_no,
                            parameter_code=param["code"],
                            parameter_name=param["name"],
                            value=value,
                            value_text=value_text,
                            unit=raw_unit or param.get("unit"),
                            context=ctx,
                            confidence=confidence,
                            object_hint=detect_object(ctx, objects),
                        )
                    )
    # Удаление точных дублей, возникающих из повторяющихся колонтитулов.
    unique = {}
    for item in findings:
        key = (
            item.document,
            item.page,
            item.parameter_code,
            item.value,
            item.unit,
            item.context[:120],
        )
        unique[key] = item
    return list(unique.values())


def normalize_unit(unit: str | None) -> str:
    if not unit:
        return ""
    u = unit.lower().replace(" ", "").replace("²", "2").replace("³", "3").replace(".", "")
    aliases = {"квм": "м2", "кубм": "м3", "человек": "чел", "чел": "чел"}
    return aliases.get(u, u)


def compare_findings(findings: list[Finding], tolerance: float = 0.01) -> list[dict]:
    groups: dict[tuple[str, str], list[Finding]] = {}
    for f in findings:
        if f.value is None:
            continue
        if f.object_hint == "Не определён":
            continue
        groups.setdefault((f.object_hint, f.parameter_code, normalize_unit(f.unit)), []).append(f)

    rows: list[dict] = []
    for (object_hint, code, unit), items in groups.items():
        docs = {i.document_type for i in items}
        values = sorted({round(i.value or 0, 6) for i in items})
        if len(docs) < 2:
            continue
        min_value, max_value = min(values), max(values)
        mismatch = not math.isclose(min_value, max_value, rel_tol=tolerance, abs_tol=tolerance)
        rows.append(
            {
                "object": object_hint,
                "parameter_code": code,
                "parameter_name": items[0].parameter_name,
                "unit": unit,
                "status": "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ" if mismatch else "СОВПАДАЕТ",
                "min_value": min_value,
                "max_value": max_value,
                "documents": ", ".join(sorted(docs)),
                "sources": " | ".join(
                    f"{i.document_type}, стр. {i.page}: {i.value_text}" for i in items[:12]
                ),
                "comment": (
                    "Требуется проверить, относятся ли значения к одному объекту и одному виду площади/мощности."
                    if mismatch
                    else "Найдены одинаковые значения в нескольких разделах."
                ),
            }
        )
    rows.sort(key=lambda x: (x["status"] != "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ", x["parameter_name"]))
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
    finding_rows = [f.to_dict() for f in all_findings]
    comparison_rows = compare_findings(all_findings)
    return documents, finding_rows, comparison_rows
