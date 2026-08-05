from __future__ import annotations

import re
from typing import Any, Iterable

from .normalization import normalize_text

_FILE_RE = re.compile(r"(?:\.pdf|\.xml|\.sig|\.zip|\.docx?|\.xlsx?)$", re.I)


def object_key(row: dict[str, Any]) -> str:
    position = str(row.get('Позиция по ГП') or row.get('Позиция') or row.get('position') or '').strip()
    name = normalize_text(row.get('Наименование объекта') or row.get('Объект') or row.get('name') or '')
    return f"{position}|{name}"


def display_name(row: dict[str, Any]) -> str:
    return str(row.get('Наименование объекта') or row.get('Объект') or row.get('name') or '').strip()


def build_assembly_rows(trusted: Iterable[dict[str, Any]], candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
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
            rows.append({
                'Ключ': key,
                'Включить': bool(default_include and not obvious_file),
                'Позиция по ГП': row.get('Позиция по ГП') or row.get('Позиция') or '',
                'Наименование объекта': name,
                'Статус проектирования': row.get('Статус проектирования') or 'Не определён',
                'Доверие': row.get('Доверие к объекту', ''),
                'Источники': row.get('Источники') or row.get('Количество источников') or '',
                'Автоматическое решение': 'Предложено включить' if default_include and not obvious_file else 'Не включён автоматически',
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
