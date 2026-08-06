from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

import fitz

from .position_rules import normalize_genplan_position

# Позиции генплана бывают как целыми (1, 2, 5), так и составными (3.1, 4.13).
# Координаты, пикетаж и длинные числовые значения не считаются позициями.
POSITION_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){0,5}$")
CLASSIFIER_RE = re.compile(r"^\d{2}\.\d{2}\.\d{3}\.\d{3}$")
CHAINAGE_RE = re.compile(r"\bПК\s*\d+(?:\+\d+(?:[.,]\d+)?)?", re.I)

EXPLICATION_TOKENS = (
    "экспликация зданий", "экспликация сооружений", "экспликация объектов",
    "экспликация площадок", "экспликация производственных площадок",
    "перечень зданий и сооружений", "перечень проектируемых объектов",
)
COLUMN_TOKENS = ("номер на плане", "наименование", "примечание")
SERVICE_NAMES = {
    "номер на плане", "номер", "наименование", "наименование объекта", "примечание",
    "экспликация зданий и сооружений", "экспликация площадок",
    "экспликация производственных площадок месторождения", "резервный номер",
    "площадка", "условные обозначения", "проект", "проект.", "сущ", "сущ.",
    "перспект", "перспект.", "стр", "стр.",
}
ROW_NOTES = {"проект", "проект.", "сущ", "сущ.", "существ.", "перспект", "перспект.", "стр", "стр."}

# Консервативный словарь для подписей/выносок непосредственно на поле генплана.
# Такие записи имеют меньший приоритет, чем экспликация, но могут формировать
# кандидата объекта, если экспликация отсутствует (характерно для линейных объектов).
PLAN_OBJECT_TOKENS = (
    "трубопровод", "газопровод", "нефтепровод", "водовод", "пульпопровод",
    "узел запорной арматуры", "площадка узла", "насосная станция", "компрессорная станция",
    "резервуар", "емкость", "ёмкость", "здание", "сооружение", "склад", "ктп", "дэс",
    "автодорога", "автомобильная дорога", "канал", "пруд", "карьер", "отвал",
    "площадка очистных", "площадка склада", "промплощадка", "факельная установка",
    "установка подготовки", "сепаратор", "скважина", "куст скважин",
)


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
    named_plan_label: bool = False

    def to_finding(self, document: str) -> dict[str, Any]:
        confirmations = []
        if self.in_explication:
            confirmations.append("экспликация генплана")
        if self.on_drawing:
            confirmations.append(f"поле чертежа ({self.drawing_occurrences})")
        if self.named_plan_label:
            confirmations.append("инженерная выноска на поле генплана")
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
            "general_plan_named_label": self.named_plan_label,
            "general_plan_occurrences": self.drawing_occurrences,
            "review_note": "; ".join(confirmations),
        }


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").replace("ё", "е").replace("\u00ad", "").split()).lower()


def _clean_position(value: str) -> str:
    return normalize_genplan_position(value, allow_integer=True)


def _clean_name(value: str) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split()).strip(" .;:-")
    text = re.sub(r"^\d{1,3}(?:\.\d{1,3}){0,5}\s+", "", text).strip(" .;:-")
    # Примечания из последней колонки не являются частью наименования.
    words = text.split()
    while words and words[-1].lower().strip(".;") in ROW_NOTES:
        words.pop()
    return " ".join(words).strip(" .;:-")


def _is_plausible_name(value: str) -> bool:
    name = _clean_name(value)
    low = _normalize_text(name)
    if len(name) < 3 or low in SERVICE_NAMES:
        return False
    if re.fullmatch(r"[\d.,+\-–— ]+", name):
        return False
    if name.lower().endswith((".pdf", ".xml", ".sig", ".zip")):
        return False
    return any(ch.isalpha() for ch in name)


def _records_from_lines(text: str) -> list[tuple[str, str]]:
    """Извлекает одну или несколько строк вида `позиция -> наименование` из блока.

    PyMuPDF может вернуть строку таблицы одним блоком, двумя соседними блоками либо
    объединить несколько ячеек. Парсер работает по строкам и не требует точки в позиции.
    """
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    records: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        pos = _clean_position(lines[i])
        if not pos:
            inline = re.match(r"^(\d{1,3}(?:\.\d{1,3}){0,5})\s+(.+)$", lines[i])
            if inline:
                pos = _clean_position(inline.group(1))
                name = _clean_name(inline.group(2))
                if pos and _is_plausible_name(name):
                    records.append((pos, name))
            i += 1
            continue

        name_lines: list[str] = []
        j = i + 1
        while j < len(lines):
            if _clean_position(lines[j]):
                break
            normalized = _normalize_text(lines[j]).strip(".;")
            if normalized not in ROW_NOTES and normalized not in SERVICE_NAMES:
                name_lines.append(lines[j])
            j += 1
        name = _clean_name(" ".join(name_lines))
        records.append((pos, name))
        i = max(j, i + 1)
    return records


