from __future__ import annotations

import math
import re
from typing import Any, Callable

from .normalization import normalize_text
from .object_semantics import canonical_parameter_code
from .requirement_contracts import SCOPE_PROJECT, SCOPE_SITE, SCOPE_SYSTEM, SCOPE_DOCUMENT, SCOPE_OBJECT, SCOPE_EQUIPMENT

# Conservative vocabulary. These expressions are not project-specific; they describe
# engineering metrics that can appear in any industry profile.
METRIC_PATTERNS: dict[str, tuple[str, ...]] = {
    'SHIFT_DURATION': (r'продолжительност[ьи]\s+смены', r'смен[аы]\s*(?:составляет|[-–—:])?'),
    'CAPACITY': (r'производительност[ьи]', r'производственн(?:ая|ой)\s+мощност[ьи]', r'проектн(?:ая|ой)\s+мощност[ьи]', r'мощност[ьи]'),
    'AREA_BUILD': (r'площад[ьи]\s+застройки',),
    'AREA_TOTAL': (r'общ(?:ая|ей)\s+площад[ьи]',),
    'BODY_VOLUME': (r'об[ъь]?[её]м(?:ом)?\s+кузова',),
    'BUCKET_VOLUME': (r'об[ъь]?[её]м(?:ом)?\s+ковша',),
    'POWER_INSTALLED': (r'установленн(?:ая|ой)\s+мощност[ьи]',),
    'FLOW_RATE': (r'расход',),
    'VOLUME': (r'об[ъь]?[её]м', r'вместимост[ьи]'),
    'LENGTH': (r'длин[аы]', r'протяж[её]нност[ьи]'),
    'HEIGHT_BUILD': (r'высот[аы]',),
    'QUANTITY': (r'количеств[оа]',),
}

UNIT_RE = {
    'SHIFT_DURATION': r'(?:ч(?:ас(?:а|ов)?)?)',
    'CAPACITY': r'(?:тыс\.?\s*(?:т|тонн)\s*/\s*год|т\s*/\s*(?:ч|час|год)|м[³3]\s*/\s*ч)',
    'AREA_BUILD': r'(?:м[²2])', 'AREA_TOTAL': r'(?:м[²2])',
    'BODY_VOLUME': r'(?:м[³3])', 'BUCKET_VOLUME': r'(?:м[³3])', 'VOLUME': r'(?:м[³3])',
    'POWER_INSTALLED': r'(?:квт|мвт|ква)', 'FLOW_RATE': r'(?:м[³3]\s*/\s*ч|л\s*/\s*с)',
    'LENGTH': r'(?:мм|см|м|км)', 'HEIGHT_BUILD': r'(?:мм|см|м)', 'QUANTITY': r'(?:шт\.?)',
}

SECTION_ALIASES = {
    'ПЗ': ('_пз.', '№1_пз', 'пояснительн'),
    'ПЗУ': ('пзу', 'схема планировочной'),
    'АР': ('_ар', 'архитектурн'),
    'КР': ('_кр', 'конструктивн'),
    'ТХ': ('_тх', 'технологическ'),
    'ИОС1': ('иос1', 'электроснабжен'),
    'ИОС2': ('иос2', 'водоснабжен', 'водоотведен'),
    'ИОС': ('иос', 'инженерн'),
}



def normalize_engineering_unit(unit: Any) -> str:
    raw=normalize_text(unit).lower().replace('ё','е')
    compact=re.sub(r'\s+','',raw).replace('³','3').replace('²','2')
    compact=compact.replace('тонн','т').replace('тонны','т').replace('тонну','т')
    compact=compact.replace('часов','ч').replace('часа','ч').replace('час','ч')
    compact=compact.replace('вгод','/год').replace('загод','/год').replace('вчас','/ч')
    compact=compact.replace('тыс.','тыс').replace('тыс','тыс.')
    compact=compact.replace('м3','м3').replace('м2','м2')
    aliases={
        'м2':'м2','м3':'м3','шт.':'шт','шт':'шт',
        'т/ч':'т/ч','т/год':'т/год','тыс.т/год':'тыс.т/год',
        'тыс.тгод':'тыс.т/год','тыс.т/год.':'тыс.т/год',
        'м3/ч':'м3/ч','л/с':'л/с','квт':'квт','мвт':'мвт','ква':'ква',
        'ч':'ч','м':'м','км':'км','мм':'мм','см':'см',
    }
    return aliases.get(compact,compact)

