from __future__ import annotations

import re
from typing import Any, Iterable

from .normalization import normalize_text
from .object_quality_rules import has_object_semantics, name_rejection_reasons
from .position_rules import is_date_like_position, normalize_genplan_position

# Strong linguistic anchors that often introduce the actual scope of construction.
STRONG_SCOPE_MARKERS = (
    'проектом предусматривается строительство',
    'проектом предусмотрено строительство',
    'проектом предусматривается реконструкция',
    'проектом предусмотрена реконструкция',
    'проектными решениями предусматривается строительство',
    'в состав проектируемого объекта входят',
    'в состав объекта входят',
    'состав сложного объекта',
    'перечень проектируемых объектов',
    'перечень зданий и сооружений',
    'экспликация зданий и сооружений',
    'экспликация проектируемых объектов',
    'идентификационные признаки зданий и сооружений',
    'идентификационные признаки объекта',
)

CONSTRUCTION_SCOPE_MARKERS = (
    'проектом предусматривается строительство',
    'проектом предусмотрено строительство',
    'проектом предусматривается реконструкция',
    'проектом предусмотрена реконструкция',
    'проектными решениями предусматривается строительство',
    'в состав проектируемого объекта входят',
    'в состав объекта входят',
)

IDENTIFICATION_MARKERS = (
    'идентификационные признаки',
    'наименование здания или сооружения',
    'наименование объекта капитального строительства',
    'принадлежность к объектам транспортной инфраструктуры',
    'назначение здания или сооружения',
)

TOC_CONTEXT_MARKERS = ('содержание', 'оглавление', 'состав тома', 'перечень листов', 'содержание тома')
LINE_NO_RE = re.compile(r'^\s*(?P<pos>\d{1,3}(?:\.\d{1,3}){0,4})[.)]?\s+(?P<name>.+?)\s*$')
BULLET_RE = re.compile(r'^\s*(?:[-–—•▪●]|\d+[.)])\s*(.+?)\s*$')
SPLIT_RE = re.compile(r'\s*(?:;|\n|\r|•|▪|●)\s*')
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.;])\s+(?=[А-ЯA-Z0-9])')

# Phrases that indicate text is describing scope rather than a document heading.
PROJECT_SCOPE_TOKENS = ('проектируем', 'строительств', 'реконструкц', 'возведен', 'размещен', 'предусмотр')


def _clean_candidate(text: str) -> tuple[str, str]:
    raw = re.sub(r'\s+', ' ', str(text or '')).strip(' \t\r\n;:,.–—-')
    if not raw:
        return '', ''
    pos = ''
    m = LINE_NO_RE.match(raw)
    if m:
        maybe_pos = normalize_genplan_position(m.group('pos'), allow_integer=True)
        if maybe_pos and not is_date_like_position(m.group('pos')):
            pos = maybe_pos
            raw = m.group('name').strip(' ;:,.–—-')
    m2 = BULLET_RE.match(raw)
    if m2:
        raw = m2.group(1).strip(' ;:,.–—-')
    # Strip common lead-ins without destroying the engineering noun phrase.
    raw = re.sub(r'^(?:строительство|реконструкция|техническое перевооружение)\s+(?:объекта\s+)?', '', raw, flags=re.I)
    raw = re.sub(r'^(?:проектируем(?:ого|ой|ые|ых)|строящегося)\s+', '', raw, flags=re.I)
    return pos, raw.strip()


def _is_plausible_object_name(name: str, *, strong_context: bool = False) -> bool:
    if not name or len(name) < 3 or len(name) > 180:
        return False
    low = normalize_text(name)
    if is_date_like_position(name):
        return False
    if '. ' in name or name.count('.') >= 2 or re.search(r'\b(?:RAM|РД|ПД)-?\d', name, re.I):
        return False
    if re.search(r'\b(?:и|или|по|в|на|для|от|к)$', low):
        return False
    if re.match(r'^\d{1,3}(?:\.\d{1,3}){1,5}\s+', name) and not has_object_semantics(name):
        return False
    # Sentence-like prose, legal references and actions are not register names.
    if any(tok in low for tok in ('в соответствии с','федеральн закон','градостроительн кодекс','застройщик','использовать','используя','выполняется','будет расположен','будет размещ','будет введен','будет введён','являются','является','представлено','организовать','схема устройства','система пожарной сигнализации','проектируемую систему','проектируемая система')):
        return False
    reasons = name_rejection_reasons(name)
    if reasons:
        return False
    if has_object_semantics(name):
        return True
    # In a verified object register / identification block, a short proper noun or
    # industry abbreviation can still be an object (e.g. "ККВ", "ДСК", "ОПУ").
    if strong_context:
        # Only compact industry abbreviations are allowed to bypass the object-noun
        # requirement. This prevents an identification-signs page from turning
        # every label or paragraph into an object.
        compact=re.sub(r'[^A-Za-zА-Яа-яЁё0-9-]+','',name)
        known={'ККВ','ДСК','ОПУ','АБК','КТП','ДЭС','ЛОС','ЗИФ','ГРП','ГРС','ДНС','УПН','УКПГ','ПС'}
        if compact.upper() in known or re.fullmatch(r'[A-ZА-ЯЁ]{2,8}(?:-?\d{0,3})?', compact):
            return True
    return False


