from __future__ import annotations

import re
from typing import Any, Iterable

from .normalization import canonical_parameter, normalize_numeric, normalize_text
from .object_quality_rules import has_object_semantics
from .position_rules import normalize_genplan_position

# The PZ block "Сведения о сложном объекте ... зданиях (сооружениях), входящих в состав"
# is an authoritative project-object register. It must be parsed before generic
# narrative recovery/filtering because its rows often span several physical text lines.
_COMPLEX_OBJECT_ANCHORS = (
    'сведения о сложном объекте',
    'входящих в состав сложного объект',
)
_STOP_ANCHORS = (
    'заверение проектной организации',
)
_POSITION_LINE = re.compile(r'^\s*(\d{1,3}(?:\.\d{1,3}){1,4})\s*$')
_CLASSIFIER = re.compile(r'^\d{2}\.\d{2}\.\d{3}\.\d{3}\b')
_FOOTER_PATTERNS = (
    re.compile(r'^\d{1,2}\.\d{1,2}\.\d{4},\s*\d{1,2}:\d{2}$'),
    re.compile(r'^about:blank$', re.I),
    re.compile(r'^\d+/\d+$'),
    re.compile(r'^пояснительная записка$', re.I),
)

# Once one of these starts, the object name column has ended and another table
# column / TEP column has begun.
_NAME_STOP_PREFIXES = (
    'рф,', 'российская федерация', 'забайкальский', 'московская область', 'республика ',
    'объекты добычи', 'объекты ', 'сооружение ', 'прочие объекты', 'не принадлежит',
    'принадлежит', 'нормативная ', 'уровень ', 'класс ', 'категория ', 'коэф',
    'площадь ', 'общая площадь', 'полезная площадь', 'строительный объем', 'строительный объём',
    'мощность ', 'производительность ', 'протяженность ', 'протяжённость ', 'длина ',
    'высота ', 'высотность ', 'объем ', 'объём ', 'напряжение ', 'давление ', 'диаметр ',
    'расход ', 'вместимость ', 'количество ', 'ширина ', 'глубина ',
)

# Common object-table parameters in the final column. This is deliberately small
# and conservative; the normal cross-section engine can enrich the rest later.
_PROP_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ('AREA_BUILD', 'Площадь застройки', re.compile(r'площадь\s+застройки\s+([\d\s]+(?:[.,]\d+)?)\s*(м2|м²)', re.I)),
    ('AREA_TOTAL', 'Общая площадь', re.compile(r'общая\s+площадь\s+([\d\s]+(?:[.,]\d+)?)\s*(м2|м²)', re.I)),
    ('VOLUME_BUILD', 'Строительный объём', re.compile(r'строительн(?:ый|ого)\s+об[ъь]ем\s+([\d\s]+(?:[.,]\d+)?)\s*(м3|м³)', re.I)),
    ('LENGTH', 'Протяжённость', re.compile(r'(?:протяженност(?:ь|и)|протяжённост(?:ь|и)|длина)\s+(?:участков\s+)?([\d\s]+(?:[.,]\d+)?)\s*(м|км)', re.I)),
    ('HEIGHT_BUILD', 'Высота здания (сооружения)', re.compile(r'(?:высота|высотность)\s+([\d\s]+(?:[.,]\d+)?)\s*(м)', re.I)),
    ('CAPACITY', 'Производительность', re.compile(r'(?:производительность|мощность)\s+([\d\s]+(?:[.,]\d+)?)\s*([^\s]+(?:/[^\s]+)?)', re.I)),
    ('VOLTAGE', 'Напряжение', re.compile(r'напряжение\s+([\d/.,]+)\s*(кв|кВ)', re.I)),
    ('VOLUME', 'Объём', re.compile(r'(?<!строительный )об[ъь]ем\s+([\d\s]+(?:[.,]\d+)?)\s*(м3|м³)', re.I)),
]


def _is_footer(line: str) -> bool:
    s = line.strip()
    return any(p.fullmatch(s) for p in _FOOTER_PATTERNS)


def _clean_lines(text: str) -> list[str]:
    out: list[str] = []
    for raw in str(text or '').splitlines():
        line = re.sub(r'[\u00ad\ufffe\uffff]', '', raw).strip()
        if not line or _is_footer(line):
            continue
        out.append(line)
    return out