def units_compatible(required_unit: Any, candidate_unit: Any, code: str='') -> bool:
    ru=normalize_engineering_unit(required_unit); cu=normalize_engineering_unit(candidate_unit)
    if not ru or not cu: return False
    if ru==cu: return True
    # Safe scale conversions only. Flow/capacity time-basis conversions are NOT inferred.
    families=[{'м','км','мм','см'},{'квт','мвт'}]
    return any(ru in fam and cu in fam for fam in families)

def _file_name(f: Any) -> str:
    return str(getattr(f, 'name', '') or '')


def _section_ok(filename: str, expected: list[str]) -> bool:
    if not expected:
        return True
    low = normalize_text(filename)
    for section in expected:
        s = str(section or '').upper()
        aliases = SECTION_ALIASES.get(s, (normalize_text(section),))
        if any(normalize_text(a) in low for a in aliases):
            return True
    return False


def _object_tokens(name: str) -> set[str]:
    stop={'здание','сооружение','площадка','комплекс','оборудование','станция','система','установка'}
    return {w for w in re.findall(r'[а-яa-z0-9-]{3,}', normalize_text(name), re.I) if w not in stop}


def _owner_match(text: str, object_name: str, scope: str) -> tuple[bool, float]:
    if scope in {SCOPE_PROJECT, SCOPE_SITE, SCOPE_SYSTEM, SCOPE_DOCUMENT}:
        return True, 1.0
    if not object_name:
        return False, 0.0
    low=normalize_text(text); obj=normalize_text(object_name)
    if obj and obj in low:
        return True, 1.0
    toks=_object_tokens(obj); present=sum(1 for t in toks if t in low)
    ratio=present/max(1,len(toks))
    return ratio >= .6, ratio


def _extract_metric_values(text: str, code: str) -> list[tuple[float,str,str]]:
    code=canonical_parameter_code(code)
    patterns=METRIC_PATTERNS.get(code) or ()
    unit=UNIT_RE.get(code, r'(?:м[²2³3]|м|км|шт\.?|ч(?:ас(?:а|ов)?)?|т\s*/\s*ч|т\s*/\s*год)')
    results=[]
    # Windowed metric-first extraction. A value must be within 100 chars of the metric label.
    for mp in patterns:
        rx=re.compile(rf'(?P<label>{mp})[^\n;:]{{0,100}}?(?P<value>\d[\d\s\u00a0]*(?:[,.]\d+)?)\s*(?P<unit>{unit})', re.I)
        for m in rx.finditer(text):
            raw=m.group('value').replace('\u00a0','').replace(' ','').replace(',','.')
            try: value=float(raw)
            except Exception: continue
            results.append((value,m.group('unit'),m.group(0)))
        # value-first formulations such as "12 часов" after a row heading are allowed only
        # when the metric label occurs in the same short line/window.
    return results


def _page_context(text: str, hit: str, radius: int=320) -> str:
    pos=normalize_text(text).find(normalize_text(hit)) if hit else -1
    if pos < 0:
        return re.sub(r'\s+',' ',text)[:700]
    return re.sub(r'\s+',' ',text[max(0,pos-radius):pos+len(hit)+radius])[:900]


def build_page_corpus(files: list[Any], reader: Callable[[bytes,str], list[tuple[int,str]]]) -> list[dict[str,Any]]:
    corpus=[]
    for f in files or []:
        name=_file_name(f)
        try:
            data=f.getvalue() if hasattr(f,'getvalue') else f.read()
            pages=reader(data,name)
        except Exception:
            continue
        for page,text in pages or []:
            if text and len(str(text).strip())>20:
                corpus.append({'document':name,'page':page,'text':str(text)})
    return corpus


