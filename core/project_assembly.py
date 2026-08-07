from __future__ import annotations

import re
from typing import Any, Iterable

from .normalization import normalize_text
from .evidence_registry import evidence_for_row, compact_source, is_forbidden_evidence
from .position_rules import normalize_genplan_position

_FILE_RE = re.compile(r"(?:\.pdf|\.xml|\.sig|\.zip|\.docx?|\.xlsx?)$", re.I)


def object_key(row: dict[str, Any]) -> str:
    position = normalize_genplan_position(row.get('Позиция по ГП') or row.get('Позиция') or row.get('position'), allow_integer=True)
    name = normalize_text(row.get('Наименование объекта') or row.get('Объект') or row.get('name') or '')
    return f"{position}|{name}"


def display_name(row: dict[str, Any]) -> str:
    return str(row.get('Наименование объекта') or row.get('Объект') or row.get('name') or '').strip()


def build_assembly_rows(trusted: Iterable[dict[str, Any]], candidates: Iterable[dict[str, Any]], evidence_index: dict[str, list[dict[str, Any]]] | None = None, intelligence_decisions: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source, default_include in ((trusted, True), (candidates, False)):
        for original in source:
            row = dict(original)
            key = object_key(row)
            if not key or key in seen:
                continue
            seen.add(key)
            name = display_name(row)
            obvious_file = bool(_FILE_RE.search(name))
            evidence = evidence_for_row(row, evidence_index or {})
            forbidden_evidence = [e for e in evidence if e.get('forbidden')]
            valid_evidence = [e for e in evidence if not e.get('forbidden')]
            auto_blocked = obvious_file or (bool(evidence) and not valid_evidence)
            source_preview = '; '.join(compact_source(e) for e in valid_evidence[:3])
            intel=(intelligence_decisions or {}).get(key,{})
            intel_decision = intel.get('decision')
            # Strictly rejected service/date/TOC candidates are not shown to the
            # engineer at all. The audit remains available in developer mode.
            if intel_decision == 'blocked' and int(intel.get('confidence') or 0) == 0:
                continue
            if intel_decision:
                if intel_decision in {'blocked','context'}:
                    auto_blocked=True
                # Консервативный режим: при наличии решения Object Intelligence
                # автоматически включаются только trusted.
                default_include = bool(default_include and intel_decision == 'trusted')
                if intel_decision != 'trusted':
                    default_include=False
            rows.append({
                'Ключ': key,
                'Включить': bool(default_include and not auto_blocked),
                'Позиция по ГП': normalize_genplan_position(row.get('Позиция по ГП') or row.get('Позиция'), allow_integer=True),
                'Наименование объекта': name,
                'Статус проектирования': row.get('Статус проектирования') or 'Не определён',
                'Доверие': row.get('Доверие к объекту', ''),
                'Источники': source_preview or row.get('Источники') or row.get('Количество источников') or '',
                'Количество доказательств': len(valid_evidence),
                'Основание включения': source_preview or ('Надёжное доказательство не найдено' if not valid_evidence else ''),
                'Блокировка': '; '.join(e.get('forbidden_reason','') for e in forbidden_evidence[:2]) if auto_blocked else '',
                'Решение пользователя': 'Не задано',
                'Комментарий пользователя': '',
                '_evidence': evidence,
                'Автоматическое решение': 'Предложено включить' if default_include and not auto_blocked else 'Не включён автоматически',
                'Решение Object Intelligence': intel.get('decision',''),
                'Доверие Object Intelligence': intel.get('confidence',''),
                'Обоснование Object Intelligence': intel.get('reason',''),
                'Независимых документов': intel.get('independent_documents',0),
                'Официальных источников': intel.get('official_sources',0),
                'Канонический источник': compact_source(intel.get('canonical_source')) if intel.get('canonical_source') else '',
            })
    return rows


def selected_keys(rows: Iterable[dict[str, Any]]) -> set[str]:
    return {str(row.get('Ключ') or '') for row in rows if bool(row.get('Включить'))}


def filter_registry_by_keys(registry: Iterable[dict[str, Any]], allowed: set[str]) -> list[dict[str, Any]]:
    return [dict(row) for row in registry if object_key(row) in allowed]


def filter_passports_by_keys(passports: Iterable[dict[str, Any]], allowed: set[str]) -> list[dict[str, Any]]:
    result=[]
    for p in passports:
        row={'Позиция по ГП':p.get('position'),'Наименование объекта':p.get('name')}
        if object_key(row) in allowed:
            result.append(p)
    return result


def filter_comparisons_by_keys(comparisons: Iterable[dict[str, Any]], assembly_rows: Iterable[dict[str, Any]], allowed: set[str]) -> list[dict[str, Any]]:
    names={normalize_text(r.get('Наименование объекта') or '') for r in assembly_rows if r.get('Ключ') in allowed}
    positions={str(r.get('Позиция по ГП') or '').strip() for r in assembly_rows if r.get('Ключ') in allowed and str(r.get('Позиция по ГП') or '').strip()}
    out=[]
    for item in comparisons:
        name=normalize_text(item.get('object') or item.get('Объект') or '')
        position=str(item.get('genplan_position') or item.get('Позиция по ГП') or '').strip()
        if (position and position in positions) or (name and name in names):
            out.append(dict(item))
    return out
