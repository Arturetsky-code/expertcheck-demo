from __future__ import annotations

import re
from typing import Any

from .normalization import normalize_text
from .object_semantics import is_service_object_candidate

_POSITION = re.compile(r"^\s*(?P<pos>\d{1,3}(?:\.\d{1,3}){1,5})\s*(?:[-–—:]\s*)?(?P<name>.*)$")
_ORDINAL = re.compile(r"^\s*(?P<num>\d{1,3})[.)]?\s*$")
_CLASSIFIER = re.compile(r"^\d{2}\.\d{2}\.\d{3}\.\d{3}$")

_OBJECT_TABLE_SIGNALS = (
    "состав сложного объекта", "сведения о составе объекта", "объекты входящие в состав",
    "объекты, входящие в состав", "перечень объектов", "состав проектируемого объекта",
    "экспликация зданий и сооружений", "экспликация объектов", "позиция по генплану",
    "наименование объекта капитального строительства", "наименование здания и сооружения",
)
_DOCUMENT_TABLE_SIGNALS = (
    "состав проектной документации", "перечень разделов проектной документации",
    "ведомость документов", "ведомость основного комплекта", "содержание тома",
    "перечень файлов", "наименование документа", "обозначение документа",
)
_HEADER_WORDS = (
    "поз.", "позиция", "наименование", "количество", "примечание", "единица измерения",
    "технико-экономические показатели", "номер по генплану", "№ п/п", "значение",
)
_STOP_PREFIXES = (
    "раздел ", "подраздел ", "часть ", "том ", "лист ", "примечание", "условные обозначения",
    "технико-экономические показатели", "показатель", "единица измерения", "значение",
)
_UNIT_LINE = re.compile(r"^(?:шт\.?|ед\.?|м|м2|м²|м3|м³|квт|ква|мвт|мпа|кпа|бар|т/ч|т/сут|т/год|м3/ч|м³/ч|л/с|чел\.?|эт\.?)$", re.I)
_NUMBER_LINE = re.compile(r"^[()\-+]?\d[\d\s]*(?:[.,]\d+)?(?:\s*(?:шт\.?|м|м2|м²|м3|м³|квт|ква|мвт|мпа|кпа|бар|т/ч|т/сут|т/год|м3/ч|м³/ч|л/с|чел\.?|эт\.?))?$", re.I)


def _page_kind(text: str) -> str:
    low = normalize_text(text)
    doc_score = sum(token in low for token in _DOCUMENT_TABLE_SIGNALS)
    obj_score = sum(token in low for token in _OBJECT_TABLE_SIGNALS)
    if doc_score and doc_score >= obj_score:
        return "document_register"
    if obj_score:
        return "object_register"
    return "unknown"


def _clean_name(parts: list[str]) -> str:
    value = " ".join(x.strip(" .;:–—-") for x in parts if x.strip())
    value = re.sub(r"\s+", " ", value).strip()
    return value[:240]


def _valid_name(name: str, document: str, context: str) -> bool:
    low = normalize_text(name)
    if len(name) < 3 or len(name) > 220:
        return False
    if low in _HEADER_WORDS or any(low.startswith(prefix) for prefix in _STOP_PREFIXES):
        return False
    if _UNIT_LINE.fullmatch(low) or _NUMBER_LINE.fullmatch(low):
        return False
    probe = {
        "value_text": name,
        "object_hint": name,
        "document": document,
        "context": context,
        "structural_zone": "Универсальный перечень объектов",
        "match_method": "Universal Registry Extractor",
    }
    service, _ = is_service_object_candidate(probe)
    return not service