def _block_position_and_name(text: str) -> tuple[str, str]:
    records = _records_from_lines(text)
    return records[0] if records else ("", "")


def _page_has_explication(page: fitz.Page, textpage: fitz.TextPage | None = None) -> bool:
    text = _normalize_text(page.get_text("text", textpage=textpage))
    if any(token in text for token in EXPLICATION_TOKENS):
        return True
    return all(token in text for token in COLUMN_TOKENS)


def _find_explication_header(raw_blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for block in raw_blocks:
        low = _normalize_text(block["text"])
        if any(token in low for token in EXPLICATION_TOKENS):
            return block
    return None


def _extract_explication_blocks(page: fitz.Page, textpage: fitz.TextPage | None = None) -> tuple[dict[str, str], list[dict[str, Any]]]:
    raw_blocks = []
    for raw in page.get_text("blocks", textpage=textpage):
        x0, y0, x1, y1, text = raw[:5]
        clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if clean:
            raw_blocks.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "text": clean})

    header = _find_explication_header(raw_blocks)
    if header and page.rotation in {90, 270}:
        # На повернутом листе строки таблицы идут слева от вертикального заголовка.
        blocks = [b for b in raw_blocks
                  if header["x0"] - 750 <= b["x0"] <= header["x0"] - 35
                  and header["y0"] - 190 <= b["y0"] <= header["y1"] + 90]
    elif header:
        # На альбомном листе строки расположены ниже заголовка в правой части листа.
        blocks = [b for b in raw_blocks
                  if header["x0"] - 220 <= b["x0"] <= page.rect.width - 20
                  and header["y1"] + 5 <= b["y0"] <= header["y1"] + 520]
    else:
        blocks = raw_blocks

    direct: dict[str, str] = {}
    standalone_positions: list[dict[str, Any]] = []
    name_only: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []

    for block in blocks:
        records = _records_from_lines(block["text"])
        if records:
            for position, name in records:
                if position and _is_plausible_name(name):
                    direct[position] = name
                    audit.append({"page": page.number + 1, "position": position, "name": name,
                                  "decision": "принято", "method": "строка экспликации"})
                elif position and not name:
                    standalone_positions.append({**block, "position": position})
        elif _is_plausible_name(block["text"]):
            name_only.append({**block, "name": _clean_name(block["text"])})

    # Позиция и наименование могут быть разнесены по соседним блокам.
    used_names: set[int] = set()
    for pos_block in standalone_positions:
        candidates: list[tuple[float, int, dict[str, Any]]] = []
        for idx, name_block in enumerate(name_only):
            if idx in used_names:
                continue
            dx = abs(name_block["x0"] - pos_block["x0"])
            dy = abs(name_block["y0"] - pos_block["y0"])
            if page.rotation in {90, 270}:
                score = dx + 0.02 * dy
                eligible = dx <= 30 and dy <= 520
            else:
                score = dy + 0.02 * dx
                eligible = dy <= 20 and dx <= 1100
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
                              "decision": "принято", "method": "связаны соседние ячейки экспликации"})
        else:
            audit.append({"page": page.number + 1, "position": pos_block["position"], "name": "",
                          "decision": "требует проверки", "method": "позиция без наименования"})
    return direct, audit


def _drawing_positions(page: fitz.Page, textpage: fitz.TextPage | None = None) -> dict[str, int]:
    result: dict[str, int] = {}
    for raw in page.get_text("blocks", textpage=textpage):
        text = " ".join(str(raw[4]).split())
        pos = _clean_position(text)
        if pos:
            result[pos] = result.get(pos, 0) + 1
    return result


def _is_engineering_plan_label(text: str) -> bool:
    low = _normalize_text(text)
    if len(low) < 6 or len(low) > 260:
        return False
    if any(ext in low for ext in (".pdf", ".sig", ".xml")):
        return False
    if any(token in low for token in ("условные обозначения", "система координат", "стадия лист", "разраб", "проверил", "граница ", "охранная зона")):
        return False
    return any(token in low for token in PLAN_OBJECT_TOKENS)


