from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

import fitz

from .normalization import normalize_text
from .position_rules import normalize_genplan_position

OFFICIAL_REGISTER_MARKERS = (
    'состав сложного объекта', 'сведения о составе объекта', 'экспликация зданий и сооружений',
    'экспликация сооружений', 'экспликация площадок', 'экспликация производственных площадок',
    'перечень проектируемых объектов', 'сведения о зданиях и сооружениях',
)
SERVICE_MARKERS = (
    'состав проектной документации', 'содержание', 'оглавление', 'ведомость документов',
    'ведомость ссылочных и прилагаемых документов', 'перечень файлов', 'титульный лист',
    'список исполнителей', 'перечень нормативных документов',
)
PROPERTY_MARKERS = {
    'AREA_BUILD': ('площадь застройки',),
    'AREA_TOTAL': ('общая площадь',),
    'VOLUME_BUILD': ('строительный объем', 'строительный объём'),
    'HEIGHT_BUILD': ('высота здания', 'высота сооружения', 'высота'),
    'FLOORS': ('этажность', 'количество этажей', 'число этажей'),
    'POWER_INSTALLED': ('установленная мощность',),
    'POWER_CALCULATED': ('расчетная мощность', 'расчётная мощность', 'расчетная нагрузка', 'расчётная нагрузка', 'максимальная мощность'),
    'MOISTURE': ('влажность руды', 'влажность материала', 'массовая влажность'),
    'BULK_DENSITY': ('насыпная плотность', 'объемная масса', 'объёмная масса'),
    'CAPACITY': ('производительность', 'пропускная способность'),
    'PRESSURE': ('рабочее давление', 'давление'),
    'FLOW_RATE': ('расход',),
    'VOLUME': ('объем', 'объём', 'вместимость'),
    'DIAMETER': ('диаметр',),
    'LENGTH': ('протяженность', 'протяжённость', 'длина'),
    'WIDTH': ('ширина',),
    'QUANTITY': ('количество',),
}
UNITS = r'(?:м²|м2|м³|м3|м|км|мм|кВт|кВА|МВт|МПа|кПа|бар|т/ч|т/сут|т/год|т/м³|т/м3|кг/м³|кг/м3|м³/ч|м3/ч|м³/сут|м3/сут|л/с|шт\.?|эт\.?|%)'
VALUE_RE = re.compile(r'(?P<value>-?\d+(?:[\s ]\d{3})*(?:[.,]\d+)?)\s*(?P<unit>'+UNITS+r')?', re.I)
POSITION_RE = re.compile(r'^\s*(\d{1,3}(?:\.\d{1,3}){0,5})\s*$')
FILE_RE = re.compile(r'\.(?:pdf|xml|sig|zip|docx?|xlsx?)$', re.I)


@dataclass
class PageStructure:
    document: str
    document_type: str
    page: int
    zone: str
    confidence: int
    table_count: int
    block_count: int
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _zone(text: str) -> tuple[str, int, str]:
    low = normalize_text(text)
    if any(x in low for x in SERVICE_MARKERS):
        return 'DOCUMENT_SERVICE', 99, 'Обнаружена служебная зона документа.'
    if any(x in low for x in OFFICIAL_REGISTER_MARKERS):
        return 'OFFICIAL_OBJECT_REGISTER', 98, 'Обнаружен официальный перечень/экспликация объектов.'
    if 'технико-экономические показатели' in low or 'основные показатели' in low:
        return 'OBJECT_PROPERTY_TABLE', 94, 'Обнаружена таблица технико-экономических показателей.'
    if 'генеральный план' in low or 'ситуационный план' in low:
        return 'DRAWING', 85, 'Обнаружен графический лист генерального/ситуационного плана.'
    return 'NARRATIVE', 55, 'Обычный текстовый фрагмент.'


def _clean_cell(value: Any) -> str:
    return ' '.join(str(value or '').replace('\n', ' ').split()).strip()


def _looks_object_name(value: str) -> bool:
    text = _clean_cell(value)
    low = normalize_text(text)
    if len(text) < 3 or len(text) > 220 or FILE_RE.search(text):
        return False
    if any(x in low for x in SERVICE_MARKERS):
        return False
    if low in {'наименование', 'наименование объекта', 'показатель', 'значение', 'примечание', 'номер на плане'}:
        return False
    if not any(ch.isalpha() for ch in text):
        return False
    return True


def _parse_value(value: str) -> tuple[float | None, str]:
    m = VALUE_RE.search(str(value or ''))
    if not m:
        return None, ''
    raw = m.group('value').replace(' ', '').replace('\u00a0', '').replace(',', '.')
    try:
        number = float(raw)
    except ValueError:
        return None, ''
    return number, (m.group('unit') or '').strip()


def _header_index(headers: list[str], tokens: tuple[str, ...]) -> int | None:
    for idx, header in enumerate(headers):
        low = normalize_text(header)
        if any(token in low for token in tokens):
            return idx
    return None


def _property_code(header: str) -> str | None:
    low = normalize_text(header)
    for code, tokens in PROPERTY_MARKERS.items():
        if any(token in low for token in tokens):
            return code
    return None