def _find_real_anchor(pages: list[dict[str, Any]]) -> tuple[int, int] | None:
    """Return page-index and line-index of a real complex-object register heading.

    The TOC contains the same heading. A real heading is accepted only when a
    numbered object row appears shortly after it on the same or next page.
    """
    for pi, page in enumerate(pages):
        lines = _clean_lines(page.get('text') or '')
        for li, line in enumerate(lines):
            low = normalize_text(line)
            if not any(a in low for a in _COMPLEX_OBJECT_ANCHORS):
                continue
            probe = lines[li + 1: li + 80]
            if pi + 1 < len(pages):
                probe += _clean_lines(pages[pi + 1].get('text') or '')[:50]
            if any(_POSITION_LINE.fullmatch(x) for x in probe):
                return pi, li
    return None


def _name_from_chunk(chunk: list[str]) -> str:
    parts: list[str] = []
    for line in chunk:
        s = line.strip()
        low = normalize_text(s)
        if not s:
            continue
        if _CLASSIFIER.match(s):
            break
        if any(low.startswith(prefix) for prefix in _NAME_STOP_PREFIXES):
            break
        # Address / table-column switches.
        if re.match(r'^\d{2}\.\d{2}\.\d{3}\.\d{3}\b', s):
            break
        if re.match(r'^(?:ООО|АО|ПАО)\s+[«"]', s, re.I):
            break
        parts.append(s)
        if len(parts) >= 8:
            break
    # Join wrapped lines. Hyphenated compound adjectives ending in -о keep the
    # hyphen (производственно-противопожарного); ordinary PDF word breaks lose it
    # (резервуа- + рами -> резервуарами).
    name = ''
    for part in parts:
        if not name:
            name = part
            continue
        if name.endswith('-'):
            stem = name[:-1].lower()
            # Preserve genuine compound-adjective hyphens; remove only likely
            # PDF word-break hyphens inside an unfinished word.
            preserve = stem.endswith(('о','ая','яя','ое','ее','ый','ий','ой','ого','ему','ому'))
            name = name + part if preserve else name[:-1] + part
        else:
            name += ' ' + part
    name = re.sub(r'\s+', ' ', name).strip(' ;:,.–—-')
    return name[:240]



def _append_page_continuation_if_needed(name: str, chunk_pairs: list[tuple[int, str]], start_page_index: int) -> str:
    """Recover a name cell split by a PDF page boundary / reading order.

    Some tables place the last word of a name at the top of the next page while
    address/classifier columns from the previous page appear earlier in text order.
    Only append a short engineering-object fragment from a later page.
    """
    if not name:
        return name
    later = [line.strip() for pi, line in chunk_pairs if pi > start_page_index and line.strip()]
    for line in later[:4]:
        low = normalize_text(line)
        if _POSITION_LINE.fullmatch(line) or _CLASSIFIER.match(line):
            break
        if any(low.startswith(prefix) for prefix in _NAME_STOP_PREFIXES):
            continue
        if len(line.split()) <= 4 and has_object_semantics(line):
            if normalize_text(line) in normalize_text(name):
                return name
            combined = re.sub(r'\s+', ' ', name + ' ' + line).strip()
            return combined[:240]
        break
    return name

def _find_properties(text: str, base: dict[str, Any]) -> list[dict[str, Any]]:
    flat = re.sub(r'\s+', ' ', text.replace('\ufffe', ' '))
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for code, label, pattern in _PROP_PATTERNS:
        for m in pattern.finditer(flat):
            raw_value = m.group(1).strip()
            unit = m.group(2).strip() if m.lastindex and m.lastindex >= 2 else ''
            value = normalize_numeric(raw_value)
            key = (code, raw_value + unit)
            if key in seen:
                continue
            seen.add(key)
            out.append({
                **base,
                'parameter_code': code,
                'parameter_name': label,
                'value': value,
                'value_text': raw_value,
                'unit': unit.replace('м2', 'м²').replace('м3', 'м³'),
                'confidence': 0.98,
                'match_method': 'PZ Complex Object Register: TEP in same row',
                'binding_status': 'ROW_LOCKED',
                'record_kind': 'object_property',
                'pz_complex_object_register': True,
            })
    return out


