from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from .normalization import normalize_text

TOC_ZONE_TOKENS = (
    'содержание', 'оглавление', 'состав тома', 'содержание тома', 'перечень разделов',
    'ведомость документов', 'состав проектной документации', 'состав раздела',
)
TOC_HEADINGS = {
    'введение','общие положения','общие сведения','исходные данные','основные положения',
    'описание проектных решений','технико-экономические показатели','заключение','приложения',
    'термины и определения','нормативные ссылки','содержание','оглавление','общая часть',
    'пояснительная записка','сведения о проекте','характеристика района строительства',
}
TOC_NUMBERED_RE = re.compile(r'^\s*(?:раздел\s+)?\d+(?:\.\d+){0,5}\s+[А-ЯA-Zа-яё][^|]{1,160}$', re.I)
TOC_DOTTED_RE = re.compile(r'^\s*\d+(?:\.\d+){1,5}\s+[А-ЯA-Zа-яё]', re.I)
PAGE_TRAILER_RE = re.compile(r'\.{2,}\s*\d+\s*$')

MANDATORY_DOCUMENTS = (
    {
        'code':'IRD-OCN','title':'Сведения/справка об объектах культурного наследия',
        'tokens':('объект культурного наследия','окн','историко-культурн'),
        'applicability':'По территории проектирования и принятым проектным решениям',
        'risk':'Проверить покрытие всей территории проектирования, включая изменённые примыкания и линейные участки.',
    },
    {
        'code':'IRD-OOPT','title':'Сведения/справка об особо охраняемых природных территориях',
        'tokens':('особо охраняем','оопт','природн территор'),
        'applicability':'По территории проектирования',
        'risk':'Проверить наличие актуальных сведений по федеральным, региональным и местным ООПТ.',
    },
    {
        'code':'IRD-LAND','title':'Документы, подтверждающие права на земельные участки',
        'tokens':('договор аренды','земельн участ','выписка егрн','право пользован'),
        'applicability':'Для земельных участков, занятых объектами и временными площадками',
        'risk':'Сверить кадастровые номера, срок действия и охват всех участков проектирования.',
    },
    {
        'code':'IRD-GPZU','title':'Градостроительный план земельного участка / иные градостроительные исходные данные',
        'tokens':('градостроительн план','гпзу','градостроительн регламент'),
        'applicability':'В случаях, когда документ требуется для соответствующего объекта и территории',
        'risk':'Не считать отсутствие автоматическим нарушением без оценки применимости.',
    },
    {
        'code':'IRD-TU','title':'Технические условия и условия подключения',
        'tokens':('технические условия','условия подключения','ту №','ту на подключение'),
        'applicability':'При подключении к внешним инженерным сетям и инфраструктуре',
        'risk':'Проверить срок действия, владельца сети и соответствие принятых решений условиям.',
    },
    {
        'code':'IRD-CLIMATE','title':'Климатические и гидрометеорологические исходные данные',
        'tokens':('климатическ','гидрометеоролог','справка о климат','метеостанц'),
        'applicability':'Для решений, зависящих от климатических параметров',
        'risk':'Проверить актуальность исходных данных и согласованность параметров между разделами.',
    },
)

NORM_REF_RE = re.compile(r'\b(?:ГОСТ(?:\s+Р)?|СП|СНиП|ФЗ|Постановлен(?:ие|ия)|Приказ)\s*[№N]?\s*[A-Za-zА-Яа-я0-9.\-/]+', re.I)


def _blob(item: dict[str, Any]) -> str:
    return normalize_text(' '.join(str(item.get(k) or '') for k in (
        'value_text','object_hint','context','section_title','structural_zone','table_title',
        'table_evidence','parameter_name','document_type','document','trusted_zone','match_method'
    )))


