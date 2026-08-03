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
    structural_zone: str = ""
    extraction_profile: str = "универсальный"
    genplan_position: str = ""

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



def _line_spans(text: str) -> list[tuple[int, int, str]]:
    """Возвращает строки страницы с абсолютными позициями в тексте."""
    spans: list[tuple[int, int, str]] = []
    pos = 0
    for line in text.splitlines(keepends=True):
        clean = line.strip()
        start = pos
        end = pos + len(line)
        if clean:
            spans.append((start, end, clean))
        pos = end
    return spans


def _canonical_from_text(value: str, objects: list[dict]) -> str | None:
    low = normalized_search_text(value)
    compact_low = re.sub(r"[^а-яa-z0-9]+", "", low)
    candidates: list[tuple[int, str]] = []
    for obj in objects:
        for alias in obj.get("aliases", []):
            a = normalized_search_text(alias)
            compact_alias = re.sub(r"[^а-яa-z0-9]+", "", a)
            direct = len(a) >= 4 and a in low
            compact = len(compact_alias) >= 6 and compact_alias in compact_low
            if direct or compact:
                candidates.append((len(compact_alias), obj["canonical"]))
    return max(candidates)[1] if candidates else None


def _page_section_object(text: str, document_type: str, objects: list[dict]) -> tuple[str, str]:
    """Определяет объект и структурную зону страницы по заголовкам раздела.

    Особенно полезно для АР1 и ТХ1: заголовок 1.14/1.5.1 обычно задаёт
    объект для последующего текста, даже если название не повторяется рядом с ТЭП.
    """
    lines = _line_spans(text)
    heading_patterns = []
    if document_type in {"АР1", "ТХ1"}:
        heading_patterns = [r"^\d+(?:\.\d+){1,3}\s+(.{3,160})$"]
    elif document_type == "ПЗУ1":
        heading_patterns = [r"^\d+(?:\.\d+)?\s+(.{3,160})$"]
    elif document_type == "ПЗ":
        heading_patterns = [r"^\d+(?:\.\d+)?\s+(.{3,160})$"]

    for _, _, line in lines:
        for pattern in heading_patterns:
            m = re.match(pattern, line)
            if not m:
                continue
            title = m.group(1).strip(" .")
            obj = _canonical_from_text(title, objects)
            if obj:
                return obj, title
    return "Не определён", ""


def _structural_zone(text: str, document_type: str) -> str:
    low = normalized_search_text(text)
    zones = {
        "ПЗ": [
            ("Состав сложного объекта", ["сведения о сложном объекте", "входящих в состав сложного объекта"]),
            ("Технико-экономические показатели", ["технико-экономические показатели"]),
            ("Проектная мощность", ["сведения о проектной мощности"]),
        ],
        "ПЗУ1": [
            ("ТЭП земельного участка", ["технико-экономические показатели земельного участка"]),
            ("Планировочная организация", ["планировочной организации земельного участка"]),
            ("Благоустройство", ["решений по благоустройству"]),
        ],
        "АР1": [
            ("Архитектурные характеристики", ["технико-экономические показатели", "общая площадь", "площадь застройки"]),
            ("Описание объекта", ["описание внешнего вида", "объемно-планировоч"]),
        ],
        "ТХ1": [
            ("Технологические показатели", ["производительность", "технологического процесса"]),
            ("Организация производства", ["организация производства"]),
            ("Персонал", ["численность работающих", "количество работающих"]),
        ],
    }
    for zone, tokens in zones.get(document_type, []):
        if any(token in low for token in tokens):
            return zone
    return "Основной текст"


def _profile_name(document_type: str) -> str:
    return {
        "ПЗ": "ПЗ: состав объекта и ТЭП",
        "ПЗУ1": "ПЗУ: экспликация и показатели участка",
        "ПЗУ2": "ПЗУ: графическая часть",
        "АР1": "АР: характеристики зданий",
        "АР2": "АР: графическая часть",
        "ТХ1": "ТХ: технологические показатели",
        "ТХ2": "ТХ: графическая часть",
    }.get(document_type, "универсальный")