def _extract_from_scope_sentence(text: str, marker: str) -> list[str]:
    low = normalize_text(text)
    idx = low.find(marker)
    if idx < 0:
        return []
    # Use the original string with an approximate normalized offset only as a signal;
    # then search marker variants case-insensitively to preserve names.
    pattern = re.compile(re.escape(marker), re.I)
    m = pattern.search(text.lower())
    tail = text[m.end():] if m else text
    tail = re.sub(r'^\s*[:—–-]?\s*', '', tail)
    # Keep one to two sentences after the marker; long explanations are not object names.
    parts = SENTENCE_SPLIT_RE.split(tail, maxsplit=2)
    tail = ' '.join(parts[:2])
    chunks = [x for x in re.split(r'\s*(?:;|,\s+(?=(?:здание|сооружение|площадка|станция|склад|резервуар|дорога|трубопровод|линия|узел|комплекс|установка|карьер|отвал|дамба|пруд|хвостохранилище)))\s*', tail, flags=re.I) if x]
    return chunks


def recover_project_objects_from_pages(
    pages_by_document: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Recover project objects from strong textual evidence.

    `pages_by_document` rows: {document, document_type, page, text}.
    The engine deliberately ignores ordinary narrative and TOC pages. It is a
    recall-oriented counterpart to Object Gate: recover only from strong scope,
    identification, object-register or project-construction language.
    """
    findings: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str, str]] = set()

    for row in pages_by_document:
        text = str(row.get('text') or '')
        if not text.strip():
            continue
        low = normalize_text(text)
        doc = str(row.get('document') or '')
        dtype = str(row.get('document_type') or '')
        page = int(row.get('page') or 0)
        # Explicit TOC pages are never recovery sources.
        if any(tok in low[:1200] for tok in TOC_CONTEXT_MARKERS) and low.count('.....') + low.count('…') >= 2:
            audit.append({'document': doc, 'page': page, 'decision': 'skip', 'reason': 'TOC/content page'})
            continue

        strong_marker = next((m for m in STRONG_SCOPE_MARKERS if m in low), '')
        identification = any(m in low for m in IDENTIFICATION_MARKERS)
        strong_page = bool(strong_marker or identification)
        if strong_page:
            audit.append({
                'document': doc, 'page': page, 'decision': 'scope_source',
                'reason': strong_marker or 'идентификационные признаки',
                'excerpt': re.sub(r'\s+', ' ', text).strip()[:3500],
                'document_type': dtype,
            })

        candidates: list[tuple[str, str, str]] = []  # pos, name, evidence type
        if strong_marker:
            for marker in [m for m in CONSTRUCTION_SCOPE_MARKERS if m in low]:
                for chunk in _extract_from_scope_sentence(text, marker):
                    pos, name = _clean_candidate(chunk)
                    if _is_plausible_object_name(name, strong_context=True):
                        candidates.append((pos, name, f'сильная формулировка: {marker}'))

        # Strong pages often contain tables flattened to lines. Read compact lines,
        # but only inside a verified register/identification context.
        if strong_page:
            lines = [re.sub(r'\s+', ' ', x).strip() for x in re.split(r'[\r\n]+', text) if x.strip()]
            for line in lines:
                if len(line) > 220:
                    continue
                line_low=normalize_text(line)
                if any(tok in line_low for tok in ('проектом предусматривается','проектом предусмотрено','состав сложного объекта','перечень проектируемых объектов','идентификационные признаки')):
                    continue
                # A flattened table row may contain several objects separated by semicolons.
                line_chunks=[x.strip() for x in re.split(r'\s*;\s*',line) if x.strip()]
                for chunk in line_chunks:
                    pos, name = _clean_candidate(chunk)
                    if not _is_plausible_object_name(name, strong_context=True):
                        continue
                    nlow = normalize_text(name)
                    if any(label in nlow for label in ('идентификационные признаки', 'наименование здания или сооружения', 'наименование объекта капитального строительства')):
                        continue
                    candidates.append((pos, name, 'идентификационные признаки / официальный перечень'))

        # Construction-scope narrative is allowed only when an engineering noun
        # and an explicit project-action token occur in the same compact sentence.
        for sent in SENTENCE_SPLIT_RE.split(text):
            slow = normalize_text(sent)
            if len(sent) > 400 or not any(tok in slow for tok in PROJECT_SCOPE_TOKENS):
                continue
            if not has_object_semantics(sent):
                continue
            # Try to retain the noun phrase after construction/reconstruction verbs.
            match = re.search(r'(?:строительств[оа]?|реконструкц(?:ия|ии)|размещен(?:ие|ия)|предусматривается|предусмотрено)\s+(?:объекта\s+)?(.{3,180})', sent, re.I)
            if match:
                phrase = match.group(1)
                phrase = re.split(r'[.;]', phrase, maxsplit=1)[0]
                pos, name = _clean_candidate(phrase)
                if _is_plausible_object_name(name, strong_context=False):
                    candidates.append((pos, name, 'проектная формулировка строительства/реконструкции'))

        for pos, name, evidence_type in candidates:
            key = (doc, page, normalize_text(name), pos)
            if key in seen:
                continue
            seen.add(key)
            context_excerpt = ''
            needle = normalize_text(name)
            # Preserve a short evidence excerpt around the object name when possible.
            for line in re.split(r'[\r\n]+', text):
                if needle and needle in normalize_text(line):
                    context_excerpt = re.sub(r'\s+', ' ', line).strip()[:500]
                    break
            official = strong_page
            findings.append({
                'parameter_code': 'OBJECT_ENTRY' if official else 'OBJECT_CANDIDATE',
                'parameter_name': 'Проектируемый объект',
                'value_text': name,
                'object_hint': name,
                'genplan_position': pos,
                'document': doc,
                'document_type': dtype,
                'page': page,
                'confidence': 0.94 if official else 0.78,
                'core2_confidence': 0.94 if official else 0.78,
                'source_type': 'OBJECT_REGISTER' if official else 'NARRATIVE',
                'source_kind': 'project_scope_recovery',
                'match_method': 'Project Object Recovery: ' + evidence_type,
                'structural_zone': 'сильный источник состава проектируемых объектов' if official else 'проектная формулировка состава строительства',
                'context': context_excerpt,
                'object_lifecycle_status': 'Проектируемый',
                'trusted_zone': 'OBJECT_REGISTER' if official else 'NARRATIVE',
                'object_recovery_strong_evidence': official,
                'record_kind': 'project_object',
            })
            audit.append({'document': doc, 'page': page, 'name': name, 'position': pos, 'decision': 'recovered', 'evidence': evidence_type})

    return findings, audit

def recover_project_objects_from_uploaded(files: Iterable[Any], document_types: dict[str,str]) -> tuple[list[dict[str,Any]], list[dict[str,Any]]]:
    """Read PDF page text preserving line structure and run recovery rules."""
    pages=[]
    try:
        import fitz
    except Exception as exc:
        return [], [{'decision':'error','reason':f'PyMuPDF unavailable: {exc}'}]
    for file_obj in files:
        name=str(getattr(file_obj,'name',''))
        try:
            if hasattr(file_obj,'seek'): file_obj.seek(0)
            data=file_obj.read() if hasattr(file_obj,'read') else bytes(file_obj)
            if hasattr(file_obj,'seek'): file_obj.seek(0)
            doc=fitz.open(stream=data,filetype='pdf')
            dtype=str(document_types.get(name) or '')
            for idx,page in enumerate(doc):
                text=page.get_text('text') or ''
                # Object composition is normally textual. Very sparse drawing pages
                # are handled by the general-plan/drawing engines, not this module.
                if len(text.strip()) < 20:
                    continue
                pages.append({'document':name,'document_type':dtype,'page':idx+1,'text':text})
        except Exception as exc:
            pages.append({'document':name,'document_type':str(document_types.get(name) or ''),'page':0,'text':'','error':str(exc)})
    return recover_project_objects_from_pages(pages)
