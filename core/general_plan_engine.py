from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

import fitz

POSITION_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){1,5}$")
CLASSIFIER_RE = re.compile(r"^\d{2}\.\d{2}\.\d{3}\.\d{3}$")
SERVICE_NAMES = {
    "номер на плане", "наименование", "примечание", "экспликация зданий и сооружений",
    "резервный номер", "площадка", "условные обозначения",
}


@dataclass
class GeneralPlanEntry:
    position: str
    name: str
    page: int
    in_explication: bool
    on_drawing: bool
    drawing_occurrences: int
    confidence: float
    extraction_method: str
    evidence: str

    def to_finding(self, document: str) -> dict[str, Any]:
        confirmations = []
        if self.in_explication:
            confirmations.append("экспликация генплана")
        if self.on_drawing:
            confirmations.append(f"поле чертежа ({self.drawing_occurrences})")
        return {
            "document": document,
            "document_type": "ПЗУ2",
            "page": self.page,
            "parameter_code": "OBJECT_CANDIDATE",
            "parameter_name": "Объект по генеральному плану",
            "value": 1.0,
            "value_text": self.name or f"Позиция {self.position}",
            "unit": "шт.",
            "context": self.evidence,
            "confidence": self.confidence,
            "object_hint": self.name or f"Позиция {self.position}",
            "match_method": self.extraction_method,
            "structural_zone": "Экспликация/поле генерального плана",
            "extraction_profile": "ПЗУ2: независимый реестр генерального плана",
            "genplan_position": self.position,
            "general_plan_explication": self.in_explication,
            "general_plan_field": self.on_drawing,
            "general_plan_occurrences": self.drawing_occurrences,
            "review_note": "; ".join(confirmations),
        }


def _clean_position(value: str) -> str:
    value = re.sub(r"\s+", "", str(value or "").strip())
    if POSITION_RE.fullmatch(value) and not CLASSIFIER_RE.fullmatch(value):
        return value
    return ""


def _clean_name(value: str) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split()).strip(" .;:-")
    text = re.sub(r"^\d{1,3}(?:\.\d{1,3}){1,5}\s*", "", text).strip(" .;:-")
    return text


def _is_plausible_name(value: str) -> bool:
    name = _clean_name(value)
    if len(name) < 3 or name.lower() in SERVICE_NAMES:
        return False
    if re.fullmatch(r"[\d.,+\-–— ]+", name):
        return False
    return any(ch.isalpha() for ch in name)


def _block_position_and_name(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if not lines:
        return "", ""
    first = _clean_position(lines[0])
    if first:
        return first, _clean_name(" ".join(lines[1:]))
    inline = re.match(r"^(\d{1,3}(?:\.\d{1,3}){1,5})\s+(.+)$", " ".join(lines))
    if inline:
        pos = _clean_position(inline.group(1))
        return pos, _clean_name(inline.group(2))
    return "", ""


def _page_has_explication(page: fitz.Page) -> bool:
    text = page.get_text("text").lower().replace("ё", "е")
    return "экспликация зданий и сооружений" in text or (
        "номер" in text and "на плане" in text and "наименование" in text
    )


def _extract_explication_blocks(page: fitz.Page) -> tuple[dict[str, str], list[dict[str, Any]]]:
    raw_blocks = []
    for raw in page.get_text("blocks"):
        x0, y0, x1, y1, text = raw[:5]
        clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if clean:
            raw_blocks.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "text": clean})

    header = next((b for b in raw_blocks if "экспликация зданий и сооружений" in b["text"].lower()), None)
    if header and page.rotation in {90, 270}:
        # На повернутых листах строки экспликации идут параллельными вертикальными
        # блоками слева от заголовка. Ограничение области исключает подписи на плане.
        blocks = [b for b in raw_blocks
                  if header["x0"] - 1250 <= b["x0"] <= header["x1"] + 40
                  and header["y0"] - 180 <= b["y0"] <= header["y1"] + 220]
    elif header:
        blocks = [b for b in raw_blocks
                  if header["x0"] - 100 <= b["x0"] <= header["x1"] + 1800
                  and header["y0"] - 40 <= b["y0"] <= header["y1"] + 1200]
    else:
        blocks = raw_blocks

    direct: dict[str, str] = {}
    standalone_positions: list[dict[str, Any]] = []
    name_only: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []

    for block in blocks:
        position, name = _block_position_and_name(block["text"])
        if position and _is_plausible_name(name):
            direct[position] = name
            audit.append({"page": page.number + 1, "position": position, "name": name,
                          "decision": "принято", "method": "единый блок экспликации"})
        elif position and not name:
            standalone_positions.append({**block, "position": position})
        elif _is_plausible_name(block["text"]):
            name_only.append({**block, "name": _clean_name(block["text"])})

    # В повернутых листах позиция и наименование иногда выгружаются двумя соседними блоками.
    used_names: set[int] = set()
    for pos_block in standalone_positions:
        candidates: list[tuple[float, int, dict[str, Any]]] = []
        for idx, name_block in enumerate(name_only):
            if idx in used_names:
                continue
            dx = abs(name_block["x0"] - pos_block["x0"])
            dy = abs(name_block["y0"] - pos_block["y0"])
            if page.rotation in {90, 270}:
                # Одна строка повернутой таблицы имеет почти одинаковую X-координату.
                score = dx + 0.02 * dy
                eligible = dx <= 26 and dy <= 420
            else:
                score = dy + 0.02 * dx
                eligible = dy <= 18 and dx <= 900
            if eligible:
                candidates.append((score, idx, name_block))
        candidates.sort(key=lambda item: item[0])
        if candidates:
            _, idx, match = candidates[0]
            name = match["name"]
            if _is_plausible_name(name):
                direct[pos_block["position"]] = name
                used_names.add(idx)
                audit.append({"page": page.number + 1, "position": pos_block["position"], "name": name,
                              "decision": "принято", "method": "связаны соседние блоки экспликации"})
        else:
            audit.append({"page": page.number + 1, "position": pos_block["position"], "name": "",
                          "decision": "требует проверки", "method": "позиция без наименования"})
    return direct, audit