def _document_parameter_allowed(param: dict, document_type: str, zone: str) -> bool:
    """Мягкий фильтр применимости характеристики к профилю раздела."""
    code = param.get("code")
    preferred = {
        "ПЗ": {"DOC_NAME", "AREA_BUILD", "AREA_TOTAL", "VOLUME_BUILD", "HEIGHT_BUILD", "CAPACITY", "RES_VOLUME", "POWER_KTP", "STAFF", "FLOORS"},
        "ПЗУ1": {"DOC_NAME", "AREA_BUILD"},
        "АР1": {"DOC_NAME", "AREA_BUILD", "AREA_TOTAL", "VOLUME_BUILD", "HEIGHT_BUILD", "FLOORS"},
        "ТХ1": {"DOC_NAME", "CAPACITY", "STAFF", "POWER_KTP", "POWER_INST", "POWER_CALC", "RES_VOLUME"},
    }
    if document_type not in preferred:
        return True
    # Не запрещаем идентификацию; остальные нетипичные параметры допускаем только
    # в явно релевантной структурной зоне, чтобы не терять редкие корректные значения.
    if code in preferred[document_type]:
        return True
    return zone not in {"Основной текст", ""}


def _line_oriented_match(text: str, keyword_start: int, param: dict) -> tuple[re.Match | None, str, int]:
    """Ищет значение сначала в текущей и следующих строках таблицы.

    PDF-таблицы часто извлекаются как три строки: показатель / единица / значение.
    Возвращает match, метод и абсолютное смещение начала сегмента.
    """
    spans = _line_spans(text)
    line_index = next((i for i, (s, e, _) in enumerate(spans) if s <= keyword_start < e), None)
    if line_index is not None:
        start = spans[line_index][0]
        end = spans[min(len(spans) - 1, line_index + 4)][1]
        segment = text[start:end]
        candidates = _value_candidates(segment, param)
        if candidates:
            return candidates[0][0], "структурная строка/таблица", start
    return None, "", 0


def _parameter_by_code(parameters: list[dict], code: str) -> dict | None:
    return next((p for p in parameters if p.get("code") == code), None)


def _extract_values_from_block(block: str, parameter: dict) -> list[tuple[float, str, str]]:
    result: list[tuple[float, str, str]] = []
    for match, _ in _value_candidates(block, parameter):
        raw = match.groupdict().get("value")
        if raw is None:
            continue
        value = normalize_number(raw)
        if value is None:
            continue
        result.append((value, match.groupdict().get("unit") or parameter.get("unit") or "", re.sub(r"\s+", " ", match.group(0)).strip()))
    return result




def _clean_object_name(lines: list[str]) -> str:
    name = " ".join(line.strip(" .;:-") for line in lines if line.strip())
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"\s*-\s*", "-", name)
    return name