def extract_pz_complex_object_register_from_pages(pages: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    page_list = list(pages)
    anchor = _find_real_anchor(page_list)
    if anchor is None:
        return [], [{'decision': 'not_found', 'reason': 'Не найден фактический блок «Сведения о сложном объекте» с позициями'}]

    start_pi, start_li = anchor
    stream: list[tuple[int, str]] = []
    for pi in range(start_pi, len(page_list)):
        lines = _clean_lines(page_list[pi].get('text') or '')
        if pi == start_pi:
            lines = lines[start_li + 1:]
        for line in lines:
            low = normalize_text(line)
            if any(stop in low for stop in _STOP_ANCHORS):
                # End of authoritative object register.
                return _parse_stream(stream, page_list)
            stream.append((pi, line))
    return _parse_stream(stream, page_list)


def _parse_stream(stream: list[tuple[int, str]], pages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    positions: list[tuple[int, int, str]] = []
    for idx, (pi, line) in enumerate(stream):
        m = _POSITION_LINE.fullmatch(line)
        if not m:
            continue
        pos = normalize_genplan_position(m.group(1), allow_integer=False)
        if pos:
            positions.append((idx, pi, pos))
    findings: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    seen: set[str] = set()
    for n, (idx, pi, pos) in enumerate(positions):
        end = positions[n + 1][0] if n + 1 < len(positions) else len(stream)
        chunk_pairs = stream[idx + 1:end]
        chunk = [line for _, line in chunk_pairs]
        name = _name_from_chunk(chunk)
        name = _append_page_continuation_if_needed(name, chunk_pairs, pi)
        if not name or pos in seen:
            continue
        # Final table can contain non-OCS equipment only if explicitly listed there;
        # in this block inclusion itself is authoritative for project composition.
        seen.add(pos)
        page_no = int(pages[pi].get('page') or (pi + 1))
        document = str(pages[pi].get('document') or '')
        document_type = str(pages[pi].get('document_type') or 'ПЗ')
        evidence_text = ' '.join(chunk)
        base = {
            'document': document,
            'document_type': document_type or 'ПЗ',
            'page': page_no,
            'object_hint': name,
            'genplan_position': pos,
            'context': f'Сведения о сложном объекте: {pos} {name}',
            'structural_zone': 'ПЗ / Сведения о сложном объекте / официальный состав',
            'source_kind': 'pz_complex_object_register',
            'trusted_zone': 'OBJECT_REGISTER',
            'object_recovery_strong_evidence': True,
            'pz_complex_object_register': True,
            'object_lifecycle_status': 'Проектируемый',
            'record_kind': 'project_object',
            'table_row': pos,
            'row_index': idx,
            'row_text': evidence_text[:2000],
        }
        findings.append({
            **base,
            'parameter_code': 'OBJECT_ENTRY',
            'parameter_name': 'Объект проекта',
            'value': 1.0,
            'value_text': name,
            'unit': 'шт.',
            'confidence': 0.995,
            'match_method': 'PZ Complex Object Register: authoritative row',
            'object_intelligence_decision': 'trusted',
            'object_intelligence_confidence': 0.995,
            'object_intelligence_reason': 'Строка официального перечня зданий/сооружений в составе сложного объекта ПЗ',
            'object_trust_score': 130,
        })
        findings.extend(_find_properties(evidence_text, base))
        audit.append({
            'document': document,
            'page': page_no,
            'position': pos,
            'name': name,
            'decision': 'accepted',
            'reason': 'официальная строка «Сведения о сложном объекте»',
        })
    return findings, audit


def extract_pz_complex_object_register_from_uploaded(files: Iterable[Any], document_types: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        import fitz
    except Exception as exc:
        return [], [{'decision': 'error', 'reason': f'PyMuPDF unavailable: {exc}'}]
    findings: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for file_obj in files:
        name = str(getattr(file_obj, 'name', ''))
        dtype = str(document_types.get(name) or '')
        # Document classification may be incomplete, so filename is also accepted.
        if dtype != 'ПЗ' and not re.search(r'(?:^|[_\- №])ПЗ(?:[(_\.\-]|$)', name, re.I):
            continue
        try:
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            data = file_obj.read() if hasattr(file_obj, 'read') else bytes(file_obj)
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            doc = fitz.open(stream=data, filetype='pdf')
            pages = [
                {'document': name, 'document_type': dtype or 'ПЗ', 'page': i + 1, 'text': page.get_text('text') or ''}
                for i, page in enumerate(doc)
            ]
            f, a = extract_pz_complex_object_register_from_pages(pages)
            findings.extend(f)
            audit.extend(a)
        except Exception as exc:
            audit.append({'document': name, 'decision': 'error', 'reason': str(exc)})
    return findings, audit


def enforce_authoritative_pz_registry(
    trusted: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    pz_findings: Iterable[dict[str, Any]],
    all_findings: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Use explicit PZ composition as a high-confidence source, not an exclusive whitelist.

    Different project types describe composition differently. Therefore an explicit GP
    explication is an independent strong source and must never be deleted merely because
    the PZ table is absent, incomplete, differently structured, or uses another hierarchy.
    Explicit existing/perspective GP rows remain review candidates.
    """
    pz_objects = [x for x in pz_findings if x.get('parameter_code') == 'OBJECT_ENTRY' and x.get('pz_complex_object_register')]
    if len(pz_objects) < 2:
        return [dict(x) for x in trusted], [dict(x) for x in candidates], {
            'authoritative_pz_active': 0, 'authoritative_positions': len(pz_objects),
            'suppressed_non_authoritative': 0, 'gp_only_candidates': 0,
        }

    authoritative: dict[str, dict[str, Any]] = {}
    for item in pz_objects:
        pos = normalize_genplan_position(item.get('genplan_position') or '', allow_integer=True)
        if pos:
            authoritative[pos] = item

    rows_by_pos: dict[str, dict[str, Any]] = {}
    unpositioned: list[dict[str, Any]] = []
    for row in list(trusted) + list(candidates):
        pos = normalize_genplan_position(row.get('Позиция по ГП') or row.get('position') or '', allow_integer=True)
        if pos:
            # Prefer a trusted/stronger row already present.
            if pos not in rows_by_pos or bool(row.get('Подтвержденный реестр')):
                rows_by_pos[pos] = dict(row)
        else:
            unpositioned.append(dict(row))

    gp_by_pos: dict[str, dict[str, Any]] = {}
    for item in all_findings:
        if not item.get('general_plan_explication'):
            continue
        pos = normalize_genplan_position(item.get('genplan_position') or '', allow_integer=True)
        if pos:
            gp_by_pos[pos] = item

    trusted_out: list[dict[str, Any]] = []
    candidates_out: list[dict[str, Any]] = []
    used: set[str] = set()

    # PZ explicit rows remain the highest-confidence naming source.
    for pos, item in authoritative.items():
        row = dict(rows_by_pos.get(pos) or {})
        row.setdefault('Позиция по ГП', pos)
        row['Наименование объекта'] = str(item.get('value_text') or item.get('object_hint') or row.get('Наименование объекта') or '').strip()
        row['Статус проектирования'] = 'Проектируемый'
        row['Доверие к объекту'] = max(int(row.get('Доверие к объекту') or 0), 140)
        row['Подтвержденный реестр'] = True
        row['В ПЗ'] = True
        row['Включить'] = True
        row['Источник принятого наименования'] = 'ПЗ / Сведения о сложном объекте'
        row['Статус консолидации'] = 'Подтверждено официальным составом сложного объекта ПЗ'
        row['Причины решения'] = (str(row.get('Причины решения') or '') + '; официальный состав сложного объекта ПЗ').strip('; ')
        trusted_out.append(row); used.add(pos)

    # GP explication is an independent composition register. Project/unknown rows are
    # retained even when absent from PZ; explicit existing/perspective rows are review-only.
    gp_only = 0
    for pos, item in gp_by_pos.items():
        if pos in used:
            continue
        row = dict(rows_by_pos.get(pos) or {})
        row.setdefault('Позиция по ГП', pos)
        row['Наименование объекта'] = str(item.get('value_text') or item.get('object_hint') or row.get('Наименование объекта') or '').strip()
        status = str(item.get('general_plan_design_status') or row.get('Статус проектирования') or 'Не определён')
        row['Статус проектирования'] = status
        row['В генплане'] = True
        row['Источник принятого наименования'] = row.get('Источник принятого наименования') or 'Экспликация генерального плана'
        if status in {'Существующий', 'Перспективный'}:
            row['Подтвержденный реестр'] = False
            row['Включить'] = False
            row['Статус консолидации'] = f'Экспликация ГП: {status.lower()} — требуется проверка включения'
            candidates_out.append(row)
        else:
            row['Подтвержденный реестр'] = True
            row['Включить'] = True
            row['Доверие к объекту'] = max(int(row.get('Доверие к объекту') or 0), 120)
            row['Статус консолидации'] = 'Подтверждено экспликацией генерального плана; отсутствует/не сопоставлено в составе ПЗ'
            row['Причины решения'] = (str(row.get('Причины решения') or '') + '; независимый реестр экспликации ГП').strip('; ')
            trusted_out.append(row)
        gp_only += 1; used.add(pos)

    # Preserve other already trusted rows and review candidates instead of silently
    # deleting them. They may represent section-only or unpositioned linear objects.
    for row in list(trusted):
        pos = normalize_genplan_position(row.get('Позиция по ГП') or row.get('position') or '', allow_integer=True)
        if pos and pos in used:
            continue
        trusted_out.append(dict(row))
    for row in list(candidates):
        pos = normalize_genplan_position(row.get('Позиция по ГП') or row.get('position') or '', allow_integer=True)
        if pos and pos in used:
            continue
        candidates_out.append(dict(row))

    return trusted_out, candidates_out, {
        'authoritative_pz_active': 1,
        'authoritative_positions': len(authoritative),
        'suppressed_non_authoritative': 0,
        'gp_only_candidates': gp_only,
    }