def _collect_name(lines: list[str], start: int, document: str, context: str, max_lines: int = 5) -> str:
    parts: list[str] = []
    for raw in lines[start:start + max_lines]:
        line = raw.strip()
        if not line:
            continue
        m = _POSITION.match(line)
        if m and not _CLASSIFIER.fullmatch(m.group("pos")):
            break
        low = normalize_text(line)
        if low in _HEADER_WORDS or any(low.startswith(prefix) for prefix in _STOP_PREFIXES):
            if parts:
                break
            continue
        if _UNIT_LINE.fullmatch(low) or _NUMBER_LINE.fullmatch(low):
            if parts:
                break
            continue
        parts.append(line)
        candidate = _clean_name(parts)
        if len(candidate) >= 8 and _valid_name(candidate, document, context):
            # Usually one or two lines are enough; continue only if line ends as unfinished phrase.
            if not line.endswith((",", "-", "–", "—", "для", "и")):
                return candidate
    candidate = _clean_name(parts)
    return candidate if _valid_name(candidate, document, context) else ""


class UniversalRegistryExtractor:
    """Reads project-object registers without relying on an industry dictionary."""

    def extract_uploaded(self, files, document_types: dict[str, str], reader) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        findings: list[dict[str, Any]] = []
        audit: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for uploaded in files:
            filename = str(getattr(uploaded, "name", ""))
            doc_type = document_types.get(filename, "")
            if doc_type not in {"ПЗ", "ПЗУ1", "ПЗУ2", "АР1", "ТХ1", "ТХ2", "КР"}:
                continue
            try:
                pages = reader(uploaded.getvalue(), filename)
            except Exception as exc:
                audit.append({"document": filename, "decision": "error", "reason": str(exc)})
                continue
            for page_no, text in pages:
                kind = _page_kind(text)
                if kind != "object_register":
                    if kind == "document_register":
                        audit.append({"document": filename, "page": page_no, "decision": "skip", "reason": "таблица документов"})
                    continue
                lines = [x.strip() for x in text.splitlines() if x.strip()]
                page_context = normalize_text(text[:1800])
                for i, line in enumerate(lines):
                    match = _POSITION.match(line)
                    if match and not _CLASSIFIER.fullmatch(match.group("pos")):
                        position = match.group("pos")
                        tail = match.group("name").strip()
                        name = tail if _valid_name(tail, filename, page_context) else _collect_name(lines, i + 1, filename, page_context)
                        if not name:
                            continue
                        key = (filename, position, normalize_text(name))
                        if key in seen:
                            continue
                        seen.add(key)
                        findings.append(self._finding(filename, doc_type, page_no, position, name, 0.96))
                        audit.append({"document": filename, "page": page_no, "position": position, "name": name, "decision": "accepted", "reason": "позиция в объектной таблице"})
                        continue
                    if _ORDINAL.fullmatch(line) and any(token in page_context for token in ("№ п/п", "номер", "наименование объекта")):
                        name = _collect_name(lines, i + 1, filename, page_context)
                        if not name:
                            continue
                        key = (filename, "", normalize_text(name))
                        if key in seen:
                            continue
                        seen.add(key)
                        findings.append(self._finding(filename, doc_type, page_no, "", name, 0.82))
                        audit.append({"document": filename, "page": page_no, "position": "", "name": name, "decision": "candidate", "reason": "строка объектной таблицы без позиции"})
        return findings, audit

    @staticmethod
    def _finding(filename: str, doc_type: str, page: int, position: str, name: str, confidence: float) -> dict[str, Any]:
        return {
            "document": filename,
            "document_type": doc_type,
            "page": page,
            "parameter_code": "OBJECT_CANDIDATE",
            "parameter_name": "Объект проекта",
            "value": 1.0,
            "value_text": name,
            "unit": "шт.",
            "context": f"Объектная таблица: {position} {name}".strip(),
            "confidence": confidence,
            "object_hint": name,
            "match_method": "Universal Registry Extractor: структурная строка перечня объектов",
            "review_note": "Количество явно не указано; принято 1",
            "structural_zone": "Перечень объектов / экспликация объектов",
            "extraction_profile": "универсальный реестр объектов",
            "genplan_position": position,
            "record_kind": "project_object",
            "universal_registry_row": True,
        }