def _extract_pz_object_registry(page_no: int, text: str, filename: str, objects: list[dict]) -> list[Finding]:
    """Извлекает полный реестр объектов из многостраничных таблиц ПЗ.

    В отличие от прежнего алгоритма, не требует наличия объекта в objects.json:
    позиция по генплану служит устойчивым идентификатором, а наименование
    собирается из следующих строк до начала адреса, кода классификатора или
    служебных граф таблицы. Благодаря этому учитываются все позиции таблицы,
    включая сооружения, отсутствующие в первоначальном словаре.
    """
    low = normalized_search_text(text)
    table_signals = (
        "позиция\nпо\nгенплану" in low
        or "позиция по генплану" in low
        or ("наименование объекта" in low and "генплан" in low)
        or ("наименование зданий" in low and "генплан" in low)
    )
    if not table_signals:
        return []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    pos_re = re.compile(r"^4\.\d+(?:\.\d+){0,2}$")
    class_re = re.compile(r"^\d{2}\.\d{2}\.\d{3}\.\d{3}(?:\s|$)")
    ordinal_re = re.compile(r"^\d{1,3}$")
    stop_prefixes = (
        "рф,", "забайкальский", "не принадлежит", "нормативная",
        "принадлежит", "уровень", "класс", "коэф", "назначение",
        "площадь застройки", "общая площадь", "строительный объем",
        "строительный объём", "производительность", "протяженность",
        "протяжённость", "объем", "объём", "напряжение", "высота",
    )
    header_tokens = {
        "позиция", "по", "генплану", "наименование объекта",
        "капитального", "строительства", "наименование зданий,",
        "сооружений и вид", "строительства",
    }

    result: list[Finding] = []
    for i, line in enumerate(lines):
        if not pos_re.match(line):
            continue
        position = line
        name_lines: list[str] = []
        for candidate in lines[i + 1:i + 9]:
            candidate_low = normalized_search_text(candidate)
            if pos_re.match(candidate) or class_re.match(candidate):
                break
            if ordinal_re.match(candidate):
                # Номер объекта может переноситься на следующую строку после знака №.
                if name_lines and name_lines[-1].rstrip().endswith("№"):
                    name_lines.append(candidate)
                    continue
                break
            if candidate_low.startswith(stop_prefixes):
                break
            if candidate_low in header_tokens:
                continue
            # Коды классификатора иногда начинаются в той же строке после имени.
            code_match = class_re.search(candidate)
            if code_match:
                before = candidate[:code_match.start()].strip()
                if before:
                    name_lines.append(before)
                break
            name_lines.append(candidate)
            if len(" ".join(name_lines)) > 180:
                break
        raw_name = _clean_object_name(name_lines)
        if not raw_name or len(raw_name) < 2:
            continue
        # Убираем случайно захваченные заголовки/служебные фразы.
        bad = normalized_search_text(raw_name)
        if any(token in bad for token in ["адрес объекта", "функциональное назначение", "технико-экономические показатели"]):
            continue
        canonical_match = _canonical_from_text(raw_name, objects)
        # Сохраняем различия между однотипными нумерованными объектами.
        # Иначе «Выгреб № 1» и «Выгреб № 2» схлопываются в один объект «Выгреб».
        has_instance_marker = bool(re.search(r"(?:№\s*\d+|\bV\s*=\s*\d)", raw_name, flags=re.I))
        canonical = raw_name if has_instance_marker else (canonical_match or raw_name)
        result.append(Finding(
            document=filename,
            document_type="ПЗ",
            page=page_no,
            parameter_code="OBJECT_ENTRY",
            parameter_name="Объект в составе проекта",
            value=None,
            value_text=raw_name,
            unit=None,
            context=f"Позиция {position}: {raw_name}",
            confidence=0.995,
            object_hint=canonical,
            match_method="реестр объектов ПЗ по позиции генплана",
            structural_zone="Состав сложного объекта",
            extraction_profile="ПЗ: полный реестр объектов",
            genplan_position=position,
        ))
    return result


def _extract_pz_complex_table(page_no: int, text: str, filename: str, parameters: list[dict], objects: list[dict]) -> list[Finding]:
    """Извлекает строки таблицы состава сложного объекта ПЗ.

    Каждая позиция по генплану задаёт отдельный блок, поэтому характеристики
    больше не связываются с соседним объектом по расстоянию.
    """
    low = normalized_search_text(text)
    if "позиция" not in low or not re.search(r"по\s+генплану", low) or "технико-экономические" not in low:
        return []
    markers = list(re.finditer(r"(?m)^(?P<pos>4\.\d+(?:\.\d+)?)\s*$", text))
    if not markers:
        return []
    result: list[Finding] = []
    wanted = ["AREA_BUILD", "AREA_TOTAL", "VOLUME_BUILD", "CAPACITY", "HEIGHT_BUILD", "RES_VOLUME"]
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        block = text[marker.start():end]
        head = block[:500]
        obj = _canonical_from_text(head, objects)
        if not obj:
            continue
        pos = marker.group("pos")
        for code in wanted:
            parameter = _parameter_by_code(parameters, code)
            if not parameter:
                continue
            for value, unit, value_text in _extract_values_from_block(block, parameter):
                start = text.find(value_text.split()[0], marker.start(), end)
                result.append(Finding(
                    document=filename,
                    document_type="ПЗ",
                    page=page_no,
                    parameter_code=code,
                    parameter_name=parameter["name"],
                    value=value,
                    value_text=value_text,
                    unit=unit,
                    context=re.sub(r"\s+", " ", block[:900]).strip(),
                    confidence=0.985,
                    object_hint=obj,
                    match_method="строка таблицы состава сложного объекта",
                    structural_zone="Состав сложного объекта",
                    extraction_profile="ПЗ: состав объекта и ТЭП",
                    genplan_position=pos,
                ))
    return result