def _drawing_positions(page: fitz.Page) -> dict[str, int]:
    result: dict[str, int] = {}
    for raw in page.get_text("blocks"):
        text = " ".join(str(raw[4]).split())
        pos = _clean_position(text)
        if pos:
            result[pos] = result.get(pos, 0) + 1
    return result


class GeneralPlanRegisterEngine:
    """Извлекает независимый реестр из экспликации и позиционных обозначений ПЗУ2.

    На первом этапе движок анализирует текстовый/векторный слой PDF. Он не пытается
    распознавать геометрию контуров, поэтому отсутствие позиции в поле чертежа имеет
    диагностический, а не окончательный статус.
    """

    def extract_pdf(self, data: bytes, filename: str) -> tuple[list[GeneralPlanEntry], list[dict[str, Any]]]:
        doc = fitz.open(stream=data, filetype="pdf")
        explication: dict[str, tuple[str, int]] = {}
        field_counts: dict[str, int] = {}
        field_pages: dict[str, set[int]] = {}
        audit: list[dict[str, Any]] = []

        for page in doc:
            positions = _drawing_positions(page)
            for position, count in positions.items():
                field_counts[position] = field_counts.get(position, 0) + count
                field_pages.setdefault(position, set()).add(page.number + 1)
            if _page_has_explication(page):
                rows, row_audit = _extract_explication_blocks(page)
                audit.extend(row_audit)
                for position, name in rows.items():
                    current = explication.get(position)
                    if not current or len(name) > len(current[0]):
                        explication[position] = (name, page.number + 1)

        # На текущем этапе официальный независимый реестр строится по экспликации.
        # Позиции поля чертежа используются для подтверждения, но не создают объект без
        # наименования: это защищает от размеров, отметок и координат.
        all_positions = set(explication)
        entries: list[GeneralPlanEntry] = []
        for position in sorted(all_positions, key=lambda p: tuple(int(x) for x in p.split("."))):
            name, exp_page = explication.get(position, ("", 0))
            occurrences = field_counts.get(position, 0)
            # Одно вхождение может быть строкой экспликации. Два и более дают более
            # устойчивое подтверждение присутствия обозначения на поле чертежа.
            on_drawing = occurrences >= 2 if position in explication else occurrences >= 1
            page_no = exp_page or min(field_pages.get(position, {1}))
            confidence = 0.98 if name and on_drawing else 0.93 if name else 0.62
            method = "экспликация + позиция на поле чертежа" if name and on_drawing else (
                "экспликация зданий и сооружений" if name else "позиционное обозначение на поле чертежа"
            )
            evidence = f"ПЗУ2, стр. {page_no}; экспликация={'да' if name else 'нет'}; вхождений позиции={occurrences}"
            entries.append(GeneralPlanEntry(
                position=position, name=name, page=page_no,
                in_explication=bool(name), on_drawing=on_drawing,
                drawing_occurrences=occurrences, confidence=confidence,
                extraction_method=method, evidence=evidence,
            ))
        return entries, audit

    def extract_uploaded(self, files: Iterable[Any], document_types: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        findings: list[dict[str, Any]] = []
        audit: list[dict[str, Any]] = []
        for uploaded in files:
            if document_types.get(uploaded.name) != "ПЗУ2":
                continue
            try:
                entries, file_audit = self.extract_pdf(uploaded.getvalue(), uploaded.name)
            except Exception as exc:
                audit.append({"document": uploaded.name, "decision": "ошибка", "reason": str(exc)})
                continue
            findings.extend(entry.to_finding(uploaded.name) for entry in entries)
            for row in file_audit:
                row["document"] = uploaded.name
            audit.extend(file_audit)
        return findings, audit