def directed_candidates(requirement: dict[str,Any], corpus: list[dict[str,Any]], limit: int=8) -> list[dict[str,Any]]:
    contract=requirement.get('evidence_contract_v2') or {}
    code=canonical_parameter_code(requirement.get('parameter_code'))
    if not code or code not in METRIC_PATTERNS:
        return []
    scope=str(contract.get('scope') or requirement.get('requirement_scope') or '')
    obj=str(requirement.get('object_name') or '')
    expected=list(contract.get('expected_sections') or [])
    required=requirement.get('required_value')
    ranked=[]
    for page in corpus:
        if not _section_ok(page['document'], expected):
            continue
        text=page['text']
        owner_ok, owner_score=_owner_match(text,obj,scope)
        if scope in {SCOPE_OBJECT,SCOPE_EQUIPMENT} and not owner_ok:
            continue
        values=_extract_metric_values(text,code)
        for value,unit,hit in values:
            score=40
            score += int(owner_score*25)
            if expected: score += 10
            req_unit=requirement.get('unit') or ''
            unit_ok=units_compatible(req_unit,unit,code) if req_unit else False
            if req_unit:
                if unit_ok: score += 15
                else: score -= 30
            if required is not None and unit_ok:
                try:
                    rv=float(required)
                    if math.isclose(value,rv,rel_tol=.002,abs_tol=.05): score += 20
                except Exception: pass
            # Project-global metrics need an explicit metric label; object-specific metrics
            # additionally need the owner match above.
            evidence_state='verified_candidate' if score>=70 else 'candidate'
            ranked.append((score,{
                'evidence_kind':'DIRECTED_VALUE', 'evidence_state':evidence_state,
                'document':page['document'],'page':page['page'],'object':obj,
                'parameter_code':code,'value':value,'unit':unit,
                'context':_page_context(text,hit),'match_method':'REQUIREMENT_DIRECTED_TEXT',
                'owner_match':owner_ok,'owner_score':round(owner_score,2),'unit_compatible':unit_ok,'score':score,
            }))
    ranked.sort(key=lambda x:(x[0], -int(x[1]['page'] or 0)), reverse=True)
    # Deduplicate same value on same page.
    out=[];seen=set()
    for _,item in ranked:
        key=(item['document'],item['page'],round(item['value'],6),item['parameter_code'])
        if key in seen: continue
        seen.add(key);out.append(item)
        if len(out)>=limit: break
    return out


def attach_directed_evidence(requirements: list[dict[str,Any]], corpus: list[dict[str,Any]]) -> dict[str,int]:
    stats={'requirements':len(requirements),'with_candidates':0,'verified_candidates':0}
    for req in requirements:
        cands=directed_candidates(req,corpus)
        req['directed_evidence_candidates']=cands
        if cands: stats['with_candidates']+=1
        stats['verified_candidates']+=sum(1 for c in cands if c.get('evidence_state')=='verified_candidate')
    return stats


def directed_evidence_facts(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    """Project exact directed hits into the Deep Evidence layer only.

    These records do not enter the object registry or cross-section model. They
    preserve a deterministic requirement-to-source trace so that the adversarial
    gate can verify an already established positive result.
    """
    facts=[]; seen=set()
    for row in rows or []:
        if str(row.get('status') or '') != 'Соответствует заданию':
            continue
        code=canonical_parameter_code(row.get('parameter_code'))
        required=row.get('required_value')
        if not code or required is None:
            continue
        try: required_value=float(required)
        except (TypeError,ValueError): continue
        scope=str((row.get('evidence_contract_v2') or {}).get('scope') or row.get('requirement_scope') or '')
        owner=str(row.get('object_name') or ('Проект' if scope==SCOPE_PROJECT else '')).strip()
        for candidate in row.get('directed_evidence_candidates') or []:
            if str(candidate.get('evidence_state') or '')!='verified_candidate':
                continue
            if canonical_parameter_code(candidate.get('parameter_code'))!=code:
                continue
            if row.get('unit') and not units_compatible(row.get('unit'),candidate.get('unit'),code):
                continue
            try: value=float(candidate.get('value'))
            except (TypeError,ValueError): continue
            if not math.isclose(value,required_value,rel_tol=.002,abs_tol=.05):
                continue
            key=(str(row.get('requirement_id') or ''),str(candidate.get('document') or ''),candidate.get('page'),round(value,6),code)
            if key in seen: continue
            seen.add(key)
            facts.append({
                'requirement_id':row.get('requirement_id'),
                'document':candidate.get('document'),'page':candidate.get('page'),
                'object_hint':owner,'semantic_anchor_name':owner,
                'parameter_code':code,'parameter_name':code,
                'value':value,'unit':candidate.get('unit'),'context':candidate.get('context'),
                'match_method':'REQUIREMENT_DIRECTED_TEXT','directed_evidence':True,
                'evidence_quality_decision':'VERIFIED','fact_admission_decision':'ADMIT',
                'binding_status':'EXACT_OBJECT' if owner else '',
            })
    return facts