def _extract_pzu_building_areas(page_no: int, text: str, filename: str, parameters: list[dict], objects: list[dict]) -> list[Finding]:
    """Извлекает площади объектов из таблицы ТЭП ПЗУ."""
    low = normalized_search_text(text)
    if "площадь застройки, всего" not in low or "технико-экономические показатели земельного участка" not in low:
        return []
    parameter = _parameter_by_code(parameters, "AREA_BUILD")
    if not parameter:
        return []
    result: list[Finding] = []
    normalized = normalize_text(text)
    for obj in objects:
        best: tuple[int, int, str] | None = None
        for alias in obj.get("aliases", []):
            for m in re.finditer(re.escape(normalized_search_text(alias)), normalized_search_text(normalized)):
                if best is None or len(alias) > len(best[2]):
                    best = (m.start(), m.end(), alias)
        if not best:
            continue
        segment = normalized[best[1]: min(len(normalized), best[1] + 120)]
        vm = re.search(r"(?:«|м\s*[2²])\s*(?P<value>\(?\d[\d \u00a0]*(?:[.,]\d+)?\)?)", segment, flags=re.I)
        if not vm:
            continue
        raw = vm.group("value").strip("()")
        value = normalize_number(raw)
        if value is None:
            continue
        # Подстроки насосной/резервуаров в скобках не считаем общей площадью объекта.
        if vm.group("value").startswith("("):
            continue
        context = _context(normalized, best[0], best[1] + vm.end(), window=80)
        result.append(Finding(
            document=filename,
            document_type="ПЗУ1",
            page=page_no,
            parameter_code="AREA_BUILD",
            parameter_name=parameter["name"],
            value=value,
            value_text=f"{best[2]} — {value:g} м²",
            unit="м²",
            context=context,
            confidence=0.97,
            object_hint=obj["canonical"],
            match_method="строка таблицы ТЭП ПЗУ",
            structural_zone="ТЭП земельного участка",
            extraction_profile="ПЗУ: экспликация и показатели участка",
        ))
    return result

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
        page_object, page_heading = _page_section_object(text, document_type, objects)
        zone = _structural_zone(text, document_type)
        profile = _profile_name(document_type)

        specialized: list[Finding] = []
        structured_metrics: list[Finding] = []
        if document_type == "ПЗ":
            specialized.extend(_extract_pz_object_registry(page_no, text, filename, objects))
            structured_metrics = _extract_pz_complex_table(page_no, text, filename, parameters, objects)
            specialized.extend(structured_metrics)
        elif document_type == "ПЗУ1":
            structured_metrics = _extract_pzu_building_areas(page_no, text, filename, parameters, objects)
            specialized.extend(structured_metrics)
        if specialized:
            findings.extend(specialized)

        for param in parameters:
            # На таблицах с уже извлечёнными ТЭП используем специализированный извлекатель,
            # но наличие реестровых записей OBJECT_ENTRY не блокирует обычный поиск характеристик.
            if structured_metrics and param.get("code") != "DOC_NAME":
                continue
            # Идентификационные признаки извлекаются один раз на документ.
            if param.get("once_per_document") and param["code"] in identity_added:
                continue
            if contents_page and not param.get("allow_contents", False):
                continue
            allowed_docs = param.get("document_types")
            if allowed_docs and document_type not in allowed_docs:
                continue
            if not _document_parameter_allowed(param, document_type, zone):
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
                        if object_hint == "Не определён" and page_object != "Не определён":
                            object_hint, object_conf = page_object, 0.82
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
                            structural_zone=zone if not page_heading else f"{zone}: {page_heading}",
                            extraction_profile=profile,
                        ))
                        identity_added.add(param["code"])
                        break

                    line_vm, line_method, line_offset = _line_oriented_match(text, km.start(), param)
                    if line_vm is not None:
                        vm, method, segment_offset = line_vm, line_method, line_offset
                    else:
                        segment_end = min(len(text), km.end() + param.get("search_window", 180))
                        segment = text[km.start():segment_end]
                        candidates = _value_candidates(segment, param)
                        if not candidates:
                            continue
                        vm, method = candidates[0]
                        segment_offset = km.start()
                    raw_value = vm.groupdict().get("value")
                    raw_unit = vm.groupdict().get("unit")
                    if raw_value is None:
                        continue
                    value = normalize_number(raw_value)
                    if value is None:
                        continue
                    absolute_end = segment_offset + vm.end()
                    absolute_value_start = segment_offset + vm.start()
                    object_hint, object_conf = detect_object(text, km.start(), absolute_end, objects)
                    if object_hint == "Не определён" and page_object != "Не определён":
                        object_hint, object_conf = page_object, 0.82

                    distance = max(0, absolute_value_start - km.start())
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
                        structural_zone=zone if not page_heading else f"{zone}: {page_heading}",
                        extraction_profile=profile,
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


