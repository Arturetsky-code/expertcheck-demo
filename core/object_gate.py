from __future__ import annotations

import re
from typing import Any, Iterable

from .normalization import normalize_text
from .object_quality_rules import has_object_semantics, name_rejection_reasons
from .position_rules import is_date_like_position, normalize_genplan_position

# A final hard gate runs after all extractors. It is intentionally stricter than
# individual parsers: service/document structure must never reach the project
# object registry, even when a legacy parser labelled it OBJECT_ENTRY.
NUMBERED_HEADING_RE = re.compile(r"^\s*(?:раздел\s+|подраздел\s+|пункт\s+)?(?P<num>\d+(?:\.\d+){0,6})[.)]?\s+(?P<title>[^|]{2,180})$", re.I)
DOTTED_LEADER_RE = re.compile(r"\.{2,}\s*\d+\s*$")
DATE_PREFIX_RE = re.compile(r"^\s*(\d{1,4}[./-]\d{1,2}[./-]\d{1,4})(?:\s|$)")
PURE_DATE_RE = re.compile(r"^\s*\d{1,4}[./-]\d{1,2}[./-]\d{1,4}\s*$")

SERVICE_TITLES = (
    'введение','общая часть','общие сведения','общие положения','исходные данные','термины и определения',
    'нормативные ссылки','содержание','оглавление','заключение','приложение','приложения','список литературы',
    'описание проектных решений','основные проектные решения','основные решения','технико экономические показатели',
    'технико-экономические показатели','организация строительства','мероприятия по охране окружающей среды',
    'мероприятия по пожарной безопасности','характеристика района строительства','сведения о проекте',
    'сведения об объекте капитального строительства','сведения о земельных участках','расчетная часть','расчётная часть',
)
ABSTRACT_SECTION_STEMS = (
    'сведен','описан','обоснован','требован','мероприят','организац','характеристик','исходн','общ','решен',
    'расчет','расчёт','положен','данн','порядок','назначен','услови','состав документац','пояснен','перечен',
)
SERVICE_ZONE_TOKENS = (
    'содержание','оглавление','состав проектной документации','ведомость документов','состав тома','перечень документов',
    'титульный лист','список исполнителей','ведомость ссылочных','перечень листов','содержание тома',
)

PROPERTY_LABEL_STEMS = (
    'площадь участка', 'площадь застройки', 'общая площадь', 'полезная площадь',
    'строительный объем', 'строительный объём', 'производительность', 'мощность',
    'высота', 'этажность', 'количество этажей', 'протяженность', 'протяжённость',
    'диаметр', 'давление', 'расход', 'вместимость', 'объем', 'объём', 'ширина', 'глубина',
)


def _context_blob(item: dict[str, Any]) -> str:
    return normalize_text(' '.join(str(item.get(k) or '') for k in (
        'context','section_title','structural_zone','table_title','table_evidence','match_method','trusted_zone','parameter_name'
    )))


def _section_heading_reason(name: str, item: dict[str, Any]) -> str:
    raw = str(name or '').strip()
    low = normalize_text(raw)
    context = _context_blob(item)
    if any(token in context for token in SERVICE_ZONE_TOKENS):
        return 'служебная зона документа (содержание/оглавление/ведомость)'
    if DOTTED_LEADER_RE.search(raw):
        return 'строка оглавления с номером страницы'
    match = NUMBERED_HEADING_RE.match(raw)
    if not match:
        return ''
    title = normalize_text(match.group('title')).strip(' .–—-')
    # A numbered row from a verified object register / explication is not a
    # document heading merely because its name is short or industry-specific.
    # Service-zone evidence still wins above and is always blocked.
    strong_register = bool(
        item.get('general_plan_explication')
        or item.get('object_recovery_strong_evidence')
        or item.get('source_kind') in {'xml','project_scope_recovery','pz_complex_object_register'}
        or any(token in normalize_text(str(item.get('match_method') or '') + ' ' + str(item.get('structural_zone') or ''))
               for token in ('экспликац','состав сложного объекта','идентификационн призна','сильный источник состава'))
    )
    if strong_register:
        return ''
    if title in SERVICE_TITLES or any(title.startswith(x + ' ') for x in SERVICE_TITLES):
        return 'нумерованный заголовок раздела документа'
    # Outside a verified object register, a short dotted-number heading without
    # engineering-object semantics is overwhelmingly a section/subsection row.
    # This catches arbitrary TOC items, not only a fixed dictionary of titles.
    if '.' in match.group('num') and not has_object_semantics(title) and len(title.split()) <= 12:
        return 'нумерованный пункт/подпункт проектной документации'
    # Section headings are normally short abstract phrases. Engineering object
    # semantics is required to escape this guard.
    if not has_object_semantics(title) and len(title.split()) <= 14:
        if any(stem in title for stem in ABSTRACT_SECTION_STEMS):
            return 'нумерованный пункт/подпункт проектной документации'
        # In a TOC-like context, any short numbered non-object phrase is service data.
        if any(token in context for token in ('страница','лист','раздел','подраздел','содержание','оглавление')):
            return 'элемент структуры документа'
    return ''