def looks_like_toc_entry(value: Any, *, context: str = '', section_title: str = '', structural_zone: str = '') -> tuple[bool, str]:
    raw = str(value or '').strip()
    low = normalize_text(raw)
    zone = normalize_text(' '.join([context, section_title, structural_zone]))
    if not raw:
        return False, ''
    if any(token in zone for token in TOC_ZONE_TOKENS):
        if TOC_NUMBERED_RE.match(raw) or TOC_DOTTED_RE.match(raw) or PAGE_TRAILER_RE.search(raw):
            return True, 'элемент содержания/оглавления'
    # Typical heading rows like "1.1 Введение" are blocked even when the PDF lost the heading "Содержание".
    if TOC_DOTTED_RE.match(raw):
        tail = normalize_text(re.sub(r'^\s*\d+(?:\.\d+){1,5}\s*', '', raw))
        if tail in TOC_HEADINGS or any(tail.startswith(x + ' ') for x in TOC_HEADINGS):
            return True, 'нумерованный заголовок раздела документа'
        # Section titles are usually abstract nouns and contain no engineering object noun.
        if len(tail.split()) <= 9 and any(x in tail for x in ('сведен','описан','решен','требован','мероприят','организац','обоснован','характеристик','расчет','расчёт')):
            return True, 'нумерованный структурный заголовок документа'
    if low in TOC_HEADINGS:
        return True, 'заголовок раздела документа'
    return False, ''


def apply_structure_guards(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    audit = {'checked':0,'blocked_toc':0,'service_zones':0}
    for item in findings:
        if str(item.get('parameter_code') or '') not in {'OBJECT_ENTRY','OBJECT_CANDIDATE'}:
            continue
        audit['checked'] += 1
        name = item.get('value_text') or item.get('object_hint') or ''
        is_toc, reason = looks_like_toc_entry(
            name,
            context=str(item.get('context') or ''),
            section_title=str(item.get('section_title') or ''),
            structural_zone=str(item.get('structural_zone') or ''),
        )
        blob = _blob(item)
        in_service_zone = any(token in blob for token in TOC_ZONE_TOKENS)
        if is_toc or in_service_zone:
            item['trusted_zone'] = 'DOCUMENT_SERVICE'
            item['structure_guard_blocked'] = True
            item['structure_guard_reason'] = reason or 'служебная зона документа'
            item['object_intelligence_decision'] = 'blocked'
            item['object_intelligence_confidence'] = 0
            item['object_intelligence_reason'] = 'Structure Guard: ' + item['structure_guard_reason']
            item['object_trust_score'] = -100
            if is_toc: audit['blocked_toc'] += 1
            if in_service_zone: audit['service_zones'] += 1
    return audit


def audit_mandatory_documents(documents: Iterable[dict[str, Any]], findings: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    text_parts=[]
    for doc in documents:
        text_parts.extend(str(doc.get(k) or '') for k in ('Файл','Раздел','Тип документа','Семейство'))
    for f in findings:
        text_parts.extend(str(f.get(k) or '') for k in ('document','document_type','context','section_title','table_title','value_text'))
    blob=normalize_text(' '.join(text_parts))
    rows=[]
    for rule in MANDATORY_DOCUMENTS:
        matched=[token for token in rule['tokens'] if token in blob]
        rows.append({
            'code':rule['code'],'title':rule['title'],
            'status':'Найдено' if matched else 'Требует проверки',
            'matched_signals':matched[:6],
            'applicability':rule['applicability'],
            'recommendation':rule['risk'],
        })
    return rows


def scan_normative_references(findings: Iterable[dict[str, Any]], limit: int = 250) -> list[dict[str, Any]]:
    rows=[]; seen=set()
    for item in findings:
        text=' '.join(str(item.get(k) or '') for k in ('context','section_title','table_title','value_text'))
        for match in NORM_REF_RE.findall(text):
            ref=re.sub(r'\s+',' ',match).strip(' .;,')
            key=normalize_text(ref)
            if not key or key in seen: continue
            seen.add(key)
            rows.append({'reference':ref,'document':item.get('document'),'page':item.get('page'),'status':'Требует проверки актуальности'})
            if len(rows)>=limit: return rows
    return rows