def _quality_score(item: Finding) -> float:
    """Оценка пригодности найденного значения для автоматической сверки."""
    score = float(item.confidence)
    method_bonus = {
        "структурная строка/таблица": 0.08,
        "идентификационный признак": 0.03,
        "контекстный поиск": 0.0,
    }
    score += method_bonus.get(item.match_method, 0.0)
    if item.structural_zone and item.structural_zone != "Основной текст":
        score += 0.04
    if item.review_note:
        score -= 0.08
    if item.object_hint == "Не определён":
        score -= 0.20
    return max(0.0, min(1.0, score))


def _cluster_values(items: list[Finding], abs_tol: float, rel_tol: float) -> list[list[Finding]]:
    clusters: list[list[Finding]] = []
    for item in sorted(items, key=lambda x: float(x.value or 0)):
        placed = False
        for cluster in clusters:
            ref = float(cluster[0].value)
            if math.isclose(float(item.value), ref, abs_tol=abs_tol, rel_tol=rel_tol):
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])
    return clusters


def _representative_by_document(
    items: list[Finding],
    min_confidence: float,
    abs_tol: float,
    rel_tol: float,
) -> tuple[dict[str, Finding], dict[str, list[Finding]], dict[str, list[Finding]]]:
    """Выбирает одно подтверждённое значение на раздел.

    Возвращает: представители, неоднозначные разделы, отброшенные слабые находки.
    Низкоуверенные дубли не должны превращать корректный показатель в ложную
    неоднозначность.
    """
    by_doc: dict[str, list[Finding]] = {}
    rejected: dict[str, list[Finding]] = {}
    for item in items:
        if _quality_score(item) < min_confidence:
            rejected.setdefault(item.document_type, []).append(item)
            continue
        by_doc.setdefault(item.document_type, []).append(item)

    representatives: dict[str, Finding] = {}
    ambiguous: dict[str, list[Finding]] = {}
    for doc_type, doc_items in by_doc.items():
        clusters = _cluster_values(doc_items, abs_tol=abs_tol, rel_tol=rel_tol)
        clusters.sort(
            key=lambda group: (
                max(_quality_score(x) for x in group),
                len(group),
            ),
            reverse=True,
        )
        if not clusters:
            continue
        best = clusters[0]
        # Второй кластер считается конкурирующим только при сопоставимом качестве.
        if len(clusters) > 1:
            best_score = max(_quality_score(x) for x in best)
            second_score = max(_quality_score(x) for x in clusters[1])
            if second_score >= max(min_confidence, best_score - 0.06):
                ambiguous[doc_type] = [x for cluster in clusters for x in cluster]
                continue
        representatives[doc_type] = max(best, key=_quality_score)
    return representatives, ambiguous, rejected


def _comparison_rule(parameter: dict) -> dict:
    return {
        "min_confidence": float(parameter.get("comparison_min_confidence", 0.78)),
        "abs_tolerance": float(parameter.get("comparison_abs_tolerance", 0.01)),
        "rel_tolerance": float(parameter.get("comparison_rel_tolerance", 0.005)),
        "documents": set(parameter.get("comparison_documents", [])),
        "priority": parameter.get("priority", "Средний"),
    }


def _evidence_level(representatives: dict[str, Finding]) -> str:
    if len(representatives) >= 3 and all(_quality_score(x) >= 0.88 for x in representatives.values()):
        return "Высокая"
    if len(representatives) >= 2 and all(_quality_score(x) >= 0.80 for x in representatives.values()):
        return "Средняя"
    return "Низкая"


