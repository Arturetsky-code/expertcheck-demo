from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable

from .normalization import normalize_text
from .object_quality_rules import name_rejection_reasons

FORBIDDEN_ZONE_TOKENS = (
    'состав проектной документации','ведомость документов','ведомость ссылочных',
    'содержание','оглавление','перечень файлов','титульный лист','исходно-разрешительная',
    'перечень норматив','список исполнителей','сведения о лицах','контрольная сумма',
)
FORBIDDEN_NAME_RE = re.compile(
    r'(?:\.pdf|\.xml|\.sig|\.zip|\.docx?|\.xlsx?|раздел\s+пд|подраздел\s+пд|'
    r'^раздел\s+\d+|^часть\s+\d+|^том\s*№?|пояснительная записка$|'
    r'архитектурные решения$|конструктивные решения$|технологические решения$|'
    r'проект организации строительства$|система электроснабжения$|система водоснабжения$|'
    r'система водоотведения$|мероприятия по охране окружающей среды$)', re.I,
)

SOURCE_TYPE_LABELS = {
    'OBJECT_REGISTER': 'официальный перечень объектов',
    'OBJECT_TEP': 'таблица ТЭП объекта',
    'DRAWING_FIELD': 'поле чертежа',
    'NARRATIVE': 'текстовое упоминание',
    'DOCUMENT_SERVICE': 'служебная зона документа',
}


def is_forbidden_evidence(item: dict[str, Any]) -> tuple[bool, str]:
    name = str(item.get('value_text') or item.get('object_hint') or '')
    if item.get('pz_complex_object_register') or item.get('source_kind') == 'pz_complex_object_register':
        return False, ''
    zone = normalize_text(' '.join(str(item.get(k) or '') for k in (
        'trusted_zone','structural_zone','context','table_type','table_evidence','parameter_name'
    )))
    if FORBIDDEN_NAME_RE.search(name):
        return True, 'наименование документа, раздела или файла'
    strict_reasons = name_rejection_reasons(name)
    if strict_reasons:
        return True, '; '.join(strict_reasons)
    if any(token in zone for token in FORBIDDEN_ZONE_TOKENS):
        return True, 'служебная зона документа не может создавать объект'
    return False, ''


def evidence_record(item: dict[str, Any]) -> dict[str, Any]:
    forbidden, reason = is_forbidden_evidence(item)
    page = item.get('page') or item.get('Страница') or ''
    document_type = str(item.get('document_type') or item.get('Раздел') or '').strip()
    document = str(item.get('document') or item.get('Файл') or '').strip()
    section = str(item.get('section_title') or item.get('structural_zone') or item.get('context') or '').strip()
    table = str(item.get('table_title') or item.get('table_evidence') or '').strip()
    row = item.get('row_index') or item.get('table_row') or ''
    source_type = str(item.get('trusted_zone') or '').strip() or 'NARRATIVE'
    return {
        'document_type': document_type,
        'document': document,
        'page': page,
        'section': section,
        'table': table,
        'row': row,
        'position': str(item.get('genplan_position') or '').strip(),
        'source_type': source_type,
        'source_type_label': SOURCE_TYPE_LABELS.get(source_type, source_type),
        'confidence': item.get('object_trust_score', item.get('core2_confidence', '')),
        'lifecycle': item.get('object_lifecycle_status') or 'Не определён',
        'forbidden': forbidden,
        'forbidden_reason': reason,
        'quote': str(item.get('value_text') or item.get('object_hint') or '').strip(),
    }


def build_evidence_index(findings: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in findings:
        if str(item.get('parameter_code') or '') not in {'OBJECT_ENTRY','OBJECT_CANDIDATE'}:
            continue
        name = normalize_text(item.get('value_text') or item.get('object_hint') or '')
        pos = str(item.get('genplan_position') or '').strip()
        rec = evidence_record(item)
        if pos:
            by_key[f'pos:{pos}'].append(rec)
        if name:
            by_key[f'name:{name}'].append(rec)
    return dict(by_key)


def evidence_for_row(row: dict[str, Any], index: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    pos = str(row.get('Позиция по ГП') or row.get('Позиция') or '').strip()
    name = normalize_text(row.get('Наименование объекта') or row.get('Объект') or '')
    records: list[dict[str, Any]] = []
    if pos:
        records.extend(index.get(f'pos:{pos}', []))
    if name:
        records.extend(index.get(f'name:{name}', []))
    unique=[]; seen=set()
    for rec in records:
        key=(rec['document'],rec['page'],rec['section'],rec['table'],rec['quote'])
        if key not in seen:
            seen.add(key); unique.append(rec)
    return sorted(unique, key=lambda x: (bool(x['forbidden']), -float(x['confidence'] or 0) if str(x['confidence']).replace('.','',1).isdigit() else 0))


def compact_source(rec: dict[str, Any]) -> str:
    parts=[]
    if rec.get('document_type'): parts.append(str(rec['document_type']))
    if rec.get('section'): parts.append(str(rec['section'])[:70])
    if rec.get('page'): parts.append(f"стр. {rec['page']}")
    if rec.get('table'): parts.append(str(rec['table'])[:70])
    return ', '.join(parts) or str(rec.get('document') or 'Источник не определён')