def hard_rejection_reason(item: dict[str, Any]) -> str:
    if str(item.get('parameter_code') or '') not in {'OBJECT_ENTRY','OBJECT_CANDIDATE'}:
        return ''
    name = str(item.get('value_text') or item.get('object_hint') or '').strip()
    position = str(item.get('genplan_position') or '').strip()

    if position and is_date_like_position(position):
        return 'позиция похожа на календарную дату, а не позицию генерального плана'
    if PURE_DATE_RE.match(name) and is_date_like_position(name):
        return 'наименование является календарной датой'
    prefix = DATE_PREFIX_RE.match(name)
    if prefix and is_date_like_position(prefix.group(1)):
        return 'строка начинается с календарной даты'

    # The authoritative PZ complex-object register wins over generic title/service heuristics.
    # Calendar-like positions/names were already blocked above.
    if item.get('pz_complex_object_register') or item.get('source_kind') == 'pz_complex_object_register':
        return ''

    heading = _section_heading_reason(name, item)
    if heading:
        return heading

    low_name = normalize_text(name)
    # A parameter label/value row is not a project object. This specifically
    # prevents rows such as "Площадь застройки, всего" from surviving recovery.
    if any(low_name.startswith(stem) for stem in PROPERTY_LABEL_STEMS):
        return 'наименование является технико-экономическим показателем, а не объектом'
    if re.fullmatch(r'(?:линии|линия|итого|всего)[,;:]?\s*(?:т|шт|м|м2|м²|м3|м³)?', low_name):
        return 'обрывок строки таблицы/показателя, а не объект'

    # Reuse global non-object rules as the final safety net. Object semantics
    # can override only weak generic reasons, never file/service/date reasons.
    reasons = name_rejection_reasons(name)
    hard_tokens = ('файл','служеб','раздел','содержание','оглавление','норматив','шифр','требован','числов','абзац')
    hard = [r for r in reasons if any(t in normalize_text(r) for t in hard_tokens)]
    if hard:
        return '; '.join(hard)
    return ''


def apply_hard_object_gate(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    audit = {'checked': 0, 'blocked': 0, 'date_positions_cleared': 0, 'toc_or_sections_blocked': 0}
    for item in findings:
        if str(item.get('parameter_code') or '') not in {'OBJECT_ENTRY','OBJECT_CANDIDATE'}:
            continue
        audit['checked'] += 1
        position = str(item.get('genplan_position') or '').strip()
        if position:
            normalized = normalize_genplan_position(position, allow_integer=True)
            if not normalized:
                item['genplan_position_original'] = position
                item['genplan_position'] = ''
                if is_date_like_position(position):
                    audit['date_positions_cleared'] += 1
        reason = hard_rejection_reason(item)
        if not reason:
            continue
        item['hard_object_gate_blocked'] = True
        item['hard_object_gate_reason'] = reason
        item['trusted_zone'] = 'DOCUMENT_SERVICE'
        item['structure_guard_blocked'] = True
        item['structure_guard_reason'] = reason
        item['object_intelligence_decision'] = 'blocked'
        item['object_intelligence_confidence'] = 0
        item['object_intelligence_reason'] = 'Object Gate: ' + reason
        item['object_trust_score'] = -1000
        audit['blocked'] += 1
        if any(x in normalize_text(reason) for x in ('оглавлен','содержан','раздел','пункт','структур')):
            audit['toc_or_sections_blocked'] += 1
    return audit
