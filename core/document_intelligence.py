from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from .normalization import normalize_text

SERVICE_TOKENS = (
    'содержание', 'оглавление', 'состав проектной документации', 'ведомость документов',
    'ведомость ссылочных', 'перечень файлов', 'титульный лист', 'список исполнителей',
    'исходно-разрешительная', 'перечень норматив', 'контрольная сумма',
)
OBJECT_REGISTER_TOKENS = (
    'состав сложного объекта', 'экспликация зданий', 'экспликация сооружений',
    'экспликация площадок', 'экспликация производственных площадок',
    'перечень проектируемых объектов', 'сведения о зданиях и сооружениях',
)
TEP_TOKENS = (
    'технико-экономические показатели', 'основные показатели', 'тэп',
    'площадь застройки', 'производительность', 'установленная мощность',
)
DRAWING_TOKENS = ('генеральный план', 'ситуационный план', 'план расположения', 'экспликация')

@dataclass(frozen=True)
class ZoneDecision:
    zone: str
    confidence: int
    can_create_object: bool
    can_create_property: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_zone(item: dict[str, Any]) -> ZoneDecision:
    text = normalize_text(' '.join(str(item.get(k) or '') for k in (
        'section_title', 'structural_zone', 'context', 'table_title', 'table_evidence',
        'parameter_name', 'document_type', 'document',
    )))
    source_type = str(item.get('trusted_zone') or '').strip().upper()
    if source_type == 'DOCUMENT_SERVICE' or any(t in text for t in SERVICE_TOKENS):
        return ZoneDecision('DOCUMENT_SERVICE', 99, False, False, 'Служебная зона документа.')
    if source_type == 'OBJECT_REGISTER' or any(t in text for t in OBJECT_REGISTER_TOKENS):
        return ZoneDecision('OBJECT_REGISTER', 96, True, True, 'Официальный объектный реестр или экспликация.')
    if source_type == 'OBJECT_TEP' or any(t in text for t in TEP_TOKENS):
        return ZoneDecision('OBJECT_TEP', 90, True, True, 'Объектная таблица технико-экономических показателей.')
    if source_type == 'DRAWING_FIELD' or any(t in text for t in DRAWING_TOKENS):
        return ZoneDecision('DRAWING_FIELD', 78, True, False, 'Инженерное поле чертежа или план.')
    return ZoneDecision('NARRATIVE', 45, False, False, 'Обычное текстовое описание; самостоятельно объект не создаёт.')


def redact_text(value: str) -> str:
    text = str(value or '')
    text = re.sub(r'\b\d{3}-\d{3}-\d{3}[ -]?\d{2}\b', '[СНИЛС]', text)
    text = re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-zА-Яа-я]{2,}\b', '[EMAIL]', text)
    text = re.sub(r'\b(?:ИНН|КПП|ОГРН)\s*[:№]?\s*\d+\b', '[РЕКВИЗИТ]', text, flags=re.I)
    text = re.sub(r'\b(?:RAM|РАМ)-[A-ZА-Я0-9._/-]{3,}\b', '[ШИФР]', text, flags=re.I)
    return text


def build_structured_ai_context(
    object_rows: Iterable[dict[str, Any]],
    comparisons: Iterable[dict[str, Any]],
    checklist_rows: Iterable[dict[str, Any]] | None = None,
    max_items: int = 60,
) -> dict[str, Any]:
    objects=[]
    for row in list(object_rows)[:max_items]:
        objects.append({
            'position': redact_text(str(row.get('Позиция по ГП') or '')),
            'name': redact_text(str(row.get('Наименование объекта') or '')),
            'included': bool(row.get('Включить')),
            'decision': str(row.get('Решение Object Intelligence') or ''),
            'confidence': row.get('Доверие Object Intelligence'),
            'reason': redact_text(str(row.get('Обоснование Object Intelligence') or row.get('Блокировка') or '')),
            'source': redact_text(str(row.get('Канонический источник') or row.get('Основание включения') or '')),
        })
    checks=[]
    for row in list(comparisons)[:max_items]:
        checks.append({
            'object': redact_text(str(row.get('object') or row.get('Объект') or '')),
            'property': redact_text(str(row.get('parameter_name') or row.get('parameter') or row.get('Характеристика') or '')),
            'status': str(row.get('status') or row.get('Статус') or ''),
            'values': redact_text(str(row.get('values') or row.get('Значения') or '')),
            'sources': redact_text(str(row.get('sources') or row.get('Источники') or '')),
        })
    checklist=[]
    for row in list(checklist_rows or [])[:max_items]:
        checklist.append({
            'item': redact_text(str(row.get('item_no') or row.get('Позиция') or '')),
            'question': redact_text(str(row.get('question') or row.get('Контрольный вопрос') or '')),
            'status': str(row.get('status') or row.get('Соответствие') or ''),
            'evidence': redact_text(str(row.get('evidence') or '')),
        })
    return {'objects': objects, 'cross_checks': checks, 'checklist': checklist}
