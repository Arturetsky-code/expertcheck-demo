from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable

from .normalization import normalize_text


SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "ПЗ": ("пз", "пояснительная записка", "№1_пз"),
    "ПЗУ": ("пзу", "пзу1", "пзу2", "генеральный план", "генплан", "схема планировочной"),
    "АР": ("ар", "ар1", "ар2", "архитектурные решения"),
    "КР": ("кр", "кр1", "кр2", "кж", "км", "конструктивные решения"),
    "ТХ": ("тх", "тх1", "тх2", "технологические решения"),
    "ИОС1": ("иос1", "электроснабжение", "электроснабжения"),
    "ИОС2": ("иос2", "водоснабжение", "водоотведение", "водоснабжения", "водоотведения"),
    "ИОС3": ("иос3", "канализация"),
    "ИОС4": ("иос4", "отопление", "вентиляция"),
    "ИОС5": ("иос5", "связь", "автоматизация", "слаботочные"),
    "ИОС6": ("иос6", "газоснабжение"),
    "ИОС7": ("иос7",),
    "ПОС": ("пос", "организация строительства"),
    "ПБ": ("пб", "пожарная безопасность"),
    "ООС": ("оос", "моос", "охрана окружающей среды"),
    "ГТС": ("гтс", "гидротехнические сооружения"),
}


def _compact(value: Any) -> str:
    return re.sub(r"[^a-zа-яё0-9]", "", normalize_text(value).lower())


def canonical_section(value: Any) -> str:
    """Return a stable section family without guessing from generic words."""
    low = normalize_text(value).lower()
    compact = _compact(value)
    if not low:
        return ""
    for code in ("ИОС1", "ИОС2", "ИОС3", "ИОС4", "ИОС5", "ИОС6", "ИОС7", "ПЗУ", "АР", "КР", "ТХ", "ПОС", "ПБ", "ООС", "ГТС", "ПЗ"):
        code_compact = _compact(code)
        if compact == code_compact or compact.startswith(code_compact):
            return code
    words = set(re.findall(r"[a-zа-яё0-9]+", low))
    for code, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            norm = normalize_text(alias).lower()
            if len(norm) <= 3:
                if norm in words:
                    return code
            elif norm in low:
                return code
    return ""


def section_matches(actual: Any, expected: Iterable[Any] | None) -> bool:
    expected_codes = {canonical_section(x) for x in (expected or []) if canonical_section(x)}
    if not expected_codes:
        return True
    actual_code = canonical_section(actual)
    if not actual_code:
        return False
    if actual_code in expected_codes:
        return True
    # A generic IOS contract may intentionally accept any IOS subsection.
    return "ИОС" in {normalize_text(x).upper() for x in (expected or [])} and actual_code.startswith("ИОС")


def source_section(record: dict[str, Any]) -> str:
    explicit = record.get("section") or record.get("document_type") or record.get("section_family")
    return canonical_section(explicit) or canonical_section(record.get("document"))


def is_assignment_source(record: dict[str, Any] | str) -> bool:
    """Identify requirement-source documents that cannot prove their own fulfilment."""
    if isinstance(record, dict):
        document = str(record.get("document") or record.get("filename") or "")
        document_type = normalize_text(record.get("document_type") or record.get("section") or "").upper()
    else:
        document = str(record or "")
        document_type = ""
    low = normalize_text(document).lower().replace("ё", "е")
    return document_type in {"ЗАДАНИЕ", "ТЗ", "ASSIGNMENT"} or any(
        marker in low
        for marker in ("задание на проектирование", "техническое задание", "техзадание")
    )


def _chunks(text: str, *, limit: int = 1500, overlap: int = 220) -> list[str]:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if not clean:
        return []
    if len(clean) <= limit:
        return [clean]
    sentences = [x.strip() for x in re.split(r"(?<=[.!?;])\s+", clean) if x.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > limit:
            chunks.append(current)
            tail = current[-overlap:].lstrip()
            current = (tail + " " + sentence).strip()
        else:
            current = (current + " " + sentence).strip()
    if current:
        chunks.append(current)
    return chunks


def page_evidence_records(page_corpus: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create source-locked passages from the real PDF page corpus.

    These passages are retrieval material, not verified engineering facts.  A
    typed checker must still qualify a passage before it can close a check.
    """
    records: list[dict[str, Any]] = []
    for page in page_corpus or []:
        document = str(page.get("document") or "").strip()
        page_no = page.get("page") or ""
        section = canonical_section(page.get("document_type")) or canonical_section(document)
        if not document or not section:
            continue
        for index, chunk in enumerate(_chunks(str(page.get("text") or "")), 1):
            digest = hashlib.sha1(f"{document}|{page_no}|{index}|{chunk[:160]}".encode("utf-8", "ignore")).hexdigest()[:14].upper()
            records.append({
                "evidence_id": f"PG-{digest}",
                "kind": "PAGE_PASSAGE",
                "document": document,
                "document_type": section,
                "section": section,
                "page": page_no,
                "passage_index": index,
                "text": chunk,
                "owner": "",
                "metric": "",
                "value": "",
                "unit": "",
                "trust": "SOURCE_PASSAGE",
                "source_locator": f"{document}, стр. {page_no}",
                "physical_trace_level": "PAGE_TRACE",
            })
    return records