def _clean_plan_label(text: str) -> str:
    lines = [" ".join(line.split()) for line in str(text or "").splitlines() if line.strip()]
    # Убираем чистый пикетаж, служебные слова и начало/конец трассы; сохраняем тип/обозначение объекта.
    kept: list[str] = []
    for line in lines:
        low = _normalize_text(line)
        if re.fullmatch(r"ПК\s*\d+(?:\+\d+(?:[.,]\d+)?)?", line, re.I):
            continue
        if low in ROW_NOTES or low in SERVICE_NAMES:
            continue
        kept.append(line)
    text = " ".join(kept)
    text = re.sub(r"\bПК\s*\d+(?:\+\d+(?:[.,]\d+)?)?\b", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" .;:-")
    return _clean_name(text)


def _extract_named_plan_labels(page: fitz.Page, explication_names: set[str], textpage: fitz.TextPage | None = None) -> list[tuple[str, str]]:
    labels: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in page.get_text("blocks", textpage=textpage):
        text = str(raw[4] or "")
        if not _is_engineering_plan_label(text):
            continue
        name = _clean_plan_label(text)
        if not _is_plausible_name(name):
            continue
        if not any(token in _normalize_text(name) for token in PLAN_OBJECT_TOKENS):
            continue
        norm = _normalize_text(name)
        if norm in explication_names or norm in seen:
            continue
        # Для линейных выносок наличие пикетажа или номера узла — сильное подтверждение.
        evidence = "пикетаж/выноска" if CHAINAGE_RE.search(text) or "№" in text else "инженерная подпись"
        labels.append((name, evidence))
        seen.add(norm)
    return labels


def _extract_ocr_named_labels(text: str) -> list[tuple[str, str]]:
    """Консервативно извлекает только устойчивые подписи из OCR-слоя.

    OCR крупноформатных чертежей часто содержит шум. Поэтому здесь намеренно
    не пытаемся восстановить длинные трассовые подписи: в реестр попадают только
    короткие узнаваемые узлы и площадки, остальные строки остаются в аудите.
    """
    flat = " ".join(str(text or "").split())
    patterns = [
        r"Площадка\s+узл[ао]\s+запорн\w*\s+арма\w*\s*№\s*\d+",
        r"Узел\s+запорн\w*\s+арма\w*\s*№\s*\d+",
        r"Насосн\w*\s+станц\w*(?:\s*№\s*\d+)?",
        r"Компрессорн\w*\s+станц\w*(?:\s*№\s*\d+)?",
        r"Резервуар\w*(?:\s*№\s*\d+)?",
    ]
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, flat, flags=re.I):
            name = _clean_name(match.group(0))
            norm = _normalize_text(name)
            if norm and norm not in seen:
                result.append((name, "OCR: устойчивая инженерная подпись"))
                seen.add(norm)
    return result


def _looks_like_general_plan(page: fitz.Page, textpage: fitz.TextPage | None = None) -> bool:
    text = _normalize_text(page.get_text("text", textpage=textpage))
    return (
        _page_has_explication(page, textpage)
        or "генеральный план" in text
        or "ситуационный план" in text
        or ("план" in text and any(token in text for token in PLAN_OBJECT_TOKENS))
        or ("условные обозначения" in text and any(token in text for token in PLAN_OBJECT_TOKENS))
    )


def _page_textpage(page: fitz.Page) -> tuple[fitz.TextPage | None, str]:
    """Возвращает OCR-слой только для почти пустых растровых листов.

    OCR является опциональным: если Tesseract недоступен в окружении, анализ
    продолжается без падения, а аудит фиксирует ограничение.
    """
    if len(page.get_text("words")) >= 20:
        return None, "векторный текст"
    try:
        return page.get_textpage_ocr(flags=0, language="rus+eng", dpi=120, full=True), "OCR rus+eng"
    except Exception as exc:
        return None, f"OCR недоступен: {exc}"