def _tables(page: fitz.Page) -> list[list[list[str]]]:
    result: list[list[list[str]]] = []
    try:
        finder = page.find_tables()
        for table in finder.tables:
            matrix = table.extract()
            if matrix and len(matrix) >= 2:
                result.append([[_clean_cell(cell) for cell in row] for row in matrix])
    except Exception:
        pass
    return result


def _object_findings_from_table(
    matrix: list[list[str]], filename: str, doc_type: str, page_no: int, zone: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    headers = matrix[0]
    pos_idx = _header_index(headers, ('позиция', 'номер на плане', '№', 'поз.'))
    name_idx = _header_index(headers, ('наименование объекта', 'наименование здания', 'наименование сооружения', 'наименование'))
    if name_idx is None:
        return findings, audit
    property_columns = [(idx, _property_code(header), header) for idx, header in enumerate(headers)]
    property_columns = [(i, c, h) for i, c, h in property_columns if c]
    for row_no, row in enumerate(matrix[1:], start=2):
        if name_idx >= len(row):
            continue
        name = _clean_cell(row[name_idx])
        if not _looks_object_name(name):
            continue
        position = ''
        if pos_idx is not None and pos_idx < len(row):
            candidate = _clean_cell(row[pos_idx])
            position = normalize_genplan_position(candidate, allow_integer=True)
        evidence = f'Таблица, строка {row_no}: ' + ' | '.join(row)
        findings.append({
            'document': filename, 'document_type': doc_type, 'page': page_no,
            'parameter_code': 'OBJECT_ENTRY', 'parameter_name': 'Объект проекта',
            'value': 1.0, 'value_text': name, 'unit': 'шт.', 'object_hint': name,
            'genplan_position': position, 'confidence': 0.99 if zone == 'OFFICIAL_OBJECT_REGISTER' else 0.92,
            'match_method': 'Cognitive Document Intelligence: строка структурированной таблицы',
            'structural_zone': zone, 'trusted_zone': 'OBJECT_REGISTER' if zone == 'OFFICIAL_OBJECT_REGISTER' else 'OBJECT_TEP',
            'record_kind': 'project_object', 'table_title': 'Структурированная объектная таблица',
            'table_row': row_no, 'table_evidence': evidence, 'source_bbox': '',
            'cognitive_extraction': True,
        })
        audit.append({'document': filename, 'page': page_no, 'row': row_no, 'position': position, 'name': name, 'decision': 'object', 'evidence': evidence})
        for col_idx, code, header in property_columns:
            if col_idx >= len(row):
                continue
            value, unit = _parse_value(row[col_idx])
            if value is None:
                continue
            findings.append({
                'document': filename, 'document_type': doc_type, 'page': page_no,
                'parameter_code': code, 'parameter_name': header, 'value': value,
                'value_text': _clean_cell(row[col_idx]), 'unit': unit, 'object_hint': name,
                'genplan_position': position, 'confidence': 0.99,
                'match_method': 'Cognitive Property Binding: та же строка таблицы, что и объект',
                'structural_zone': 'OBJECT_TEP', 'trusted_zone': 'OBJECT_TEP',
                'table_title': 'Структурированная объектная таблица', 'table_row': row_no,
                'table_column': col_idx + 1, 'table_header': header, 'table_evidence': evidence,
                'binding_status': 'ROW_LOCKED', 'cognitive_extraction': True,
            })
    return findings, audit


class CognitiveDocumentIntelligence:
    """Layout-aware extraction layer using PyMuPDF tables and page zones.

    It intentionally creates objects only from official registers or object/property tables.
    Narrative text is retained for evidence, but cannot create a project object.
    """

    def extract_uploaded(self, files, document_types: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        findings: list[dict[str, Any]] = []
        structures: list[dict[str, Any]] = []
        audit: list[dict[str, Any]] = []
        seen: set[tuple[str, int, str, str]] = set()
        for uploaded in files:
            filename = str(getattr(uploaded, 'name', ''))
            doc_type = document_types.get(filename, '')
            try:
                pdf = fitz.open(stream=uploaded.getvalue(), filetype='pdf')
            except Exception as exc:
                audit.append({'document': filename, 'decision': 'error', 'reason': str(exc)})
                continue
            for page in pdf:
                page_no = page.number + 1
                text = page.get_text('text')
                zone, confidence, reason = _zone(text)
                # find_tables() is expensive on large drawings and narrative pages.
                # Run it only where document semantics indicate an object register or TEP table.
                if zone in {'OFFICIAL_OBJECT_REGISTER', 'OBJECT_PROPERTY_TABLE'}:
                    tables = _tables(page)
                else:
                    tables = []
                blocks = page.get_text('blocks')
                structures.append(PageStructure(filename, doc_type, page_no, zone, confidence, len(tables), len(blocks), reason).to_dict())
                if zone == 'DOCUMENT_SERVICE':
                    audit.append({'document': filename, 'page': page_no, 'decision': 'blocked', 'reason': reason})
                    continue
                for matrix in tables:
                    f_rows, a_rows = _object_findings_from_table(matrix, filename, doc_type, page_no, zone)
                    for item in f_rows:
                        key = (filename, page_no, str(item.get('parameter_code')), normalize_text(str(item.get('object_hint'))) + '|' + str(item.get('value_text')))
                        if key in seen:
                            continue
                        seen.add(key)
                        findings.append(item)
                    audit.extend(a_rows)
        return findings, structures, audit