def compare_findings(findings: list[Finding], parameters: list[dict]) -> list[dict]:
    """Выполняет доказательную межраздельную сверку.

    Сравниваются только значения, связанные с одним каноническим объектом,
    характеристикой и нормализованной единицей. Для каждой характеристики
    применяются собственные допуски и допустимые разделы.
    """
    parameter_map = {p.get("code"): p for p in parameters}
    groups: dict[tuple[str, str, str], list[Finding]] = {}
    for finding in findings:
        if finding.value is None or finding.object_hint == "Не определён":
            continue
        groups.setdefault(
            (finding.object_hint, finding.parameter_code, normalize_unit(finding.unit)), []
        ).append(finding)

    rows: list[dict] = []
    for (object_hint, code, unit), items in groups.items():
        parameter = parameter_map.get(code, {})
        rule = _comparison_rule(parameter)
        eligible_items = [
            x for x in items
            if not rule["documents"] or x.document_type in rule["documents"]
        ]
        representatives, ambiguous, rejected = _representative_by_document(
            eligible_items,
            min_confidence=rule["min_confidence"],
            abs_tol=rule["abs_tolerance"],
            rel_tol=rule["rel_tolerance"],
        )
        involved = set(representatives) | set(ambiguous)
        if len(involved) < 2:
            continue

        check_code = f"CROSS-{code}-{re.sub(r'[^А-Яа-яA-Za-z0-9]+', '-', object_hint).strip('-')[:30]}"
        base = {
            "check_code": check_code,
            "object": object_hint,
            "parameter_code": code,
            "parameter_name": items[0].parameter_name,
            "unit": unit,
            "priority": rule["priority"],
            "evidence_level": _evidence_level(representatives),
            "evidence_count": len(representatives),
            "rejected_count": sum(len(v) for v in rejected.values()),
        }

        if ambiguous:
            source_parts = []
            for doc, doc_items in sorted(ambiguous.items()):
                values = sorted({float(x.value) for x in doc_items if x.value is not None})
                pages = sorted({x.page for x in doc_items})
                source_parts.append(f"{doc}: значения {values}, стр. {pages}")
            for doc, item in sorted(representatives.items()):
                source_parts.append(f"{doc}, стр. {item.page}: {item.value_text}")
            rows.append({
                **base,
                "status": "ТРЕБУЕТ УТОЧНЕНИЯ",
                "min_value": "",
                "max_value": "",
                "difference": "",
                "documents": ", ".join(sorted(involved)),
                "document_values": " | ".join(source_parts),
                "sources": " | ".join(source_parts),
                "comment": "В одном из разделов есть несколько равноценных значений. Нужен выбор корректного источника.",
            })
            continue

        values = [float(item.value) for item in representatives.values()]
        min_value, max_value = min(values), max(values)
        mismatch = not math.isclose(
            min_value,
            max_value,
            rel_tol=rule["rel_tolerance"],
            abs_tol=rule["abs_tolerance"],
        )
        difference = max_value - min_value
        doc_values = " | ".join(
            f"{doc}: {item.value:g} {unit or ''} (стр. {item.page}, уверенность {_quality_score(item):.0%})"
            for doc, item in sorted(representatives.items())
        )
        rows.append({
            **base,
            "status": "ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ" if mismatch else "СОВПАДАЕТ",
            "min_value": min_value,
            "max_value": max_value,
            "difference": difference,
            "documents": ", ".join(sorted(representatives)),
            "document_values": doc_values,
            "sources": " | ".join(
                f"{doc}, стр. {item.page}: {item.value_text}"
                for doc, item in sorted(representatives.items())
            ),
            "comment": (
                "Подтверждённые значения в разделах отличаются сверх установленного допуска."
                if mismatch else "Значение подтверждено минимум в двух разделах в пределах допуска."
            ),
        })

    order = {"ПОТЕНЦИАЛЬНОЕ РАСХОЖДЕНИЕ": 0, "ТРЕБУЕТ УТОЧНЕНИЯ": 1, "СОВПАДАЕТ": 2}
    priority_order = {"Высокий": 0, "Средний": 1, "Низкий": 2}
    rows.sort(key=lambda row: (
        order.get(row["status"], 9),
        priority_order.get(row.get("priority", "Средний"), 9),
        row["object"],
        row["parameter_name"],
    ))
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
        doc_findings = extract_findings(uploaded.name, doc_type, pages, parameters, objects)
        object_positions = {
            x.genplan_position for x in doc_findings
            if x.parameter_code == "OBJECT_ENTRY" and x.genplan_position
        }
        characteristic_count = sum(1 for x in doc_findings if x.parameter_code != "OBJECT_ENTRY")
        documents.append({
            "Файл": uploaded.name,
            "Тип документа": doc_type,
            "Страниц": len(pages),
            "Профиль анализа": _profile_name(doc_type),
            "Объектов по реестру": len(object_positions),
            "Извлечено характеристик": characteristic_count,
            "Высокая уверенность": sum(1 for x in doc_findings if x.parameter_code != "OBJECT_ENTRY" and x.confidence >= 0.82),
        })
        all_findings.extend(doc_findings)
    return documents, [f.to_dict() for f in all_findings], compare_findings(all_findings, parameters)