class GeneralPlanRegisterEngine:
    """General Plan Intelligence Alpha 1.

    Анализирует текстовый/векторный слой PDF и строит независимый реестр по:
    1) экспликациям площадок, зданий, сооружений и объектов;
    2) позиционным обозначениям на поле листа;
    3) консервативно отобранным инженерным выноскам линейных объектов.

    Геометрическая интерпретация контуров и OCR сканов пока не выполняются. Поэтому
    записи без экспликации имеют статус кандидатов и меньшую уверенность.
    """

    def extract_pdf(self, data: bytes, filename: str) -> tuple[list[GeneralPlanEntry], list[dict[str, Any]]]:
        doc = fitz.open(stream=data, filetype="pdf")
        explication: dict[str, tuple[str, int]] = {}
        field_counts: dict[str, int] = {}
        field_pages: dict[str, set[int]] = {}
        named_labels: dict[str, tuple[str, int]] = {}
        audit: list[dict[str, Any]] = []

        for page in doc:
            textpage, text_method = _page_textpage(page)
            if text_method.startswith("OCR недоступен"):
                audit.append({"page": page.number + 1, "position": "", "name": "",
                              "decision": "ограничение", "method": text_method})
            elif text_method.startswith("OCR"):
                audit.append({"page": page.number + 1, "position": "", "name": "",
                              "decision": "OCR", "method": text_method})
            positions = _drawing_positions(page, textpage)
            for position, count in positions.items():
                field_counts[position] = field_counts.get(position, 0) + count
                field_pages.setdefault(position, set()).add(page.number + 1)
            page_rows: dict[str, str] = {}
            if _page_has_explication(page, textpage):
                page_rows, row_audit = _extract_explication_blocks(page, textpage)
                audit.extend(row_audit)
                for position, name in page_rows.items():
                    current = explication.get(position)
                    if not current or len(name) > len(current[0]):
                        explication[position] = (name, page.number + 1)
            if _looks_like_general_plan(page, textpage):
                exp_names = {_normalize_text(name) for name in page_rows.values()}
                if text_method.startswith("OCR"):
                    labels = _extract_ocr_named_labels(page.get_text("text", textpage=textpage))
                else:
                    labels = _extract_named_plan_labels(page, exp_names, textpage)
                for name, evidence in labels:
                    norm = _normalize_text(name)
                    current = named_labels.get(norm)
                    if not current or len(name) > len(current[0]):
                        named_labels[norm] = (name, page.number + 1)
                        audit.append({"page": page.number + 1, "position": "", "name": name,
                                      "decision": "кандидат", "method": f"выноска на поле генплана: {evidence}"})

        entries: list[GeneralPlanEntry] = []
        for position in sorted(explication, key=lambda p: tuple(int(x) for x in p.split("."))):
            name, exp_page = explication[position]
            occurrences = field_counts.get(position, 0)
            # Одно вхождение обычно находится в экспликации, второе — на поле чертежа.
            on_drawing = occurrences >= 2
            confidence = 0.99 if on_drawing else 0.96
            method = "экспликация + позиция на поле чертежа" if on_drawing else "экспликация генерального плана"
            evidence = f"ПЗУ2, стр. {exp_page}; экспликация=да; вхождений позиции={occurrences}"
            entries.append(GeneralPlanEntry(
                position=position, name=name, page=exp_page,
                in_explication=True, on_drawing=on_drawing,
                drawing_occurrences=occurrences, confidence=confidence,
                extraction_method=method, evidence=evidence,
            ))

        # Подписи поля не дублируют объекты экспликации по нормализованному наименованию.
        exp_names = {_normalize_text(item.name) for item in entries}
        for norm, (name, page_no) in sorted(named_labels.items()):
            if norm in exp_names:
                continue
            entries.append(GeneralPlanEntry(
                position="", name=name, page=page_no,
                in_explication=False, on_drawing=True, drawing_occurrences=1,
                confidence=0.84, extraction_method="инженерная выноска на поле генплана",
                evidence=f"ПЗУ2, стр. {page_no}; наименование обнаружено в выноске/подписи",
                named_plan_label=True,
            ))
        doc.close()
        return entries, audit

    def extract_uploaded(self, files: Iterable[Any], document_types: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        findings: list[dict[str, Any]] = []
        audit: list[dict[str, Any]] = []
        for uploaded in files:
            declared = document_types.get(uploaded.name, "")
            # Для файлов с нейтральным именем выполняется безопасная содержательная проверка.
            should_try = declared == "ПЗУ2"
            if not should_try:
                try:
                    probe = fitz.open(stream=uploaded.getvalue(), filetype="pdf")
                    should_try = any(_looks_like_general_plan(page) for page in list(probe)[:3])
                    probe.close()
                except Exception:
                    should_try = False
            if not should_try:
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
